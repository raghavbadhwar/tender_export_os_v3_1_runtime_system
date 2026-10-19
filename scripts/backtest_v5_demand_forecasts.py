#!/usr/bin/env python3
"""Backtest V5 forecast candidates against current local registers.

Default mode is dry-run. Use --write to update data/forecast_backtests.csv.
The script never mutates source registers and performs no external action.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
FORECAST_PATH = DATA_DIR / "forecast_candidates.csv"
OUTPUT_PATH = DATA_DIR / "forecast_backtests.csv"
OUTCOMES_PATH = DATA_DIR / "case_outcomes.csv"
EVENTS_PATH = DATA_DIR / "events.jsonl"

COLUMNS = [
    "backtest_id",
    "forecast_id",
    "forecast_date",
    "review_date",
    "case_or_research_id",
    "forecast_type",
    "predicted_action",
    "observed_outcome",
    "outcome_label",
    "predicted_probability",
    "binary_outcome",
    "is_mature",
    "brier_component",
    "model_version",
    "eligible_for_backtest_at",
    "score_delta",
    "false_positive_reason",
    "false_negative_reason",
    "learning_note",
    "config_change_recommended",
    "created_at",
]

ADVANCED_STATUSES = {"DEEP_READ", "SUPPLIER_SEARCH", "PRICING_READY", "ARTIFACT_PRODUCTION", "APPROVAL_REQUIRED", "APPROVED"}
WEAK_EVIDENCE = {"", "MISSING", "RAW_LEAD", "PARTIAL", "MARKETPLACE_MASKED", "PUBLIC_LISTING_ONLY", "LOW_EVIDENCE", "RESEARCH_ONLY_NOT_RFQ"}
POSITIVE_OUTCOME_TYPES = {
    "SUBMITTED",
    "TECHNICAL_QUALIFIED",
    "L1_DECLARED",
    "WON",
    "WORK_ORDER_RECEIVED",
    "OUTREACH_SENT",
    "REPLY_RECEIVED",
    "RFQ_RECEIVED",
    "QUOTE_SENT",
    "ORDER_RECEIVED",
    "SAMPLE_SENT",
    "PRODUCTION_STARTED",
    "SHIPPED",
    "DELIVERED",
    "INVOICED",
    "PAYMENT_DUE",
    "PAYMENT_RECEIVED",
    "REPEAT_INQUIRY",
}
NEGATIVE_OUTCOME_TYPES = {
    "TECHNICAL_DISQUALIFIED",
    "LOST",
    "OPT_OUT",
    "BOUNCE",
    "PAYMENT_DELAYED",
    "CLAIM_OR_RETURN",
}
JUSTIFIED_KILL_OUTCOME_TYPES = {"FAST_KILL_JUSTIFIED", "REJECTED"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def slugify(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "unknown"


def parse_date(value: Any) -> dt.date | None:
    text = str(value or "").strip()
    if not text:
        return None
    if re.fullmatch(r"\d{8}", text):
        text = f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        return None


def parse_datetime(value: Any) -> dt.datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def safe_float(value: Any) -> float:
    try:
        return float(str(value or "").replace(",", ""))
    except ValueError:
        return 0.0


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in COLUMNS})


def write_backtest_rows(path: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Upsert review receipts while preserving all prior review dates."""
    merged = {row.get("backtest_id", ""): row for row in load_csv(path) if row.get("backtest_id")}
    merged.update({row["backtest_id"]: row for row in rows if row.get("backtest_id")})
    history = sorted(merged.values(), key=lambda row: (row.get("review_date", ""), row.get("backtest_id", "")))
    write_csv(path, history)
    return rows


def horizon_days(value: str) -> int:
    text = str(value or "").lower()
    if "0-7" in text:
        return 7
    if "7-30" in text:
        return 30
    if "30-60" in text:
        return 60
    if "60-90" in text or "30-90" in text:
        return 90
    return 30


def stronger_evidence(row: dict[str, str], forecast_evidence: str) -> bool:
    current = str(row.get("evidence_level") or row.get("rfq_stage") or row.get("evidence_status") or "").upper()
    if current in {"DOCUMENTS_DOWNLOADED", "DEEP_READ_COMPLETE", "RFQ_VERIFIED", "READY_FOR_SUPPLIER_PROOF"}:
        return current != forecast_evidence.upper()
    return False


