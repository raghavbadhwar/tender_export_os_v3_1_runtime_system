#!/usr/bin/env python3
"""Validate whether cases have the evidence needed for their current or next stage."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

try:
    from scripts.compliance_matrix_contract import validate_matrix as validate_compliance_matrix
    from scripts.codex_bid_pack_contract import verify_bid_pack_approval_ready
    from scripts.codex_export_quote_pack_contract import verify_export_quote_pack_approval_ready
    from scripts.gov_supplier_532_gate import candidate_manifest_path, evaluate_supplier_532, load_candidate_manifest
    from scripts.gov_pricing_contract import validate_report as validate_gov_pricing_report
    from scripts.quote_proof import strict_quote_proofs
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from compliance_matrix_contract import validate_matrix as validate_compliance_matrix  # type: ignore
    from codex_bid_pack_contract import verify_bid_pack_approval_ready  # type: ignore
    from codex_export_quote_pack_contract import verify_export_quote_pack_approval_ready  # type: ignore
    from gov_supplier_532_gate import candidate_manifest_path, evaluate_supplier_532, load_candidate_manifest  # type: ignore
    from gov_pricing_contract import validate_report as validate_gov_pricing_report  # type: ignore
    from quote_proof import strict_quote_proofs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def quote_proofs(case_id: str, quotes: list[dict]) -> list[dict]:
    return strict_quote_proofs(case_id, quotes)


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


def gov_pricing_contract_errors(case_id: str) -> list[str]:
    path = PROJECT_ROOT / "outputs" / "case_reports" / case_id / f"pricing_{case_id}.json"
    if not path.is_file():
        return [f"missing validated GOV pricing contract: {path.relative_to(PROJECT_ROOT)}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid GOV pricing contract JSON: {exc}"]
    if not isinstance(value, dict):
        return ["GOV pricing contract must be a JSON object"]
    return validate_gov_pricing_report(value)


def gov_compliance_matrix_errors(case_id: str) -> list[str]:
    path = PROJECT_ROOT / "outputs" / "case_reports" / case_id / f"compliance_draft_{case_id}.json"
    if not path.is_file():
        return [f"missing validated GOV compliance matrix: {path.relative_to(PROJECT_ROOT)}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid GOV compliance matrix JSON: {exc}"]
    if not isinstance(value, dict):
        return ["GOV compliance matrix must be a JSON object"]
    errors = validate_compliance_matrix(value)
    if value.get("matrix_status") != "DRAFT_READY":
        errors.append("GOV compliance matrix is BLOCKED")
    return errors


def gov_bid_pack_errors(case_id: str) -> list[str]:
    pack_root = PROJECT_ROOT / "outputs" / "bid_packs" / case_id
    report = verify_bid_pack_approval_ready(
        pack_root / "artifact_manifest.json",
        pack_root / "verification_receipt.json",
        expected_case_id=case_id,
    )
    return list(report.get("errors") or []) if report.get("status") != "PASS" else []


def export_quote_pack_errors(case_id: str) -> list[str]:
    pack_root = PROJECT_ROOT / "outputs" / "export_quote_packs" / case_id
    report = verify_export_quote_pack_approval_ready(
        pack_root / "artifact_manifest.json",
        pack_root / "verification_receipt.json",
        expected_case_id=case_id,
    )
    return list(report.get("errors") or []) if report.get("status") != "PASS" else []


def rfq_is_verified(rfq: dict) -> bool:
    return rfq.get("rfq_stage") in {"RFQ_VERIFIED", "READY_FOR_SUPPLIER_PROOF"} and rfq.get("evidence_status") == "RFQ_VERIFIED"


def evaluate_case(
    case: dict,
    quotes: list[dict],
    approvals: list[dict],
    rfqs: list[dict] | None = None,
    suppliers: list[dict] | None = None,
    supplier_candidates: list[dict] | None = None,
) -> dict:
    case_id = case.get("case_id", "")
    workflow = str(case.get("workflow_type", "")).upper()
    status = str(case.get("status", "")).upper()
    blockers: list[str] = []
    warnings: list[str] = []
    next_allowed = True
    rfqs = rfqs or []
    suppliers = suppliers or []
    if supplier_candidates is None and case_id:
        try:
            supplier_candidates = load_candidate_manifest(candidate_manifest_path(case_id), case_id=case_id)
        except ValueError as exc:
            supplier_candidates = []
            blockers.append(f"invalid supplier candidate manifest: {exc}")
    supplier_candidates = supplier_candidates or []

    check_required(case, ["case_id", "workflow_type", "opportunity_title", "status"], blockers)

    if case.get("corrigenda_status") == "CHANGED_REVIEW_REQUIRED":
        blockers.append("corrigenda review required; downstream readiness invalidated")

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

    if workflow == "GOV" and status in {"PRICING_READY", "ARTIFACT_PRODUCTION", "APPROVAL_REQUIRED", "APPROVED"}:
        supplier_gate = evaluate_supplier_532(case, suppliers, quotes, supplier_candidates)
        if supplier_gate["status"] != "PASS":
            blockers.extend(f"GOV supplier 5-3-2 gate: {item}" for item in supplier_gate["blockers"])
        blockers.extend(f"GOV pricing contract: {item}" for item in gov_pricing_contract_errors(case_id))
    if workflow == "GOV" and status in {"ARTIFACT_PRODUCTION", "APPROVAL_REQUIRED", "APPROVED"}:
        blockers.extend(f"GOV compliance matrix: {item}" for item in gov_compliance_matrix_errors(case_id))
        blockers.extend(f"GOV bid pack: {item}" for item in gov_bid_pack_errors(case_id))

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
        if status in {"ARTIFACT_PRODUCTION", "APPROVAL_REQUIRED", "APPROVED"} and rfq_is_verified(rfq):
            blockers.extend(f"EXPORT quote pack: {item}" for item in export_quote_pack_errors(case_id))

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
    suppliers = load_csv(DATA_DIR / "supplier_master.csv")
    approvals = load_csv(DATA_DIR / "approvals_receipts.csv")
    rfqs = load_csv(DATA_DIR / "rfq_master.csv")
    selected = [case for case in cases if args.all or case.get("case_id") == args.case_id]
    if not selected:
        print("No matching cases found.")
        return 1

    results = [evaluate_case(case, quotes, approvals, rfqs, suppliers) for case in selected]
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
