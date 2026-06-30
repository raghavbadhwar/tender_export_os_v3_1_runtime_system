#!/usr/bin/env python3
"""Validate whether cases have the evidence needed for their current or next stage."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def quote_proofs(case_id: str, quotes: list[dict]) -> list[dict]:
    return [
        quote for quote in quotes
        if quote.get("case_id") == case_id and quote.get("quote_received_at")
    ]


def pending_approvals(case_id: str, approvals: list[dict]) -> list[dict]:
    return [
        approval for approval in approvals
        if approval.get("case_id") == case_id and approval.get("approval_status") == "PENDING"
    ]


def rfq_for_case(case_id: str, rfqs: list[dict]) -> dict:
    for rfq in rfqs:
        if rfq.get("case_id") == case_id:
            return rfq
    return {}


def card_exists(approval: dict) -> bool:
    path = approval.get("approval_card_path", "")
    return bool(path and (PROJECT_ROOT / path).exists())


def check_required(case: dict, fields: list[str], blockers: list[str]) -> None:
    for field in fields:
        if not case.get(field, ""):
            blockers.append(f"missing {field}")


def evaluate_case(case: dict, quotes: list[dict], approvals: list[dict], rfqs: list[dict] | None = None) -> dict:
    case_id = case.get("case_id", "")
    workflow = case.get("workflow_type", "")
    status = case.get("status", "")
    blockers: list[str] = []
    warnings: list[str] = []
    next_allowed = True
    rfqs = rfqs or []

    check_required(case, ["case_id", "workflow_type", "opportunity_title", "status"], blockers)

    if status in {"NEW", "FAST_KILL", "WATCHLIST", "DEEP_READ"}:
        check_required(case, ["source_name", "opportunity_title", "product_or_service"], blockers)

    if status == "SUPPLIER_SEARCH":
        check_required(case, ["product_or_service", "quantity", "unit"], blockers)
        if workflow == "GOV":
            check_required(case, ["delivery_location"], blockers)
        if workflow == "EXPORT":
            if not (case.get("delivery_location") or case.get("buyer_country")):
                blockers.append("missing export delivery_location or buyer_country")
        proofs = quote_proofs(case_id, quotes)
        if len(proofs) < 2:
            warnings.append(f"only {len(proofs)} quote proof(s); pricing gate requires 2")
            next_allowed = False

    if status == "PRICING_READY":
        proofs = quote_proofs(case_id, quotes)
        if len(proofs) < 2:
            blockers.append(f"PRICING_READY requires 2 quote proofs; found {len(proofs)}")
        if case.get("pricing_done") != "TRUE":
            blockers.append("pricing_done must be TRUE for PRICING_READY")

    if status == "ARTIFACT_PRODUCTION":
        if case.get("pricing_done") != "TRUE":
            blockers.append("artifact production requires pricing_done=TRUE")

    if status == "APPROVAL_REQUIRED":
        pending = pending_approvals(case_id, approvals)
        if not pending:
            blockers.append("APPROVAL_REQUIRED case has no pending approval")
        missing_cards = [approval.get("approval_id") for approval in pending if not card_exists(approval)]
        if missing_cards:
            blockers.append(f"pending approvals missing cards: {missing_cards}")

    if workflow == "EXPORT":
        rfq = rfq_for_case(case_id, rfqs)
        beyond_discovery = status not in {"NEW", "FAST_KILL", "REJECTED", "WATCHLIST", "DEEP_READ", "ARCHIVED", "LOST"}
        if beyond_discovery:
            if not rfq:
                blockers.append("missing linked RFQ verification row in data/rfq_master.csv")
            elif rfq.get("rfq_stage") not in {"RFQ_VERIFIED", "READY_FOR_SUPPLIER_PROOF"}:
                blockers.append(
                    f"linked RFQ is {rfq.get('rfq_stage') or 'UNKNOWN'}; export cases cannot advance beyond discovery without RFQ_VERIFIED"
                )
            elif rfq.get("evidence_status") != "RFQ_VERIFIED":
                blockers.append(
                    f"linked RFQ evidence_status is {rfq.get('evidence_status') or 'UNKNOWN'}; RFQ_VERIFIED required"
                )
        if case.get("scomet_flag") == "TRUE":
            blockers.append("SCOMET suspected; specialist review required")
        if status in {"PRICING_READY", "ARTIFACT_PRODUCTION", "APPROVAL_REQUIRED", "APPROVED"}:
            if not case.get("hsn_itchs_candidate"):
                blockers.append("missing draft HSN/ITC-HS candidate")
            if not case.get("export_policy"):
                blockers.append("missing export policy note")

    if blockers:
        next_allowed = False

    return {
        "case_id": case_id,
        "workflow_type": workflow,
        "status": status,
        "next_allowed": next_allowed,
        "blockers": blockers,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate case readiness gates")
    parser.add_argument("--case-id", help="Validate one case")
    parser.add_argument("--all", action="store_true", help="Validate all cases")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if blockers or warnings exist")
    args = parser.parse_args()

    if not args.case_id and not args.all:
        print("Provide --case-id or --all.")
        return 2

    cases = load_csv(DATA_DIR / "master_cases.csv")
    quotes = load_csv(DATA_DIR / "quote_master.csv")
    approvals = load_csv(DATA_DIR / "approvals_receipts.csv")
    rfqs = load_csv(DATA_DIR / "rfq_master.csv")
    selected = [case for case in cases if args.all or case.get("case_id") == args.case_id]
    if not selected:
        print("No matching cases found.")
        return 1

    results = [evaluate_case(case, quotes, approvals, rfqs) for case in selected]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            state = "READY" if result["next_allowed"] else "BLOCKED"
            print(f"{result['case_id']} [{result['status']}]: {state}")
            for blocker in result["blockers"]:
                print(f"  BLOCKER: {blocker}")
            for warning in result["warnings"]:
                print(f"  WARN: {warning}")

    if args.strict and any(result["blockers"] or result["warnings"] for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