def _verified_time_separated_outcome(
    forecast: dict[str, str],
    outcomes: list[dict[str, str]],
    events: list[dict[str, Any]],
    review_date: dt.date,
) -> dict[str, str] | None:
    case_id = str(forecast.get("case_or_research_id") or "")
    forecast_date = parse_date(forecast.get("forecast_date")) or review_date
    forecast_time = dt.datetime.combine(forecast_date, dt.time.min, tzinfo=dt.timezone.utc)
    review_end = dt.datetime.combine(review_date, dt.time.max, tzinfo=dt.timezone.utc)
    event_times: dict[str, dt.datetime] = {}
    for event in events:
        if event.get("event_type") != "case.outcome_recorded":
            continue
        event_time = parse_datetime(event.get("event_time"))
        if event_time:
            event_times[str(event.get("object_id") or "")] = event_time

    eligible: list[tuple[dt.datetime, dict[str, str]]] = []
    for outcome in outcomes:
        if str(outcome.get("case_id") or "") != case_id:
            continue
        if str(outcome.get("verification_status") or "").upper() != "VERIFIED":
            continue
        if not str(outcome.get("evidence_path") or "").strip() or len(str(outcome.get("evidence_sha256") or "")) != 64:
            continue
        occurred = parse_datetime(outcome.get("occurred_at"))
        if occurred is None or occurred <= forecast_time or occurred > review_end:
            continue
        outcome_id = str(outcome.get("outcome_id") or "")
        event_time = event_times.get(outcome_id)
        if events and (event_time is None or event_time <= forecast_time or event_time > review_end):
            continue
        recorded = event_time or parse_datetime(outcome.get("recorded_at"))
        if recorded is None or recorded <= forecast_time or recorded > review_end:
            continue
        eligible.append((occurred, outcome))
    return min(eligible, key=lambda item: item[0])[1] if eligible else None


def label_forecast(
    forecast: dict[str, str],
    case: dict[str, str] | None,
    review_date: dt.date,
    outcomes: list[dict[str, str]] | None = None,
    events: list[dict[str, Any]] | None = None,
) -> tuple[str, str, str, str]:
    forecast_date = parse_date(forecast.get("forecast_date")) or review_date
    elapsed = (review_date - forecast_date).days
    proof_gap = forecast.get("proof_gap", "")
    evidence = str(forecast.get("evidence_level", "")).upper()
    outcome = _verified_time_separated_outcome(forecast, outcomes or [], events or [], review_date)
    if outcome:
        outcome_type = str(outcome.get("outcome_type") or "").upper()
        outcome_id = str(outcome.get("outcome_id") or "")
        observed = f"Verified time-separated outcome {outcome_type} ({outcome_id})."
        if outcome_type in POSITIVE_OUTCOME_TYPES:
            return "HIT", observed, "", ""
        if outcome_type in JUSTIFIED_KILL_OUTCOME_TYPES:
            return "KILLED_CORRECTLY", observed, "", ""
        if outcome_type in NEGATIVE_OUTCOME_TYPES:
            return "MISS", observed, f"Verified negative outcome: {outcome_type}", ""

    eligible_at = parse_date(forecast.get("eligible_for_backtest_at"))
    if (eligible_at and review_date < eligible_at) or (
        not eligible_at and elapsed < horizon_days(forecast.get("horizon", ""))
    ):
        return "NOT_ENOUGH_TIME", f"Only {elapsed} day(s) elapsed; no source-register mutation expected.", "", ""
    return (
        "BLOCKED_BY_PROOF",
        "No verified, evidence-backed, time-separated outcome exists for this forecast.",
        "",
        "Collect a verified case outcome after the prediction timestamp.",
    )


