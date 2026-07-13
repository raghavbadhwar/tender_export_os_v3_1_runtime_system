#!/usr/bin/env python3
"""Build supplier performance projections from verified operational evidence."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any

try:
    from scripts.event_ledger import append_event
    from scripts.quote_proof import as_bool, classify_quote_proof, is_indicative_signal, norm, positive_number
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import append_event  # type: ignore
    from quote_proof import as_bool, classify_quote_proof, is_indicative_signal, norm, positive_number  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "supplier_performance_projection.schema.json"
DEFAULT_SUPPLIERS_PATH = DATA_DIR / "supplier_master.csv"
DEFAULT_QUOTES_PATH = DATA_DIR / "quote_master.csv"
DEFAULT_OUTCOMES_PATH = DATA_DIR / "case_outcomes.csv"
DEFAULT_EVENTS_PATH = DATA_DIR / "events.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "supplier_performance"

DELIVERY_OUTCOMES = {"DELIVERED", "WORK_ORDER_RECEIVED", "ORDER_RECEIVED"}
DOCUMENTATION_OUTCOMES = {
    "SUBMISSION_ACKNOWLEDGED",
    "TECHNICAL_QUALIFIED",
    "CUSTOMS_CLEARED",
    "INVOICED",
}
PAYMENT_OUTCOMES = {"PAYMENT_RECEIVED", "PAYMENT_DUE", "PAYMENT_DELAYED"}
DEFECT_OUTCOMES = {"CLAIM_OR_RETURN", "TECHNICAL_DISQUALIFIED"}
WEAK_SOURCE_PLATFORMS = {
    "indiamart",
    "tradeindia",
    "exportersindia",
    "google maps",
    "openstreetmap",
    "overpass",
    "public_listing",
    "marketplace",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Supplier performance schema must be an object: {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def upper(value: Any) -> str:
    return clean(value).upper()


def number(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def supplier_identity(row: dict[str, Any]) -> str:
    return clean(row.get("supplier_id")) or clean(row.get("supplier_name"))


def hash_report(report: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(report, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def weak_public_signal(supplier: dict[str, Any]) -> bool:
    platform = clean(supplier.get("source_platform")).casefold()
    source_type = clean(supplier.get("source_type")).casefold()
    notes = clean(supplier.get("notes")).casefold()
    return (
        as_bool(supplier.get("is_indicative_price_only"))
        or any(token in platform for token in WEAK_SOURCE_PLATFORMS)
        or any(token in source_type for token in WEAK_SOURCE_PLATFORMS)
        or "public listing" in notes
        or "marketplace" in notes
    )


def verified_quote_rows(quotes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for quote in quotes:
        if classify_quote_proof(quote)["is_strict_quote_proof"]:
            rows.append(quote)
    return rows


def selected_case_supplier_map(quotes: list[dict[str, Any]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for quote in verified_quote_rows(quotes):
        if not (as_bool(quote.get("selected_for_pricing")) or as_bool(quote.get("used_in_approved_bid"))):
            continue
        case_id = clean(quote.get("case_id"))
        supplier_id = supplier_identity(quote)
        if case_id and supplier_id:
            result.setdefault(case_id, set()).add(supplier_id)
    return result


def outcomes_by_supplier(
    outcomes: list[dict[str, Any]],
    quotes: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    case_supplier = selected_case_supplier_map(quotes)
    result: dict[str, list[dict[str, Any]]] = {}
    for outcome in outcomes:
        if upper(outcome.get("verification_status")) != "VERIFIED":
            continue
        for supplier_id in case_supplier.get(clean(outcome.get("case_id")), set()):
            result.setdefault(supplier_id, []).append(outcome)
    return result


def load_owner_corrections(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("owner corrections must be a JSON list of objects")
    return [dict(item) for item in value]


def verified_corrections_by_supplier(corrections: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for correction in corrections:
        supplier_id = clean(correction.get("supplier_id"))
        if not supplier_id:
            continue
        if upper(correction.get("verification_status")) not in {"VERIFIED", "EVIDENCE_PRESENT"}:
            continue
        result.setdefault(supplier_id, []).append(correction)
    return result


def quote_metrics(quotes: list[dict[str, Any]]) -> dict[str, Any]:
    strict = verified_quote_rows(quotes)
    response_hours = [value for value in (number(row.get("response_hrs")) for row in strict) if value is not None and value >= 0]
    clarity_scores = [value for value in (number(row.get("quote_clarity_score")) for row in strict) if value is not None and value >= 0]
    lead_times = [value for value in (number(row.get("lead_time_days")) for row in strict) if value is not None and value > 0]
    payment_terms = sorted({clean(row.get("payment_terms_offered")) for row in strict if clean(row.get("payment_terms_offered"))})
    return {
        "strict_quote_count": len(strict),
        "avg_response_hrs": round(mean(response_hours), 2) if response_hours else None,
        "avg_quote_clarity_score": round(mean(clarity_scores), 2) if clarity_scores else None,
        "avg_lead_time_days": round(mean(lead_times), 2) if lead_times else None,
        "payment_terms_seen": payment_terms,
    }


def outcome_counts(outcomes: list[dict[str, Any]]) -> dict[str, int]:
    types = [upper(row.get("outcome_type")) for row in outcomes]
    return {
        "delivery_evidence": sum(item in DELIVERY_OUTCOMES for item in types),
        "documentation_evidence": sum(item in DOCUMENTATION_OUTCOMES for item in types),
        "payment_terms_evidence": sum(item in PAYMENT_OUTCOMES for item in types),
        "defect_or_claim_evidence": sum(item in DEFECT_OUTCOMES for item in types),
    }


def score_projection(
    *,
    quotes: dict[str, Any],
    outcomes: dict[str, int],
    corrections: list[dict[str, Any]],
    weak_signal_only: bool,
) -> tuple[int, str, list[str]]:
    score = 50
    notes: list[str] = []
    if quotes["strict_quote_count"]:
        score += min(18, quotes["strict_quote_count"] * 6)
    if quotes["avg_response_hrs"] is not None:
        score += 8 if quotes["avg_response_hrs"] <= 24 else 3 if quotes["avg_response_hrs"] <= 72 else -3
    if quotes["avg_quote_clarity_score"] is not None:
        score += 8 if quotes["avg_quote_clarity_score"] >= 75 else 3 if quotes["avg_quote_clarity_score"] >= 50 else -4
    score += min(10, outcomes["delivery_evidence"] * 5)
    score += min(8, outcomes["documentation_evidence"] * 4)
    score += min(8, outcomes["payment_terms_evidence"] * 4)
    score -= min(18, outcomes["defect_or_claim_evidence"] * 9)

    for correction in corrections:
        direction = upper(correction.get("direction"))
        if direction == "POSITIVE":
            score += 5
        elif direction == "NEGATIVE":
            score -= 8
        notes.append(clean(correction.get("summary")) or clean(correction.get("notes")) or "owner correction recorded")

    operational = any(outcomes.values()) or bool(corrections)
    if operational:
        status = "OPERATIONAL_EVIDENCE"
    elif quotes["strict_quote_count"]:
        status = "QUOTE_VERIFIED"
    elif weak_signal_only:
        status = "WEAK_PUBLIC_SIGNAL_ONLY"
    else:
        status = "NO_OPERATIONAL_HISTORY"
    if any(upper(item.get("direction")) == "NEGATIVE" for item in corrections) or outcomes["defect_or_claim_evidence"]:
        status = "OWNER_REVIEW"
    return max(0, min(100, score)), status, notes


def recommendation_proposal(
    *,
    supplier_id: str,
    supplier_name: str,
    score: int,
    status: str,
    quote_summary: dict[str, Any],
    outcome_summary: dict[str, int],
    corrections: list[dict[str, Any]],
    blockers: list[str],
) -> dict[str, Any]:
    sample_size = quote_summary["strict_quote_count"] + sum(outcome_summary.values()) + len(corrections)
    uncertainty = "LOW" if sample_size >= 10 and status == "OPERATIONAL_EVIDENCE" else "MEDIUM" if sample_size >= 3 else "HIGH"
    if status in {"OPERATIONAL_EVIDENCE", "QUOTE_VERIFIED"} and score >= 70:
        recommendation = "Prefer for internal shortlist after case-specific proof checks."
    elif status == "OWNER_REVIEW":
        recommendation = "Keep available but require owner review before shortlist promotion."
    else:
        recommendation = "Do not promote beyond discovery pool until strict quote/outcome evidence improves."
    proposal_basis = f"{supplier_id}:{supplier_name}:{status}:{score}:{sample_size}"
    return {
        "proposal_id": f"SUP-RANK-{hashlib.sha1(proposal_basis.encode('utf-8')).hexdigest()[:12]}",
        "proposal_type": "SUPPLIER_RANKING_RECOMMENDATION",
        "proposal_status": "RECOMMENDATION_ONLY_NOT_APPLIED",
        "recommended_action": recommendation,
        "sample_size": sample_size,
        "observation_window": {
            "start": "derived_from_verified_quotes_outcomes_and_owner_corrections",
            "end": utc_now(),
        },
        "uncertainty": uncertainty,
        "false_positive_impact": "Over-promoting this supplier can create pricing, delivery, documentation, or quality risk from weak evidence.",
        "false_negative_impact": "Under-promoting this supplier can slow quote collection or miss a reliable category-fit supplier.",
        "rollback_plan": "Keep supplier score/ranking advisory; if promoted later, restore prior shortlist position and require fresh quote/outcome review.",
        "automatic_change_allowed": False,
        "blockers": blockers,
    }


def project_supplier(
    supplier: dict[str, Any],
    *,
    quotes: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    corrections: list[dict[str, Any]],
) -> dict[str, Any]:
    supplier_id = supplier_identity(supplier)
    supplier_quotes = [row for row in quotes if supplier_identity(row) == supplier_id]
    quote_summary = quote_metrics(supplier_quotes)
    weak_quotes = sum(is_indicative_signal(row) for row in supplier_quotes)
    outcome_summary = outcome_counts(outcomes)
    weak_signal = weak_public_signal(supplier) or weak_quotes > 0
    score, status, correction_notes = score_projection(
        quotes=quote_summary,
        outcomes=outcome_summary,
        corrections=corrections,
        weak_signal_only=weak_signal,
    )
    blockers: list[str] = []
    if not quote_summary["strict_quote_count"]:
        blockers.append("no verified supplier-specific quote response")
    if not any(outcome_summary.values()):
        blockers.append("no verified delivery/documentation/payment/defect outcome evidence")
    if weak_signal and status == "WEAK_PUBLIC_SIGNAL_ONLY":
        blockers.append("public listing or marketplace signal is weak evidence only")

    return {
        "supplier_id": clean(supplier.get("supplier_id")),
        "supplier_name": clean(supplier.get("supplier_name")),
        "projection_status": status,
        "score": score,
        "confidence": "MEDIUM" if status == "OPERATIONAL_EVIDENCE" else "LOW",
        "evidence_counts": {
            "verified_quote_responses": quote_summary["strict_quote_count"],
            **outcome_summary,
            "owner_corrections": len(corrections),
            "weak_public_signals": int(weak_signal) + weak_quotes,
        },
        "operational_signals": {
            "avg_response_hrs": quote_summary["avg_response_hrs"],
            "avg_quote_clarity_score": quote_summary["avg_quote_clarity_score"],
            "avg_lead_time_days": quote_summary["avg_lead_time_days"],
            "payment_terms_seen": quote_summary["payment_terms_seen"],
        },
        "weak_evidence": {
            "public_listing_or_marketplace_signal": weak_signal,
            "source_type": clean(supplier.get("source_type")),
            "source_platform": clean(supplier.get("source_platform")),
            "not_counted_as_delivery_history": True,
        },
        "blockers": blockers,
        "owner_correction_notes": correction_notes,
        "recommendation_proposal": recommendation_proposal(
            supplier_id=clean(supplier.get("supplier_id")),
            supplier_name=clean(supplier.get("supplier_name")),
            score=score,
            status=status,
            quote_summary=quote_summary,
            outcome_summary=outcome_summary,
            corrections=corrections,
            blockers=blockers,
        ),
    }


def build_projection(
    *,
    suppliers: list[dict[str, Any]],
    quotes: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    owner_corrections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    schema = load_schema()
    outcomes_index = outcomes_by_supplier(outcomes, quotes)
    corrections_index = verified_corrections_by_supplier(owner_corrections or [])
    projected = [
        project_supplier(
            supplier,
            quotes=quotes,
            outcomes=outcomes_index.get(supplier_identity(supplier), []),
            corrections=corrections_index.get(supplier_identity(supplier), []),
        )
        for supplier in suppliers
    ]
    status = "PASS" if projected else "BLOCKED"
    return {
        "schema_version": schema["schema_version"],
        "generated_at": utc_now(),
        "projection_status": status,
        "external_actions_executed": False,
        "supplier_count": len(projected),
        "summary": {
            "operational_evidence_suppliers": sum(row["projection_status"] in {"OPERATIONAL_EVIDENCE", "OWNER_REVIEW"} for row in projected),
            "strict_quote_suppliers": sum(row["evidence_counts"]["verified_quote_responses"] > 0 for row in projected),
            "weak_public_signal_only_suppliers": sum(row["projection_status"] == "WEAK_PUBLIC_SIGNAL_ONLY" for row in projected),
            "owner_review_suppliers": sum(row["projection_status"] == "OWNER_REVIEW" for row in projected),
        },
        "proposal_contract": {
            "automatic_supplier_ranking_changes_allowed": False,
            "required_fields": [
                "proposal_id",
                "sample_size",
                "observation_window",
                "uncertainty",
                "false_positive_impact",
                "false_negative_impact",
                "rollback_plan",
            ],
        },
        "suppliers": projected,
        "boundary": schema["boundary"],
    }


def write_projection(report: dict[str, Any], *, output_dir: Path, events_path: Path = DEFAULT_EVENTS_PATH) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    digest = hash_report(report)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"supplier_performance_projection_{timestamp}_{digest[:10]}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    event = append_event(
        "supplier.performance_projected",
        "learning_evaluation",
        case_id="",
        object_type="supplier_performance",
        object_id=digest,
        source="supplier_performance_projection",
        payload={
            "report_path": str(output_path.relative_to(PROJECT_ROOT)),
            "schema_version": report["schema_version"],
            "supplier_count": report["supplier_count"],
            "report_sha256": digest,
        },
        citations=[str(output_path.relative_to(PROJECT_ROOT))],
        idempotency_key=f"supplier-performance:{digest}",
        events_file=events_path,
    )
    return {"report_path": str(output_path), "report_sha256": digest, "event_id": str(event["event_id"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suppliers", default=str(DEFAULT_SUPPLIERS_PATH))
    parser.add_argument("--quotes", default=str(DEFAULT_QUOTES_PATH))
    parser.add_argument("--outcomes", default=str(DEFAULT_OUTCOMES_PATH))
    parser.add_argument("--owner-corrections", default="")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    corrections_path = Path(args.owner_corrections).expanduser() if args.owner_corrections else None
    report = build_projection(
        suppliers=read_csv(Path(args.suppliers).expanduser()),
        quotes=read_csv(Path(args.quotes).expanduser()),
        outcomes=read_csv(Path(args.outcomes).expanduser()),
        owner_corrections=load_owner_corrections(corrections_path),
    )
    payload: dict[str, Any] = {
        "status": report["projection_status"],
        "mode": "write" if args.write else "dry_run",
        "report": report,
        "external_actions_executed": False,
    }
    if args.write:
        payload.update(write_projection(report, output_dir=Path(args.output_dir).expanduser()))
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"Supplier performance projection: {payload['status']}")
    return 0 if report["projection_status"] != "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
