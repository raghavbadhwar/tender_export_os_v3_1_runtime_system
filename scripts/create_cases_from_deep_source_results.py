#!/usr/bin/env python3
"""Promote deep source results into case candidates through the event ledger."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from scripts.event_ledger import append_event  # noqa: E402
from scripts.source_runtime.credential_policy import sanitize_payload  # noqa: E402
from scripts.source_runtime.dedupe import DedupeEngine  # noqa: E402
from scripts.source_runtime.evidence_store import safe_name  # noqa: E402

MASTER_CASES = PROJECT_ROOT / "data" / "master_cases.csv"
RUNTIME_CONFIG = PROJECT_ROOT / "config" / "deep_source_runtime.yaml"


def today_compact() -> str:
    return dt.datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y%m%d")


def today_iso() -> str:
    return dt.datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()


def load_min_confidence_score(path: Path = RUNTIME_CONFIG) -> int:
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return int(data.get("case_creation", {}).get("min_confidence_score", 55))
    except Exception:
        return 55


def parse_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    if not value:
        return None
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d %b %Y", "%d %B %Y"]
    for fmt in formats:
        try:
            return dt.datetime.strptime(value[:20], fmt).date()
        except ValueError:
            continue
    return None


def next_case_ids() -> dict[str, int]:
    maxes = {"GOV": 0, "EXP": 0, "SUP": 0}
    date_str = today_compact()
    if MASTER_CASES.exists():
        with MASTER_CASES.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                case_id = row.get("case_id", "")
                for prefix in maxes:
                    stem = f"{prefix}-{date_str}-"
                    if case_id.startswith(stem):
                        try:
                            maxes[prefix] = max(maxes[prefix], int(case_id.split("-")[-1]))
                        except ValueError:
                            pass
    return maxes


def workflow_prefix(workflow: str) -> str:
    value = (workflow or "GOV").upper()
    if value == "EXPORT":
        return "EXP"
    if value == "SUPPLIER":
        return "SUP"
    return value if value in {"GOV", "EXP", "SUP"} else "GOV"


def build_case_row(case_id: str, result: dict[str, Any]) -> dict[str, Any]:
    shallow = result.get("shallow", {})
    extracted = result.get("extracted", {})
    workflow = extracted.get("workflow_type") or shallow.get("workflow_type") or "GOV"
    return {
        "case_id": case_id,
        "workflow_type": workflow,
        "source_name": shallow.get("source_name") or extracted.get("source_portal", ""),
        "source_url": shallow.get("source_url") or extracted.get("source_url", ""),
        "opportunity_title": extracted.get("title") or shallow.get("opportunity_title", ""),
        "buyer_name": extracted.get("buyer_organisation") or shallow.get("buyer_name", ""),
        "location": extracted.get("city", ""),
        "state": extracted.get("state", ""),
        "product_or_service": extracted.get("product_or_service") or shallow.get("product_or_service", ""),
        "quantity": shallow.get("quantity", ""),
        "unit": shallow.get("unit", ""),
        "estimated_value_inr": extracted.get("tender_value_inr") or shallow.get("estimated_value_inr", ""),
        "deadline_date": extracted.get("bid_end_date") or shallow.get("deadline_date", ""),
        "emd_amount_inr": extracted.get("emd_amount_inr", ""),
        "turnover_required_inr": extracted.get("turnover_requirement", ""),
        "past_experience_required": "TRUE" if extracted.get("past_experience_requirement") else "",
        "experience_details": extracted.get("past_experience_requirement", ""),
        "oem_required": "TRUE" if extracted.get("oem_authorization_required") or "OEM_AUTH_REQUIRED" in extracted.get("risk_flags", []) else "",
        "mandatory_certs": extracted.get("certification_requirement", ""),
        "delivery_location": extracted.get("delivery_location", ""),
        "payment_terms": extracted.get("payment_terms", ""),
        "penalty_clause": "; ".join(item.get("text", "") for item in extracted.get("important_clauses", []) if item.get("type") == "penalty"),
        "status": "NEW",
        "deep_read_done": "TRUE",
        "supplier_search_done": "FALSE",
        "pricing_done": "FALSE",
        "approval_status": "NOT_REQUESTED",
        "notes": f"Created from deep source evidence. Evidence: {result.get('evidence_dir', '')}. Missing fields: {', '.join(extracted.get('missing_fields', []))}",
        "created_at": today_iso(),
        "updated_at": today_iso(),
        "created_by_agent": "deep_source_runtime",
    }


def should_skip(result: dict[str, Any], respect_deadline: bool, min_confidence_score: int | None = None) -> tuple[bool, str]:
    if result.get("blocker_status") and not result.get("evidence_dir"):
        return True, "blocked page with no evidence"
    extracted = result.get("extracted", {})
    confidence = int(extracted.get("confidence_score") or 0)
    threshold = min_confidence_score if min_confidence_score is not None else load_min_confidence_score()
    if confidence < threshold:
        return True, f"low confidence: {confidence}"
    if respect_deadline:
        deadline = parse_date(extracted.get("bid_end_date", ""))
        if deadline and deadline < dt.datetime.now(ZoneInfo("Asia/Kolkata")).date():
            return True, f"expired deadline: {deadline.isoformat()}"
    return False, ""


def write_historical_intelligence(result: dict[str, Any], reason: str) -> Path:
    if "expired" in reason:
        bucket = "expired_tenders"
    elif "low confidence" in reason:
        bucket = "low_confidence_leads"
    else:
        bucket = "blocked_or_incomplete_leads"
    root = PROJECT_ROOT / "outputs" / "intelligence" / bucket
    root.mkdir(parents=True, exist_ok=True)
    name = safe_name(result.get("shallow", {}).get("external_reference", "") or result.get("shallow", {}).get("opportunity_title", "") or "source_result")
    path = root / f"{name}.json"
    path.write_text(json.dumps(sanitize_payload({"reason": reason, "result": result}), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def create_cases_from_file(path: Path | str, respect_deadline: bool = False, record_event: bool = False) -> list[str]:
    input_path = Path(path)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    data = json.loads(input_path.read_text(encoding="utf-8"))
    deep_results: list[dict[str, Any]] = []
    for run_result in data.get("results", []):
        deep_results.extend(run_result.get("deep_results", []))

    dedupe = DedupeEngine()
    counters = next_case_ids()
    min_confidence = load_min_confidence_score()
    created: list[str] = []
    for result in deep_results:
        skip, reason = should_skip(result, respect_deadline, min_confidence)
        if skip:
            evidence = write_historical_intelligence(result, reason)
            if record_event:
                append_event(
                    "source_adapter.dedupe_skipped" if "duplicate" in reason else "source_adapter.case_candidate_skipped",
                    "create_cases_from_deep_source_results",
                    object_type="source_adapter",
                    object_id=result.get("shallow", {}).get("external_reference", ""),
                    source=result.get("shallow", {}).get("source_name", ""),
                    payload={"reason": reason},
                    citations=[str(evidence.relative_to(PROJECT_ROOT))],
                )
            continue
        duplicate_case = dedupe.find_duplicate(_dict_to_deep_result_like(result))
        if duplicate_case:
            if record_event:
                append_event(
                    "source_adapter.dedupe_skipped",
                    "create_cases_from_deep_source_results",
                    case_id=duplicate_case,
                    object_type="source_adapter",
                    object_id=result.get("shallow", {}).get("external_reference", ""),
                    source=result.get("shallow", {}).get("source_name", ""),
                    payload={"duplicate_case_id": duplicate_case, "evidence_dir": result.get("evidence_dir", "")},
                    citations=result.get("citations", []),
                )
            continue
        workflow = result.get("extracted", {}).get("workflow_type") or result.get("shallow", {}).get("workflow_type", "GOV")
        prefix = workflow_prefix(workflow)
        counters[prefix] += 1
        case_id = f"{prefix}-{today_compact()}-{counters[prefix]:03d}"
        row = build_case_row(case_id, result)
        append_event(
            "case.created",
            "create_cases_from_deep_source_results",
            case_id=case_id,
            object_type="case",
            object_id=case_id,
            source=result.get("shallow", {}).get("source_name", "deep_source_runtime"),
            payload=sanitize_payload(row),
            citations=result.get("citations", []) + [str(input_path.relative_to(PROJECT_ROOT))],
        )
        report_dir = PROJECT_ROOT / "outputs" / "case_reports" / case_id
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / f"deep_source_candidate_{case_id}.json").write_text(json.dumps(sanitize_payload(result), indent=2, ensure_ascii=False), encoding="utf-8")
        created.append(case_id)
    return created


def _dict_to_deep_result_like(result: dict[str, Any]):
    from scripts.source_adapters.base import DeepExtractedFields, DeepSourceOpportunity, SourceDocument, SourceOpportunity

    shallow = SourceOpportunity(**{key: value for key, value in result.get("shallow", {}).items() if key in SourceOpportunity.__dataclass_fields__})
    extracted = DeepExtractedFields(**{key: value for key, value in result.get("extracted", {}).items() if key in DeepExtractedFields.__dataclass_fields__})
    documents = [SourceDocument(**{key: value for key, value in item.items() if key in SourceDocument.__dataclass_fields__}) for item in result.get("documents", [])]
    return DeepSourceOpportunity(shallow=shallow, extracted=extracted, documents=documents)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create case candidates from deep source results")
    parser.add_argument("input", help="Path to outputs/source_runs/{run_id}/deep_results.json")
    parser.add_argument("--respect-deadline", action="store_true", help="Skip expired tenders")
    parser.add_argument("--record-event", action="store_true", help="Record skip/dedupe helper events")
    args = parser.parse_args()
    created = create_cases_from_file(args.input, respect_deadline=args.respect_deadline, record_event=args.record_event)
    print(f"Created {len(created)} case candidate(s): {', '.join(created) if created else 'none'}")
    print("Run scripts/rebuild_projections_from_events.py --write after reviewing events if you want CSV projections updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
