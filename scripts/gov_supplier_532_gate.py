#!/usr/bin/env python3
"""Evaluate the GOV supplier 5-3-2 gate without any supplier outreach.

The gate is deliberately evidence-bound: a marketplace listing is not a quote,
unproven candidate counts do not satisfy 5-3-2, and a GeM-origin case needs a
verified GeM registration path before pricing can be considered.
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
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - direct CLI dependency error
    yaml = None  # type: ignore[assignment]

try:
    from scripts.event_ledger import append_event
    from scripts.quote_proof import strict_quote_proofs
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import append_event  # type: ignore
    from quote_proof import strict_quote_proofs  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_PATH = PROJECT_ROOT / "config" / "supplier_532_gate.yaml"
DEFAULT_CASES_PATH = DATA_DIR / "master_cases.csv"
DEFAULT_SUPPLIERS_PATH = DATA_DIR / "supplier_master.csv"
DEFAULT_QUOTES_PATH = DATA_DIR / "quote_master.csv"
DEFAULT_EVENTS_PATH = DATA_DIR / "events.jsonl"
DEFAULT_REPORT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def uppercase(value: Any) -> str:
    return clean_text(value).upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load the supplier 5-3-2 gate")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Supplier 5-3-2 configuration must be a mapping: {path}")
    return value


def supplier_identity(row: dict[str, Any]) -> str:
    return clean_text(row.get("supplier_id")) or clean_text(row.get("supplier_name"))


def candidate_manifest_path(case_id: str, root: Path = DEFAULT_REPORT_ROOT) -> Path:
    return root / case_id / f"supplier_candidates_{case_id}.json"


def load_candidate_manifest(path: Path, *, case_id: str) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        candidates = value
        manifest_case_id = case_id
    elif isinstance(value, dict):
        candidates = value.get("candidates", [])
        manifest_case_id = clean_text(value.get("case_id"))
    else:
        raise ValueError("Supplier candidate manifest must be a JSON object or list")
    if manifest_case_id and manifest_case_id != case_id:
        raise ValueError(f"Supplier candidate manifest case_id {manifest_case_id} does not match {case_id}")
    if not isinstance(candidates, list) or not all(isinstance(item, dict) for item in candidates):
        raise ValueError("Supplier candidate manifest candidates must be a list of objects")
    return [dict(item) for item in candidates]


def evidence_complete(row: dict[str, Any], prefix: str) -> bool:
    path = clean_text(row.get(f"{prefix}_evidence_path"))
    digest = clean_text(row.get(f"{prefix}_evidence_sha256"))
    return bool(path and SHA256_RE.fullmatch(digest))


def gem_required(case: dict[str, Any]) -> bool:
    source_name = uppercase(case.get("source_name"))
    source_url = clean_text(case.get("source_url"))
    hostname = (urlparse(source_url).hostname or "").casefold()
    return (
        "GEM" in source_name
        or hostname == "gem.gov.in"
        or hostname.endswith(".gem.gov.in")
        or uppercase(case.get("gem_registration_required")) == "TRUE"
    )


def _supplier_index(suppliers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in suppliers:
        identity = supplier_identity(row)
        if identity:
            result[identity.casefold()] = row
    return result


def _effective_candidate(candidate: dict[str, Any], suppliers_by_identity: dict[str, dict[str, Any]]) -> dict[str, Any]:
    identity = supplier_identity(candidate)
    master = suppliers_by_identity.get(identity.casefold(), {}) if identity else {}
    # Candidate evidence is case-scoped. Master risk flags are authoritative if supplied.
    result = dict(master)
    result.update(candidate)
    for key in ("blacklisted", "watchlisted"):
        if clean_text(master.get(key)):
            result[key] = master[key]
    result["_identity"] = identity
    return result


def _candidate_assessment(candidate: dict[str, Any], *, require_gem: bool) -> dict[str, Any]:
    identity = clean_text(candidate.get("_identity"))
    blockers: list[str] = []
    source_type = clean_text(candidate.get("source_type"))
    if not identity:
        blockers.append("missing supplier_id or supplier_name")
    if not source_type:
        blockers.append("missing source_type")
    if uppercase(candidate.get("blacklisted")) == "TRUE":
        blockers.append("supplier is blacklisted")
    elif uppercase(candidate.get("blacklisted")) != "FALSE":
        blockers.append("blacklist status is not explicitly FALSE")
    if uppercase(candidate.get("watchlisted")) == "TRUE":
        blockers.append("supplier is watchlisted; owner waiver required")
    elif uppercase(candidate.get("watchlisted")) != "FALSE":
        blockers.append("watchlist status is not explicitly FALSE")
    if not evidence_complete(candidate, "source"):
        blockers.append("missing source evidence path/SHA-256")
    if uppercase(candidate.get("product_fit_status")) != "MATCHED":
        blockers.append("product_fit_status must be MATCHED")
    if not evidence_complete(candidate, "capacity_delivery"):
        blockers.append("missing capacity/delivery evidence path/SHA-256")
    gem_ok = True
    if require_gem:
        registration_verified = bool(
            evidence_complete(candidate, "gem_registration")
            or (
                clean_text(candidate.get("gem_registration_verified_at"))
                and clean_text(candidate.get("gem_seller_id"))
            )
        )
        gem_ok = uppercase(candidate.get("gem_registered")) == "TRUE" and registration_verified
        if not gem_ok:
            blockers.append("GeM registration is missing or lacks verified evidence")
    return {
        "supplier_identity": identity,
        "source_type": source_type,
        "eligible": not blockers,
        "capacity_delivery_evidence": evidence_complete(candidate, "capacity_delivery"),
        "gem_verified": gem_ok,
        "blockers": blockers,
    }


def evaluate_supplier_532(
    case: dict[str, Any],
    suppliers: list[dict[str, Any]],
    quotes: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a strict, non-mutating gate decision for one GOV case."""
    config = config or load_config()
    case_id = clean_text(case.get("case_id"))
    if not case_id:
        raise ValueError("case_id is required")
    if uppercase(case.get("workflow_type")) != "GOV":
        raise ValueError("Supplier 5-3-2 GOV gate requires workflow_type=GOV")
    require_gem = gem_required(case)
    supplier_index = _supplier_index(suppliers)
    assessed = [_candidate_assessment(_effective_candidate(item, supplier_index), require_gem=require_gem) for item in candidates]
    unique_candidates: dict[str, dict[str, Any]] = {}
    duplicate_candidate_ids: list[str] = []
    for item in assessed:
        identity = item["supplier_identity"].casefold()
        if not identity:
            continue
        if identity in unique_candidates:
            duplicate_candidate_ids.append(item["supplier_identity"])
            continue
        unique_candidates[identity] = item
    eligible = [item for item in unique_candidates.values() if item["eligible"]]
    source_types = sorted({item["source_type"] for item in eligible})
    strict_quotes = strict_quote_proofs(case_id, quotes)
    strict_quote_supplier_ids = sorted({supplier_identity(row) for row in strict_quotes if supplier_identity(row)})

    blockers: list[str] = []
    if len(eligible) < int(config.get("minimum_candidates", 5)):
        blockers.append(f"requires {config.get('minimum_candidates', 5)} eligible supplier candidates; found {len(eligible)}")
    if len(source_types) < int(config.get("minimum_source_types", 3)):
        blockers.append(f"requires {config.get('minimum_source_types', 3)} distinct supplier source types; found {len(source_types)}")
    if len(strict_quotes) < int(config.get("minimum_strict_supplier_quotes", 2)):
        blockers.append(f"requires {config.get('minimum_strict_supplier_quotes', 2)} strict supplier-specific quote proofs; found {len(strict_quotes)}")
    if not candidates:
        blockers.append("missing case-scoped supplier candidate manifest")
    if duplicate_candidate_ids:
        blockers.append("duplicate candidate identities: " + ", ".join(sorted(set(duplicate_candidate_ids))))

    eligible_by_id = {item["supplier_identity"].casefold(): item for item in eligible}
    quote_supplier_capacity_ready: list[str] = []
    for identity in strict_quote_supplier_ids:
        candidate = eligible_by_id.get(identity.casefold())
        if candidate is None:
            blockers.append(f"strict quote supplier {identity} is absent from eligible case candidates")
            continue
        if not candidate["capacity_delivery_evidence"]:
            blockers.append(f"strict quote supplier {identity} lacks capacity/delivery evidence")
            continue
        quote_supplier_capacity_ready.append(identity)
    if len(quote_supplier_capacity_ready) < int(config.get("minimum_strict_supplier_quotes", 2)):
        blockers.append("fewer than two strict quote suppliers have capacity/delivery evidence")
    if require_gem and any(not item["gem_verified"] for item in eligible):
        blockers.append("all pricing-eligible candidates must have verified GeM registration for this case")

    citations: list[str] = []
    for raw in candidates:
        for key in ("source_evidence_path", "capacity_delivery_evidence_path", "gem_registration_evidence_path"):
            value = clean_text(raw.get(key))
            if value and value not in citations:
                citations.append(value)
    for quote in strict_quotes:
        value = clean_text(quote.get("quote_proof_path"))
        if value and value not in citations:
            citations.append(value)
    report_body = {
        "case_id": case_id,
        "candidate_identities": sorted(unique_candidates),
        "strict_quote_ids": sorted(clean_text(row.get("quote_id")) for row in strict_quotes),
        "config": {
            "minimum_candidates": config.get("minimum_candidates", 5),
            "minimum_source_types": config.get("minimum_source_types", 3),
            "minimum_strict_supplier_quotes": config.get("minimum_strict_supplier_quotes", 2),
        },
    }
    return {
        "schema_version": "gov_supplier_532_gate.v1",
        "case_id": case_id,
        "workflow_type": "GOV",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS" if not blockers else "BLOCKED",
        "required_gem_registration": require_gem,
        "counts": {
            "candidate_manifest_count": len(candidates),
            "eligible_candidate_count": len(eligible),
            "source_type_count": len(source_types),
            "strict_quote_proof_count": len(strict_quotes),
            "strict_quote_supplier_capacity_delivery_count": len(quote_supplier_capacity_ready),
        },
        "source_types": source_types,
        "eligible_candidates": eligible,
        "strict_quote_ids": report_body["strict_quote_ids"],
        "strict_quote_supplier_capacity_delivery_ids": quote_supplier_capacity_ready,
        "blockers": sorted(dict.fromkeys(blockers)),
        "citations": citations,
        "input_fingerprint": hashlib.sha256(json.dumps(report_body, sort_keys=True).encode("utf-8")).hexdigest(),
        "external_actions_executed": False,
    }


