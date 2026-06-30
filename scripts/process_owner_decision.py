#!/usr/bin/env python3
"""Record an owner approval decision without executing any external action."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import shutil
from pathlib import Path

from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
APPROVALS = DATA_DIR / "approvals_receipts.csv"
CASES = DATA_DIR / "master_cases.csv"
RUN_LOG = DATA_DIR / "agent_run_log.csv"
RECEIPTS_DIR = PROJECT_ROOT / "receipts" / "owner_decisions"

FINAL_ACTIONS = {
    "send_export_quotation",
    "submit_tender_bid",
    "upload_tender_documents",
    "commit_final_price",
    "pay_emd",
    "pay_security_deposit",
    "pay_advance",
    "confirm_delivery_date",
    "accept_payment_terms",
}

INTERNAL_APPROVAL_ACTIONS = {
    "send_supplier_quote_request",
    "send_supplier_quote_requests",
    "request_supplier_quote",
    "request_supplier_quotes",
    "request_buyer_clarification",
}


def load_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, headers: list[str], rows: list[dict]) -> None:
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def find_approval(rows: list[dict], approval_id: str | None, case_id: str | None) -> dict | None:
    if approval_id:
        for row in rows:
            if row.get("approval_id") == approval_id:
                return row
    pending = [
        row for row in rows
        if row.get("case_id") == case_id and row.get("approval_status") == "PENDING"
    ]
    if len(pending) == 1:
        return pending[0]
    return None


def load_case(rows: list[dict], case_id: str) -> dict | None:
    for row in rows:
        if row.get("case_id") == case_id:
            return row
    return None


def next_case_status(current: str, action: str, decision: str) -> str:
    if decision == "ask_changes":
        return "CHANGES_REQUESTED" if current == "APPROVAL_REQUIRED" else current
    if decision == "reject":
        return "REJECTED" if current == "APPROVAL_REQUIRED" else current
    if decision == "approve" and action in FINAL_ACTIONS:
        return "APPROVED"
    if decision == "approve" and action in INTERNAL_APPROVAL_ACTIONS:
        return "SUPPLIER_SEARCH" if current in {"SUPPLIER_SEARCH", "APPROVAL_REQUIRED"} else current
    return current


def append_run_log(case_id: str, approval_id: str, decision: str, receipt_path: str, dry_run: bool) -> None:
    if dry_run:
        return
    headers, rows = load_csv(RUN_LOG)
    now = dt.datetime.now()
    row = {
        "run_id": f"RUN-{now.strftime('%Y%m%d%H%M%S')}",
        "run_date": now.date().isoformat(),
        "run_time": now.strftime("%H:%M:%S"),
        "agent_name": "approval_decision_processor",
        "trigger_type": "owner_command",
        "cases_processed": "1",
        "cases_created": "0",
        "cases_rejected": "1" if decision == "reject" else "0",
        "cases_updated": "1",
        "sources_checked": "0",
        "sources_failed": "0",
        "actions_taken": f"record_decision:{approval_id}:{decision}",
        "approval_cards_created": "0",
        "receipts_created": "1",
        "errors": "0",
        "warnings": "0",
        "runtime_seconds": "0",
        "status": "SUCCESS",
        "notes": f"Owner decision recorded for {case_id}; receipt={receipt_path}",
    }
    rows.append(row)
    write_csv(RUN_LOG, headers, rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Record an owner approval decision")
    parser.add_argument("--approval-id", help="Approval ID to decide")
    parser.add_argument("--case-id", help="Case ID with one pending approval")
    parser.add_argument("--decision", required=True, choices=["approve", "reject", "ask-changes"])
    parser.add_argument("--owner", required=True, help="Owner name or handle")
    parser.add_argument("--reason", default="", help="Rejection or approval note")
    parser.add_argument("--changes", default="", help="Requested changes for ask-changes")
    parser.add_argument("--dry-run", action="store_true", help="Print the update plan without writing files")
    args = parser.parse_args()

    if not args.approval_id and not args.case_id:
        print("Provide --approval-id or --case-id.")
        return 2
    if args.decision == "reject" and not args.reason:
        print("--reason is required for reject.")
        return 2
    if args.decision == "ask-changes" and not args.changes:
        print("--changes is required for ask-changes.")
        return 2

    approval_headers, approvals = load_csv(APPROVALS)
    case_headers, cases = load_csv(CASES)
    approval = find_approval(approvals, args.approval_id, args.case_id)
    if not approval:
        print("Could not find exactly one matching approval.")
        return 1
    case_id = approval.get("case_id", "")
    case = load_case(cases, case_id)
    if not case:
        print(f"Approval references missing case: {case_id}")
        return 1
    if approval.get("approval_status") != "PENDING":
        print(f"Approval is not pending: {approval.get('approval_status')}")
        return 1

    card_path = approval.get("approval_card_path", "")
    if card_path and not (PROJECT_ROOT / card_path).exists():
        print(f"Approval card is missing: {card_path}")
        return 1

    now = dt.datetime.now().replace(microsecond=0)
    receipt_id = f"ODR-{now.strftime('%Y%m%d%H%M%S')}-{approval.get('approval_id')}"
    receipt_path = RECEIPTS_DIR / f"{case_id}_{approval.get('approval_id')}_{now.strftime('%Y%m%d%H%M%S')}.json"
    decision_status = {
        "approve": "APPROVED",
        "reject": "REJECTED",
        "ask-changes": "CHANGES_REQUESTED",
    }[args.decision]
    action = approval.get("action_approved", "")
    new_case_status = next_case_status(case.get("status", ""), action, args.decision)
    external_effect = "PENDING_APPROVED_EXECUTION" if args.decision == "approve" else "NONE_DECISION_ONLY"

    approval_updates = {
        "approval_status": decision_status,
        "approved_by": args.owner if args.decision == "approve" else "",
        "approved_at": now.isoformat() if args.decision == "approve" else "",
        "rejection_reason": args.reason if args.decision == "reject" else "",
        "changes_requested": args.changes if args.decision == "ask-changes" else "",
        "receipt_id": receipt_id,
        "receipt_path": str(receipt_path.relative_to(PROJECT_ROOT)),
        "external_effect": external_effect,
    }
    case_updates = {
        "status": new_case_status,
        "approval_status": decision_status,
        "approved_by": args.owner if args.decision == "approve" else "",
        "approved_at": now.date().isoformat() if args.decision == "approve" else "",
        "updated_at": now.date().isoformat(),
    }

    receipt = {
        "receipt_id": receipt_id,
        "case_id": case_id,
        "approval_id": approval.get("approval_id"),
        "decision": args.decision,
        "decision_status": decision_status,
        "owner": args.owner,
        "decided_at": now.isoformat(),
        "action_approved": action,
        "case_status_before": case.get("status", ""),
        "case_status_after": new_case_status,
        "external_effect": external_effect,
        "reason": args.reason,
        "changes_requested": args.changes,
        "approval_card_path": card_path,
        "sources": ["data/approvals_receipts.csv", "data/master_cases.csv", card_path],
        "safety_note": "This receipt records an owner decision only. It does not send, submit, upload, pay, or commit externally.",
    }

    print(json.dumps({"approval_updates": approval_updates, "case_updates": case_updates, "receipt": receipt}, indent=2))
    if args.dry_run:
        print("Dry run only. No files changed.")
        return 0

    for field, value in approval_updates.items():
        if field in approval:
            approval[field] = value
    for field, value in case_updates.items():
        if field in case:
            case[field] = value

    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    write_csv(APPROVALS, approval_headers, approvals)
    write_csv(CASES, case_headers, cases)
    append_run_log(case_id, approval.get("approval_id", ""), args.decision, str(receipt_path.relative_to(PROJECT_ROOT)), False)
    append_event(
        "approval.owner_decision_recorded",
        "process_owner_decision",
        case_id=case_id,
        object_type="approval",
        object_id=approval.get("approval_id", ""),
        payload=approval_updates,
        citations=["data/approvals_receipts.csv", "data/master_cases.csv", str(receipt_path.relative_to(PROJECT_ROOT))],
    )
    append_event(
        "case.updated",
        "process_owner_decision",
        case_id=case_id,
        object_type="case",
        object_id=case_id,
        payload={"updates": case_updates},
        citations=["data/master_cases.csv", str(receipt_path.relative_to(PROJECT_ROOT))],
    )
    print(f"Wrote owner decision receipt: {receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