def build_rows(
    forecasts: list[dict[str, str]],
    cases: list[dict[str, str]],
    review_date: dt.date,
    *,
    outcomes: list[dict[str, str]] | None = None,
    events: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    case_by_id = {row.get("case_id", ""): row for row in cases}
    rows: list[dict[str, str]] = []
    for forecast in forecasts:
        forecast_id = forecast.get("forecast_id", "")
        forecast_digest = hashlib.sha1(forecast_id.encode("utf-8")).hexdigest()[:8]
        case_id = forecast.get("case_or_research_id", "")
        case = case_by_id.get(case_id)
        outcome, observed, false_positive, false_negative = label_forecast(
            forecast,
            case,
            review_date,
            outcomes=outcomes,
            events=events,
        )
        forecast_date = parse_date(forecast.get("forecast_date")) or review_date
        predicted_probability = safe_float(forecast.get("predicted_probability"))
        outcome_map = {"HIT": 1, "PARTIAL_HIT": 1, "KILLED_CORRECTLY": 1, "MISS": 0}
        binary_outcome: int | str = outcome_map.get(outcome, "")
        is_mature = binary_outcome != ""
        brier = (predicted_probability - int(binary_outcome)) ** 2 if is_mature and predicted_probability else ""
        rows.append(
            {
                "backtest_id": f"FBT-{review_date.strftime('%Y%m%d')}-{slugify(forecast_id)[:72]}-{forecast_digest}",
                "forecast_id": forecast_id,
                "forecast_date": forecast_date.isoformat(),
                "review_date": review_date.isoformat(),
                "case_or_research_id": case_id,
                "forecast_type": forecast.get("forecast_type", ""),
                "predicted_action": forecast.get("next_safe_action", ""),
                "observed_outcome": observed,
                "outcome_label": outcome,
                "predicted_probability": f"{predicted_probability:.4f}" if predicted_probability else "",
                "binary_outcome": binary_outcome,
                "is_mature": "TRUE" if is_mature else "FALSE",
                "brier_component": f"{brier:.6f}" if brier != "" else "",
                "model_version": forecast.get("model_version", ""),
                "eligible_for_backtest_at": forecast.get("eligible_for_backtest_at", ""),
                "score_delta": "0",
                "false_positive_reason": false_positive,
                "false_negative_reason": false_negative,
                "learning_note": "Keep row-level review; do not calculate precision/recall until enough mature forecasts exist.",
                "config_change_recommended": "FALSE",
                "created_at": review_date.isoformat(),
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backtest V5 demand forecast candidates")
    parser.add_argument("--forecast-csv", default=str(FORECAST_PATH), help="Forecast candidates CSV")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output backtest CSV")
    parser.add_argument("--review-date", default=dt.date.today().isoformat(), help="Review date YYYY-MM-DD")
    parser.add_argument("--write", action="store_true", help="Write forecast_backtests.csv")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args(argv)

    forecast_path = Path(args.forecast_csv)
    if not forecast_path.is_absolute():
        forecast_path = PROJECT_ROOT / forecast_path
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    review_date = parse_date(args.review_date) or dt.date.today()
    try:
        from scripts.event_ledger import load_events
    except ModuleNotFoundError:  # pragma: no cover - direct execution path
        from event_ledger import load_events
    rows = build_rows(
        load_csv(forecast_path),
        load_csv(DATA_DIR / "master_cases.csv"),
        review_date,
        outcomes=load_csv(OUTCOMES_PATH),
        events=load_events(EVENTS_PATH),
    )
    if args.write:
        write_backtest_rows(output, rows)
        mature_count = sum(1 for row in rows if row.get("is_mature") == "TRUE")
        evaluation_digest = hashlib.sha256(
            json.dumps(rows, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]
        append_event(
            "forecast.backtest_evaluated",
            "V5 Forecast Backtest",
            object_type="forecast_backtest",
            object_id=f"FBT-RUN-{review_date.strftime('%Y%m%d')}",
            source="local_prediction_runtime",
            payload={
                "review_date": review_date.isoformat(),
                "evaluated_count": len(rows),
                "mature_count": mature_count,
                "output_path": rel(output),
            },
            citations=[rel(forecast_path), rel(output), "scripts/backtest_v5_demand_forecasts.py"],
            idempotency_key=f"forecast.backtest:{review_date.isoformat()}:{evaluation_digest}",
        )
    summary = {
        "ok": True,
        "mode": "write" if args.write else "dry-run",
        "forecast_csv": rel(forecast_path),
        "output": rel(output),
        "rows": len(rows),
        "label_counts": {label: sum(1 for row in rows if row["outcome_label"] == label) for label in sorted({row["outcome_label"] for row in rows})},
        "outcome_source": "data/case_outcomes.csv plus time-separated case.outcome_recorded events",
        "safety_boundary": "Internal-only backtest. Case status alone never matures a forecast and source registers were not mutated.",
    }
    if args.json:
        print(json.dumps(summary | {"preview": rows[:10]}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