def render_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    lines = [
        f"# GOV Supplier 5-3-2 Gate — {report['case_id']}",
        "",
        f"- Status: `{report['status']}`",
        f"- GeM registration required: `{str(report['required_gem_registration']).lower()}`",
        f"- Eligible candidates: `{counts['eligible_candidate_count']}`",
        f"- Source types: `{counts['source_type_count']}` ({', '.join(report['source_types']) or 'none'})",
        f"- Strict supplier-specific quote proofs: `{counts['strict_quote_proof_count']}`",
        f"- Quote suppliers with capacity/delivery evidence: `{counts['strict_quote_supplier_capacity_delivery_count']}`",
        "- External actions executed: `false`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {blocker}" for blocker in report["blockers"] or ["None"])
    lines.extend(["", "## Evidence paths", ""])
    lines.extend(f"- `{citation}`" for citation in report["citations"] or ["No evidence paths supplied."])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a readiness gate only. PASS does not select a supplier, authorize an RFQ, finalize price, commit delivery, submit, pay, or use DSC.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"supplier_532_{report['case_id']}.json"
    markdown_path = output_dir / f"supplier_532_{report['case_id']}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json_path": json_path, "markdown_path": markdown_path}


def record_gate_event(report: dict[str, Any], *, report_path: Path, events_path: Path = DEFAULT_EVENTS_PATH, actor: str = "gov_supplier_532_gate") -> str:
    event = append_event(
        "supplier.readiness_evaluated",
        actor,
        case_id=report["case_id"],
        object_type="supplier_match",
        object_id=f"{report['case_id']}:supplier_532",
        source="gov_supplier_532_gate",
        payload={
            "case_id": report["case_id"],
            "report_path": str(report_path),
            "status": report["status"],
            "input_fingerprint": report["input_fingerprint"],
        },
        citations=[str(report_path), *report["citations"]],
        idempotency_key=f"gov-supplier-532:{report['case_id']}:{report['input_fingerprint']}",
        events_file=events_path,
    )
    return str(event["event_id"])


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--master-cases", default=str(DEFAULT_CASES_PATH))
    parser.add_argument("--suppliers", default=str(DEFAULT_SUPPLIERS_PATH))
    parser.add_argument("--quotes", default=str(DEFAULT_QUOTES_PATH))
    parser.add_argument("--candidates", default="", help="Case-scoped candidate manifest JSON")
    parser.add_argument("--events", default=str(DEFAULT_EVENTS_PATH))
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--write", action="store_true", help="Write internal report and canonical gate event")
    parser.add_argument("--allow-blocked", action="store_true", help="Report an expected blocked gate without a non-zero exit")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cases = read_csv(_resolve(args.master_cases))
    case = next((row for row in cases if row.get("case_id") == args.case_id), None)
    if case is None:
        raise SystemExit(f"No Master Case Register row found for {args.case_id}")
    candidates_path = _resolve(args.candidates) if args.candidates else candidate_manifest_path(args.case_id)
    report = evaluate_supplier_532(
        case,
        read_csv(_resolve(args.suppliers)),
        read_csv(_resolve(args.quotes)),
        load_candidate_manifest(candidates_path, case_id=args.case_id),
    )
    payload: dict[str, Any] = {
        "mode": "write" if args.write else "dry_run",
        "case_id": report["case_id"],
        "status": report["status"],
        "counts": report["counts"],
        "blockers": report["blockers"],
        "external_actions_executed": False,
    }
    if args.write:
        output_dir = _resolve(args.output_dir) if args.output_dir else DEFAULT_REPORT_ROOT / args.case_id
        paths = write_report(report, output_dir)
        payload.update({key: str(value) for key, value in paths.items()})
        payload["event_id"] = record_gate_event(report, report_path=paths["json_path"], events_path=_resolve(args.events))
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"GOV supplier 5-3-2 gate: {payload}")
    return 0 if report["status"] == "PASS" or args.allow_blocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
