#!/usr/bin/env python3
"""Build conservative GOV commercial features from official public history.

This module turns already-captured historical notices, awards, and competition
signals into an internal case brief.  It explicitly keeps bidder counts and
L1 prices UNKNOWN unless a source-provenanced official record contains the
field.  It does not browse, estimate prices, contact anyone, or make a bid.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any
from urllib.parse import urlparse

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - direct CLI dependency error
    yaml = None  # type: ignore[assignment]

try:
    from scripts.event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import append_event  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
HISTORICAL_CONFIG = PROJECT_ROOT / "config" / "historical_capture.yaml"
DEFAULT_NOTICES = DATA_DIR / "historical_tender_notices.csv"
DEFAULT_AWARDS = DATA_DIR / "historical_awards.csv"
DEFAULT_SIGNALS = DATA_DIR / "historical_competition_signals.csv"
DEFAULT_CASES = DATA_DIR / "master_cases.csv"
DEFAULT_EVENTS = DATA_DIR / "events.jsonl"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"

STOPWORDS = {"and", "for", "the", "of", "supply", "supplies", "service", "services", "item", "items"}


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalized(value: Any) -> str:
    return clean_text(value).casefold()


def today_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_domains(path: Path = HISTORICAL_CONFIG) -> set[str]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load the historical source allowlist")
    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {normalized(value).rstrip(".") for value in config.get("official_domains", []) if normalized(value)}


def official_public_url(source_url: str, official_domains: set[str]) -> bool:
    parsed = urlparse(clean_text(source_url))
    hostname = (parsed.hostname or "").casefold().rstrip(".")
    return (
        parsed.scheme == "https"
        and bool(hostname)
        and not parsed.username
        and not parsed.password
        and any(hostname == domain or hostname.endswith(f".{domain}") for domain in official_domains)
    )


def has_official_provenance(row: dict[str, Any], official_domains: set[str]) -> bool:
    digest = clean_text(row.get("evidence_sha256"))
    return (
        official_public_url(clean_text(row.get("source_url")), official_domains)
        and bool(clean_text(row.get("evidence_path")))
        and bool(re.fullmatch(r"[0-9a-fA-F]{64}", digest))
    )


def as_positive_float(value: Any) -> float | None:
    text = clean_text(value).replace(",", "")
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if number > 0 else None


def as_positive_int(value: Any) -> int | None:
    number = as_positive_float(value)
    if number is None or not number.is_integer():
        return None
    return int(number)


def number_text(value: float | None) -> str:
    if value is None:
        return ""
    return str(int(value)) if value.is_integer() else f"{value:.2f}".rstrip("0").rstrip(".")


def category_match(case: dict[str, Any], row: dict[str, Any]) -> bool:
    case_code = normalized(case.get("category_code"))
    row_code = normalized(row.get("category_code"))
    if case_code and row_code and case_code == row_code:
        return True
    case_text = normalized(case.get("product_or_service") or case.get("opportunity_title"))
    row_text = normalized(row.get("category_name") or row.get("product_or_service"))
    if not case_text or not row_text:
        return False
    if case_text in row_text or row_text in case_text:
        return True
    case_tokens = {token for token in re.findall(r"[a-z0-9]+", case_text) if token not in STOPWORDS}
    row_tokens = {token for token in re.findall(r"[a-z0-9]+", row_text) if token not in STOPWORDS}
    return len(case_tokens & row_tokens) >= 2


def buyer_match(case: dict[str, Any], row: dict[str, Any]) -> bool:
    return bool(normalized(case.get("buyer_name"))) and normalized(case.get("buyer_name")) == normalized(row.get("buyer_name"))


def source_citations(rows: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for row in rows:
        for key in ("evidence_path", "source_url"):
            value = clean_text(row.get(key))
            if value and value not in values:
                values.append(value)
    return values


def _record_id(row: dict[str, Any], *, kind: str) -> str:
    return clean_text(row.get("notice_id")) or clean_text(row.get("award_id")) or f"{kind}:{clean_text(row.get('source_record_id'))}"


def _derived_competition_signals(
    notices: list[dict[str, Any]], awards: list[dict[str, Any]], external_signals: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for notice in notices:
        text = normalized(notice.get("competition_signal"))
        mapping = {
            "retender": "RETENDER",
            "re-tender": "RETENDER",
            "date extension": "DATE_EXTENSION",
            "corrigendum": "CORRIGENDUM",
            "single bid": "SINGLE_BID",
            "shortfall": "LOW_BIDDER_COUNT",
        }
        for phrase, signal_type in mapping.items():
            if phrase in text:
                signals.append({"signal_type": signal_type, "source": notice, "derived_from": "notice"})
                break
    for award in awards:
        bidder_count = as_positive_int(award.get("bidder_count"))
        if bidder_count == 1:
            signals.append({"signal_type": "SINGLE_BID", "source": award, "derived_from": "award"})
        elif bidder_count is not None and bidder_count <= 3:
            signals.append({"signal_type": "LOW_BIDDER_COUNT", "source": award, "derived_from": "award"})
        text = normalized(award.get("competition_signal"))
        if "retender" in text:
            signals.append({"signal_type": "RETENDER", "source": award, "derived_from": "award"})
    for signal in external_signals:
        signals.append(
            {
                "signal_type": clean_text(signal.get("signal_type")).upper() or "UNSPECIFIED",
                "source": signal,
                "derived_from": "recorded_signal",
            }
        )
    return signals


def build_case_intelligence(
    case: dict[str, Any],
    notices: list[dict[str, Any]],
    awards: list[dict[str, Any]],
    competition_signals: list[dict[str, Any]],
    *,
    official_domains: set[str],
) -> dict[str, Any]:
    """Calculate a strictly observed, source-cited GOV history feature set."""
    if clean_text(case.get("workflow_type")).upper() != "GOV":
        raise ValueError("Historical GOV intelligence requires workflow_type=GOV")
    if not clean_text(case.get("case_id")):
        raise ValueError("case_id is required")

    valid_notices = [row for row in notices if has_official_provenance(row, official_domains) and buyer_match(case, row)]
    valid_awards = [row for row in awards if has_official_provenance(row, official_domains) and buyer_match(case, row)]
    category_notices = [row for row in valid_notices if category_match(case, row)]
    category_awards = [row for row in valid_awards if category_match(case, row)]
    valid_signals = [
        row
        for row in competition_signals
        if has_official_provenance(row, official_domains) and buyer_match(case, row) and category_match(case, row)
    ]

    observed_tenders = {_record_id(row, kind="notice") for row in valid_notices}
    observed_tenders.update(
        clean_text(row.get("notice_id")) or _record_id(row, kind="award") for row in valid_awards
    )
    winner_counts = Counter(clean_text(row.get("winner_name")) for row in category_awards if clean_text(row.get("winner_name")))
    winners = [winner for winner, _ in winner_counts.most_common(5)]
    bidder_counts = [count for row in category_awards if (count := as_positive_int(row.get("bidder_count"))) is not None]
    l1_prices = [price for row in category_awards if (price := as_positive_float(row.get("l1_price_inr"))) is not None]
    signals = _derived_competition_signals(category_notices, category_awards, valid_signals)
    signal_types = sorted({str(item["signal_type"]) for item in signals})
    all_evidence_rows = category_notices + category_awards + valid_signals

    past_tender_count = len(observed_tenders)
    similar_category_awards = len(category_awards)
    repeat_score = min(100, past_tender_count * 12 + len(category_notices) * 12 + similar_category_awards * 20)
    repeat_score_value: int | str = repeat_score if all_evidence_rows else ""
    bidder_average = (sum(bidder_counts) / len(bidder_counts)) if bidder_counts else None
    l1_median = float(median(l1_prices)) if l1_prices else None
    incumbent_repeat = bool(winner_counts and winner_counts.most_common(1)[0][1] >= 2)
    if not l1_prices:
        l1_risk = "UNKNOWN"
    elif incumbent_repeat:
        l1_risk = "ELEVATED_INCUMBENT_AND_OBSERVED_L1_HISTORY"
    else:
        l1_risk = "HISTORICAL_OBSERVED_REFERENCE_ONLY"

    features = {
        "evidence_status": "OFFICIAL_PUBLIC_EVIDENCE_OBSERVED" if all_evidence_rows else "NO_OFFICIAL_PUBLIC_EVIDENCE",
        "buyer_repeat_score": repeat_score_value,
        "past_tender_count": past_tender_count if all_evidence_rows else "",
        "same_category_notice_count": len(category_notices),
        "similar_category_awards": similar_category_awards,
        "known_past_winners": winners,
        "incumbent_repeat_winner_observed": incumbent_repeat,
        "competition": {
            "status": "OBSERVED" if bidder_counts or signal_types else "UNKNOWN",
            "observed_bidder_counts": bidder_counts,
            "observed_bidder_count_average": bidder_average,
            "recorded_signal_types": signal_types,
            "missing_when_absent": "UNKNOWN; no bidder count or competition estimate is generated.",
        },
        "l1": {
            "status": "OBSERVED" if l1_prices else "UNKNOWN",
            "observed_l1_prices_inr": l1_prices,
            "historical_observed_l1_median_inr": l1_median,
            "l1_risk": l1_risk,
            "missing_when_absent": "UNKNOWN; award value is never treated as an L1 price.",
        },
        "source_record_counts": {
            "official_buyer_notices": len(valid_notices),
            "official_category_notices": len(category_notices),
            "official_buyer_awards": len(valid_awards),
            "official_category_awards": len(category_awards),
            "official_category_signals": len(valid_signals),
        },
    }
    updates = {
        "buyer_repeat_score": str(repeat_score_value) if repeat_score_value != "" else "",
        "past_tender_count": str(past_tender_count) if all_evidence_rows else "",
        "similar_category_awards": str(similar_category_awards) if all_evidence_rows else "",
        "known_past_winners": "; ".join(winners),
        "typical_l1_price": number_text(l1_median),
    }
    stable_input = {
        "case_id": case["case_id"],
        "features": features,
        "evidence_hashes": sorted(clean_text(row.get("evidence_sha256")) for row in all_evidence_rows),
    }
    fingerprint = hashlib.sha256(json.dumps(stable_input, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "schema_version": "gov_historical_intelligence.v1",
        "case_id": clean_text(case["case_id"]),
        "workflow_type": "GOV",
        "generated_at": now_iso(),
        "input_fingerprint": fingerprint,
        "features": features,
        "case_updates": updates,
        "citations": source_citations(all_evidence_rows),
        "external_actions_executed": False,
    }


def render_markdown(report: dict[str, Any]) -> str:
    features = report["features"]
    competition = features["competition"]
    l1 = features["l1"]
    lines = [
        f"# GOV Historical Commercial Intelligence — {report['case_id']}",
        "",
        f"- Evidence status: `{features['evidence_status']}`",
        f"- Generated at: `{report['generated_at']}`",
        "- External actions executed: `false`",
        "",
        "## Observed buyer and award history",
        "",
        f"- Buyer repeat score: `{features['buyer_repeat_score'] if features['buyer_repeat_score'] != '' else 'UNKNOWN'}`",
        f"- Observed buyer tender count: `{features['past_tender_count'] if features['past_tender_count'] != '' else 'UNKNOWN'}`",
        f"- Same-category notices: `{features['same_category_notice_count']}`",
        f"- Same-category awards: `{features['similar_category_awards']}`",
        f"- Known past winners: {', '.join(features['known_past_winners']) or 'UNKNOWN'}",
        "",
        "## Competition and L1 evidence",
        "",
        f"- Bidder-count status: `{competition['status']}`",
        f"- Observed bidder counts: `{competition['observed_bidder_counts'] or 'UNKNOWN'}`",
        f"- Observed bidder-count average: `{number_text(competition['observed_bidder_count_average']) or 'UNKNOWN'}`",
        f"- Recorded competition signals: `{', '.join(competition['recorded_signal_types']) or 'UNKNOWN'}`",
        f"- L1 evidence status: `{l1['status']}`",
        f"- Observed L1 prices (INR): `{l1['observed_l1_prices_inr'] or 'UNKNOWN'}`",
        f"- Historical observed L1 median (INR): `{number_text(l1['historical_observed_l1_median_inr']) or 'UNKNOWN'}`",
        f"- L1 risk interpretation: `{l1['l1_risk']}`",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- `{citation}`" for citation in report["citations"] or ["No official public historical evidence matched this case."])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is an internal historical signal, not a current bidder-count estimate, L1 prediction, price commitment, eligibility determination, or submission authority. Missing bidder/L1 data remains UNKNOWN.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"historical_intelligence_{report['case_id']}.json"
    markdown_path = output_dir / f"historical_intelligence_{report['case_id']}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json_path": json_path, "markdown_path": markdown_path}


def _load_case_projection(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_case_projection(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in headers} for row in rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def apply_case_intelligence(
    report: dict[str, Any],
    *,
    report_path: Path,
    master_cases_path: Path = DEFAULT_CASES,
    events_path: Path = DEFAULT_EVENTS,
    actor: str = "gov_historical_intelligence",
) -> dict[str, Any]:
    """Append the cited event before refreshing the master-case projection."""
    headers, rows = _load_case_projection(master_cases_path)
    case_id = clean_text(report.get("case_id"))
    if not case_id or "case_id" not in headers:
        raise ValueError("A case_id column and a non-empty report case_id are required")
    if not all(field in headers for field in report["case_updates"]):
        missing = sorted(field for field in report["case_updates"] if field not in headers)
        raise ValueError("Master Case Register lacks historical intelligence fields: " + ", ".join(missing))
    if sum(row.get("case_id") == case_id for row in rows) != 1:
        raise ValueError(f"Expected exactly one Master Case row for {case_id}")
    updates = {key: str(value) for key, value in report["case_updates"].items()}
    updates["updated_at"] = today_iso()
    event = append_event(
        "case.historical_intelligence_recorded",
        actor,
        case_id=case_id,
        object_type="case",
        object_id=case_id,
        source="official_public_historical_intelligence",
        payload={
            "report_path": str(report_path),
            "schema_version": report["schema_version"],
            "input_fingerprint": report["input_fingerprint"],
            "updates": updates,
        },
        citations=[str(report_path), *report.get("citations", [])],
        idempotency_key=f"gov-historical-intelligence:{case_id}:{report['input_fingerprint']}",
        events_file=events_path,
    )
    for row in rows:
        if row.get("case_id") == case_id:
            row.update(updates)
    _write_case_projection(master_cases_path, headers, rows)
    return {"event_id": str(event["event_id"]), "projection_updated": True, "external_actions_executed": False}


def _resolve(path: str) -> Path:
    value = Path(path).expanduser()
    return value if value.is_absolute() else PROJECT_ROOT / value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--notices", default=str(DEFAULT_NOTICES))
    parser.add_argument("--awards", default=str(DEFAULT_AWARDS))
    parser.add_argument("--competition-signals", default=str(DEFAULT_SIGNALS))
    parser.add_argument("--master-cases", default=str(DEFAULT_CASES))
    parser.add_argument("--events", default=str(DEFAULT_EVENTS))
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--write", action="store_true", help="Write internal report files only")
    parser.add_argument("--apply", action="store_true", help="Write report, append event, and update local projection")
    parser.add_argument("--actor", default="gov_historical_intelligence")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cases_path = _resolve(args.master_cases)
    case = next((row for row in load_csv(cases_path) if row.get("case_id") == args.case_id), None)
    if case is None:
        raise SystemExit(f"No Master Case Register row found for {args.case_id}")
    report = build_case_intelligence(
        case,
        load_csv(_resolve(args.notices)),
        load_csv(_resolve(args.awards)),
        load_csv(_resolve(args.competition_signals)),
        official_domains=load_domains(),
    )
    payload: dict[str, Any] = {
        "mode": "apply" if args.apply else "write" if args.write else "dry_run",
        "case_id": report["case_id"],
        "evidence_status": report["features"]["evidence_status"],
        "l1_status": report["features"]["l1"]["status"],
        "bidder_count_status": report["features"]["competition"]["status"],
        "external_actions_executed": False,
    }
    if args.write or args.apply:
        output_dir = _resolve(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_ROOT / report["case_id"]
        paths = write_report(report, output_dir)
        payload.update({key: str(value) for key, value in paths.items()})
        if args.apply:
            payload.update(
                apply_case_intelligence(
                    report,
                    report_path=paths["json_path"],
                    master_cases_path=cases_path,
                    events_path=_resolve(args.events),
                    actor=args.actor,
                )
            )
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"GOV historical intelligence: {payload}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
