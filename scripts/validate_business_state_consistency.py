#!/usr/bin/env python3
"""Reject business-state transitions that are not backed by canonical proof."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "system_health" / "business_state_consistency.json"


from scripts.quote_proof import strict_quote_proofs
from scripts.gov_supplier_532_gate import candidate_manifest_path, evaluate_supplier_532, load_candidate_manifest
from scripts.gov_pricing_contract import validate_report as validate_gov_pricing_report
from scripts.compliance_matrix_contract import validate_matrix as validate_compliance_matrix
from scripts.codex_bid_pack_contract import verify_bid_pack_approval_ready
from scripts.codex_export_quote_pack_contract import verify_export_quote_pack_approval_ready


GOV_SUB_STATUS_OUTCOME_TYPES = {
    "SUBMITTED": {"SUBMITTED", "SUBMISSION_ACKNOWLEDGED"},
    "TECHNICAL_EVALUATION": {"TECHNICAL_EVALUATION_STARTED"},
    "TECHNICAL_RESULT": {"TECHNICAL_QUALIFIED", "TECHNICAL_DISQUALIFIED"},
    "FINANCIAL_BID_OPEN": {"FINANCIAL_BID_OPENED"},
    "L1_DECLARED": {"L1_DECLARED"},
    "LOI_RECEIVED": {"AWARD_DECLARED"},
    "AWARD_DECLARED": {"AWARD_DECLARED"},
    "WORK_ORDER": {"WORK_ORDER_RECEIVED"},
    "DELIVERY": {"DELIVERED"},
    "INVOICE_SUBMITTED": {"INVOICED"},
    "PAYMENT_PENDING": {"PAYMENT_DUE", "PAYMENT_DELAYED"},
    "PAYMENT_RECEIVED": {"PAYMENT_RECEIVED"},
}

EXPORT_SUB_STATUS_OUTCOME_TYPES = {
    "ORDER_RECEIVED": {"ORDER_RECEIVED"},
    "SAMPLE_SENT": {"SAMPLE_SENT"},
    "PRODUCTION": {"PRODUCTION_STARTED"},
    "INSPECTION": {"INSPECTION_COMPLETED"},
    "PACKING": {"PACKING_COMPLETED"},
    "DISPATCHED": {"DISPATCHED"},
    "CUSTOMS_CLEARED": {"CUSTOMS_CLEARED"},
    "SHIPPED": {"SHIPPED"},
    "DELIVERY": {"DELIVERED"},
    "INVOICE_SUBMITTED": {"INVOICED"},
    "PAYMENT_PENDING": {"PAYMENT_DUE", "PAYMENT_DELAYED"},
    "PAYMENT_RECEIVED": {"PAYMENT_RECEIVED"},
    "CLAIM_OR_RETURN": {"CLAIM_OR_RETURN"},
    "REPEAT_INQUIRY": {"REPEAT_INQUIRY"},
}

def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _verified_outcome(row: dict[str, Any]) -> bool:
    return (
        str(row.get("verification_status") or "").upper() == "VERIFIED"
        and bool(str(row.get("evidence_path") or "").strip())
        and len(str(row.get("evidence_sha256") or "").strip()) == 64
    )


def _receipt_state(row: dict[str, Any]) -> str:
    for key in ("external_effect_status", "status", "send_status", "submission_status", "outcome"):
        value = str(row.get(key) or "").upper().strip()
        if value:
            return value
    gmail_result = row.get("gmail_result") if isinstance(row.get("gmail_result"), dict) else {}
    if gmail_result.get("status"):
        return str(gmail_result["status"]).upper()
    return ""


def _verified_receipt(row: dict[str, Any]) -> bool:
    verification = str(row.get("verification_status") or "").upper()
    state = _receipt_state(row)
    gmail_result = row.get("gmail_result") if isinstance(row.get("gmail_result"), dict) else {}
    connector_proof = bool(
        row.get("external_message_id")
        or gmail_result.get("id")
        or gmail_result.get("threadId")
        or row.get("connector_verified") is True
    )
    return (verification == "VERIFIED" or connector_proof) and state in {
        "SENT",
        "SUBMITTED",
        "EXECUTED",
        "EXECUTED_AFTER_APPROVAL",
        "SUCCESS",
        "PASS",
    }


def _finding(case_id: str, code: str, detail: str, severity: str = "ERROR") -> dict[str, str]:
    return {"case_id": case_id, "code": code, "severity": severity, "detail": detail}


def gov_pricing_contract_errors(case_id: str) -> list[str]:
    path = PROJECT_ROOT / "outputs" / "case_reports" / case_id / f"pricing_{case_id}.json"
    if not path.is_file():
        return ["validated GOV pricing contract is missing"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"GOV pricing contract is invalid JSON: {exc}"]
    if not isinstance(value, dict):
        return ["GOV pricing contract must be a JSON object"]
    return validate_gov_pricing_report(value)


def gov_compliance_matrix_errors(case_id: str) -> list[str]:
    path = PROJECT_ROOT / "outputs" / "case_reports" / case_id / f"compliance_draft_{case_id}.json"
    if not path.is_file():
        return ["validated GOV compliance matrix is missing"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"GOV compliance matrix is invalid JSON: {exc}"]
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


def is_export_quote_action(approval: dict[str, Any]) -> bool:
    action = str(approval.get("action_approved") or approval.get("proposed_action") or "").casefold().replace(" ", "_")
    return any(marker in action for marker in ("export_quotation", "buyer_rfq_reply", "send_quotation"))


def validate_business_state(
    cases: list[dict[str, Any]],
    quotes: list[dict[str, Any]],
    approvals: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    execution_receipts: list[dict[str, Any]],
    suppliers: list[dict[str, Any]] | None = None,
    supplier_candidates_by_case: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    outcome_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    receipt_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    approval_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in outcomes:
        if row.get("case_id"):
            outcome_by_case[str(row["case_id"])].append(row)
    for row in execution_receipts:
        if row.get("case_id"):
            receipt_by_case[str(row["case_id"])].append(row)
    for row in approvals:
        if row.get("case_id"):
            approval_by_case[str(row["case_id"])].append(row)

    suppliers = suppliers or []
    supplier_candidates_by_case = supplier_candidates_by_case or {}
    for case in cases:
        case_id = str(case.get("case_id") or "")
        if not case_id:
            continue
        status = str(case.get("status") or "").upper()
        sub_status = str(case.get("execution_sub_status") or "").upper()
        verified_outcomes = [row for row in outcome_by_case[case_id] if _verified_outcome(row)]
        outcome_types = {str(row.get("outcome_type") or "").upper() for row in verified_outcomes}
        verified_receipts = [row for row in receipt_by_case[case_id] if _verified_receipt(row)]
        workflow = str(case.get("workflow_type") or "").upper()

        if workflow == "GOV":
            milestone_outcomes = GOV_SUB_STATUS_OUTCOME_TYPES.get(sub_status)
            if milestone_outcomes and not (outcome_types & milestone_outcomes):
                findings.append(
                    _finding(
                        case_id,
                        "GOV_EXECUTION_MILESTONE_NOT_READY",
                        f"execution_sub_status {sub_status} requires verified outcome evidence: "
                        + ", ".join(sorted(milestone_outcomes)),
                    )
                )

        if workflow == "EXPORT":
            milestone_outcomes = EXPORT_SUB_STATUS_OUTCOME_TYPES.get(sub_status)
            if milestone_outcomes and not (outcome_types & milestone_outcomes):
                findings.append(
                    _finding(
                        case_id,
                        "EXPORT_EXECUTION_MILESTONE_NOT_READY",
                        f"execution_sub_status {sub_status} requires verified outcome evidence: "
                        + ", ".join(sorted(milestone_outcomes)),
                    )
                )

        if str(case.get("corrigenda_status") or "").upper() == "CHANGED_REVIEW_REQUIRED" and status in {
            "PRICING_READY",
            "ARTIFACT_PRODUCTION",
            "APPROVAL_REQUIRED",
            "APPROVED",
        }:
            findings.append(
                _finding(
                    case_id,
                    "CORRIGENDUM_REVIEW_REQUIRED",
                    "A changed tender/corrigendum blocks downstream readiness until a new cited review is completed.",
                )
            )

        if status == "SENT_OR_SUBMITTED" and not verified_receipts:
            findings.append(
                _finding(case_id, "SENT_WITHOUT_RECEIPT", "SENT_OR_SUBMITTED requires a verified send/submission receipt.")
            )
        if status == "PRICING_READY" and len(strict_quote_proofs(case_id, quotes)) < 2:
            findings.append(
                _finding(
                    case_id,
                    "PRICING_WITHOUT_TWO_STRICT_QUOTES",
                    "PRICING_READY requires two unique supplier-specific quote proofs.",
                )
            )
        if workflow == "GOV" and status in {
            "PRICING_READY",
            "ARTIFACT_PRODUCTION",
            "APPROVAL_REQUIRED",
            "APPROVED",
        }:
            candidates = supplier_candidates_by_case.get(case_id)
            if candidates is None:
                try:
                    candidates = load_candidate_manifest(candidate_manifest_path(case_id), case_id=case_id)
                except ValueError:
                    candidates = []
            supplier_gate = evaluate_supplier_532(case, suppliers, quotes, candidates)
            if supplier_gate["status"] != "PASS":
                findings.append(
                    _finding(
                        case_id,
                        "GOV_SUPPLIER_532_NOT_READY",
                        "GOV pricing readiness requires a passing 5-3-2 supplier gate: "
                        + "; ".join(supplier_gate["blockers"]),
                    )
                )
            pricing_errors = gov_pricing_contract_errors(case_id)
            if pricing_errors:
                findings.append(
                    _finding(
                        case_id,
                        "GOV_PRICING_CONTRACT_NOT_READY",
                        "GOV pricing contract is not ready: " + "; ".join(pricing_errors),
                    )
                )
        export_quote_approval = any(
            is_export_quote_action(row)
            and str(row.get("approval_status") or "").upper() in {"PENDING", "APPROVED"}
            for row in approval_by_case[case_id]
        )
        if workflow == "EXPORT" and export_quote_approval:
            quote_pack_errors = export_quote_pack_errors(case_id)
            if quote_pack_errors:
                findings.append(
                    _finding(
                        case_id,
                        "EXPORT_QUOTE_PACK_NOT_READY",
                        "EXPORT quotation approval requires a current verified internal quote pack: " + "; ".join(quote_pack_errors),
                    )
                )
        if workflow == "GOV" and status in {
            "ARTIFACT_PRODUCTION",
            "APPROVAL_REQUIRED",
            "APPROVED",
        }:
            compliance_errors = gov_compliance_matrix_errors(case_id)
            if compliance_errors:
                findings.append(
                    _finding(
                        case_id,
                        "GOV_COMPLIANCE_MATRIX_NOT_READY",
                        "GOV compliance matrix is not ready: " + "; ".join(compliance_errors),
                    )
                )
            bid_pack_errors = gov_bid_pack_errors(case_id)
            if bid_pack_errors:
                findings.append(
                    _finding(
                        case_id,
                        "GOV_BID_PACK_NOT_READY",
                        "GOV approval readiness requires a current verified internal bid pack: " + "; ".join(bid_pack_errors),
                    )
                )
        if sub_status == "PAYMENT_RECEIVED" and "PAYMENT_RECEIVED" not in outcome_types:
            findings.append(
                _finding(
                    case_id,
                    "PAYMENT_WITHOUT_VERIFIED_EVIDENCE",
                    "PAYMENT_RECEIVED requires a verified outcome row with evidence hash.",
                )
            )
        if status in {"WON", "LOST"} and status not in outcome_types:
            findings.append(
                _finding(case_id, "CLOSED_WITHOUT_OUTCOME", f"{status} requires a matching verified case outcome.")
            )
        archived_after_action = status == "ARCHIVED" and (sub_status or verified_receipts)
        if archived_after_action and not verified_outcomes:
            findings.append(
                _finding(
                    case_id,
                    "CLOSED_WITHOUT_OUTCOME",
                    "An archived case with execution history requires verified outcome evidence.",
                )
            )

        states = {_receipt_state(row) for row in receipt_by_case[case_id]}
        sent_claim = bool(states & {"SENT", "SUBMITTED", "EXECUTED", "EXECUTED_AFTER_APPROVAL", "SUCCESS", "PASS"})
        not_sent_claim = bool(states & {"NOT_SENT", "SAFETY_HELD_NOT_SENT", "BLOCKED_NOT_SENT", "FAILED_NOT_SENT"})
        if sent_claim and not_sent_claim:
            findings.append(
                _finding(
                    case_id,
                    "CONFLICTING_EXECUTION_CLAIMS",
                    "Verified receipt records contain both sent/executed and not-sent claims.",
                )
            )
        if verified_receipts and any(
            str(row.get("approval_status") or "").upper() == "PENDING" for row in approval_by_case[case_id]
        ):
            findings.append(
                _finding(
                    case_id,
                    "PENDING_APPROVAL_AFTER_EXECUTION",
                    "A verified external receipt exists while a case approval remains PENDING.",
                )
            )

    findings.sort(key=lambda row: (row["case_id"], row["code"], row["detail"]))
    return {
        "schema_version": 1,
        "status": "PASS" if not findings else "FAIL",
        "case_count": len(cases),
        "finding_count": len(findings),
        "findings": findings,
        "external_actions_executed": False,
    }


def _extract_receipts(
    value: Any,
    source_path: str = "",
    inherited: dict[str, Any] | None = None,
    container_key: str = "",
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    context = dict(inherited or {})
    if isinstance(value, list):
        for item in value:
            rows.extend(_extract_receipts(item, source_path, context, container_key))
    elif isinstance(value, dict):
        for key in ("receipt_id", "connector", "account", "verified_by"):
            if value.get(key) not in (None, ""):
                context[key] = value[key]
        if container_key == "sent":
            context["external_effect_status"] = "SENT"
            if context.get("verified_by"):
                context["verification_status"] = "VERIFIED"
                context["connector_verified"] = True
        elif container_key == "blocked":
            context["external_effect_status"] = "NOT_SENT"
            context["verification_status"] = "VERIFIED"
        if value.get("case_id") and any(
            key in value
            for key in (
                "receipt_id",
                "status",
                "send_status",
                "submission_status",
                "external_effect_status",
                "external_message_id",
                "sent_at",
                "gmail_result",
            )
        ):
            row = context | dict(value)
            row.setdefault("receipt_path", source_path)
            rows.append(row)
        for key in ("receipts", "sent", "submissions", "results", "items"):
            if key in value:
                rows.extend(_extract_receipts(value[key], source_path, context, key))
        if "blocked" in value:
            rows.extend(_extract_receipts(value["blocked"], source_path, context, "blocked"))
    return rows


def load_execution_receipts(roots: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            continue
        paths = [root] if root.is_file() else sorted(root.rglob("*.json"))
        for path in paths:
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            rows.extend(_extract_receipts(value, str(path)))
    return rows


def load_supplier_candidates(cases: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    values: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        case_id = str(case.get("case_id") or "")
        if not case_id:
            continue
        try:
            values[case_id] = load_candidate_manifest(candidate_manifest_path(case_id), case_id=case_id)
        except ValueError:
            values[case_id] = []
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--allow-findings", action="store_true", help="Return success while still reporting findings")
    parser.add_argument("--public-template", action="store_true", help="Validate sanitized example registers only")
    args = parser.parse_args()
    data_root = PROJECT_ROOT / "data" / "examples" if args.public_template else PROJECT_ROOT / "data"
    suffix = ".example.csv" if args.public_template else ".csv"
    cases = load_csv(data_root / f"master_cases{suffix}")
    report = validate_business_state(
        cases,
        load_csv(data_root / f"quote_master{suffix}"),
        load_csv(data_root / f"approvals_receipts{suffix}"),
        load_csv(data_root / f"case_outcomes{suffix}"),
        []
        if args.public_template
        else load_execution_receipts(
            [
                PROJECT_ROOT / "receipts" / "executions",
                PROJECT_ROOT / "receipts" / "submissions",
                PROJECT_ROOT / "outputs" / "approved_execution_outbox",
            ]
        ),
        [] if args.public_template else load_csv(data_root / f"supplier_master{suffix}"),
        {} if args.public_template else load_supplier_candidates(cases),
    )
    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(output, 0o600)
    print(json.dumps({"status": report["status"], "findings": report["finding_count"], "output": str(output)}, indent=2))
    return 0 if report["status"] == "PASS" or args.allow_findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
