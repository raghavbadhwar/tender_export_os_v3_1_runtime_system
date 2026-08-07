#!/usr/bin/env python3
"""Record owner-operated EXPORT order-to-cash evidence without external execution."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event, build_event
from scripts.record_case_outcome import append_outcome, load_csv, validate_evidence, validate_outcome


CASES_PATH = PROJECT_ROOT / "data" / "master_cases.csv"
OUTCOMES_PATH = PROJECT_ROOT / "data" / "case_outcomes.csv"
APPROVALS_PATH = PROJECT_ROOT / "data" / "approvals_receipts.csv"
EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"
RECEIPTS_DIR = PROJECT_ROOT / "receipts" / "executions"
RUN_LOG_PATH = PROJECT_ROOT / "data" / "agent_run_log.csv"
SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "export_execution_milestone.schema.json"
ORDER_APPROVAL_TOKENS = ("quote", "quotation", "buyer_rfq_reply", "export")
ORDERED_OR_EXECUTING_STATUSES = {"SENT_OR_SUBMITTED", "FOLLOW_UP", "WON"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")


def stable_id(prefix: str, case_id: str, milestone_type: str, occurred_at: str, evidence_sha256: str) -> str:
    fingerprint = hashlib.sha256(f"{case_id}|{milestone_type}|{occurred_at}|{evidence_sha256}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{slug(case_id)}-{slug(milestone_type)}-{fingerprint}"


def load_contract(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("milestones"), dict):
        raise ValueError(f"Invalid EXPORT execution milestone contract: {path}")
    return value


def milestone_config(milestone_type: str, contract: dict[str, Any] | None = None) -> dict[str, Any]:
    value = (contract or load_contract())["milestones"].get(milestone_type)
    if not isinstance(value, dict):
        raise ValueError(f"Unsupported EXPORT milestone_type: {milestone_type!r}")
    return value


def outcome_id_for(milestone: dict[str, Any]) -> str:
    return stable_id(
        "OUT",
        clean_text(milestone["case_id"]),
        clean_text(milestone["outcome_type"]),
        clean_text(milestone["occurred_at"]),
        clean_text(milestone["evidence_sha256"]),
    )


def build_outcome_row(milestone: dict[str, Any]) -> dict[str, str]:
    return {
        "outcome_id": clean_text(milestone["outcome_id"]),
        "case_id": clean_text(milestone["case_id"]),
        "workflow_type": "EXPORT",
        "outcome_type": clean_text(milestone["outcome_type"]),
        "outcome_value": clean_text(milestone.get("outcome_value")),
        "occurred_at": clean_text(milestone["occurred_at"]),
        "evidence_path": clean_text(milestone["evidence_path"]),
        "evidence_sha256": clean_text(milestone["evidence_sha256"]),
        "verification_status": clean_text(milestone["verification_status"]),
        "recorded_by": clean_text(milestone["recorded_by"]),
        "recorded_at": clean_text(milestone["recorded_at"]),
        "supersedes_outcome_id": clean_text(milestone.get("supersedes_outcome_id")),
        "notes": clean_text(milestone.get("notes")),
    }


def ranks_by_sub_status(contract: dict[str, Any]) -> dict[str, int]:
    ranks = {"": 0}
    for config in contract["milestones"].values():
        ranks[clean_text(config["execution_sub_status"])] = int(config["rank"])
    return ranks


def verify_order_approval(approval_reference: str, *, case_id: str, approvals: list[dict[str, Any]]) -> None:
    if not approval_reference:
        raise ValueError("ORDER_RECEIVED requires approval_reference for the buyer-facing quotation or RFQ reply")
    approval = next(
        (
            row
            for row in approvals
            if clean_text(row.get("approval_id")) == approval_reference and clean_text(row.get("case_id")) == case_id
        ),
        None,
    )
    if approval is None:
        raise ValueError("approval_reference does not match a case approval")
    if clean_text(approval.get("approval_status")).upper() != "APPROVED":
        raise ValueError("ORDER_RECEIVED requires an APPROVED owner quotation/RFQ-reply receipt")
    action = clean_text(approval.get("action_approved") or approval.get("proposed_action")).casefold()
    if not any(token in action for token in ORDER_APPROVAL_TOKENS):
        raise ValueError("approval_reference is not scoped to an export quotation or buyer RFQ reply")


def validate_milestone(
    milestone: dict[str, Any],
    *,
    cases: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    approvals: list[dict[str, Any]],
) -> dict[str, Any]:
    contract = load_contract()
    missing = [field for field in contract["required_fields"] if milestone.get(field) in (None, "")]
    if missing:
        raise ValueError("required milestone fields are blank: " + ", ".join(missing))
    if milestone.get("external_actions_executed") is not False:
        raise ValueError("external_actions_executed must be false; this script only records evidence")
    case_id = clean_text(milestone["case_id"])
    case = next((row for row in cases if clean_text(row.get("case_id")) == case_id), None)
    if case is None:
        raise ValueError(f"unknown case_id: {case_id}")
    if clean_text(case.get("workflow_type")).upper() != "EXPORT" or clean_text(milestone.get("workflow_type")).upper() != "EXPORT":
        raise ValueError("EXPORT execution milestones require a canonical EXPORT case")
    milestone_type = clean_text(milestone["milestone_type"])
    config = milestone_config(milestone_type, contract)
    if clean_text(milestone.get("outcome_type")) != clean_text(config["outcome_type"]):
        raise ValueError("outcome_type does not match the configured milestone")
    if clean_text(milestone.get("execution_sub_status")) != clean_text(config["execution_sub_status"]):
        raise ValueError("execution_sub_status does not match the configured milestone")
    verification_status = clean_text(milestone["verification_status"])
    if verification_status not in set(contract["verification_statuses"]):
        raise ValueError("verification_status is not allowed for EXPORT milestone evidence")
    evidence = validate_evidence(clean_text(milestone["evidence_path"]), clean_text(milestone["evidence_sha256"]))

    if verification_status == "VERIFIED" and milestone_type == "ORDER_RECEIVED":
        verify_order_approval(clean_text(milestone.get("approval_reference")), case_id=case_id, approvals=approvals)
        if clean_text(case.get("status")).upper() not in ORDERED_OR_EXECUTING_STATUSES:
            raise ValueError("ORDER_RECEIVED requires a case already in sent/follow-up/won execution state")

    verified_types = {
        clean_text(row.get("outcome_type"))
        for row in outcomes
        if clean_text(row.get("case_id")) == case_id and clean_text(row.get("verification_status")) == "VERIFIED"
    }
    if verification_status == "VERIFIED" and int(config["rank"]) > 10 and "ORDER_RECEIVED" not in verified_types:
        raise ValueError("verified export execution milestones after order receipt require verified ORDER_RECEIVED evidence")
    current_rank = ranks_by_sub_status(contract).get(clean_text(case.get("execution_sub_status")), 0)
    if verification_status == "VERIFIED" and int(config["rank"]) < current_rank:
        raise ValueError("verified milestone would move execution_sub_status backwards")

    outcome = build_outcome_row(milestone)
    validate_outcome(outcome, cases=cases, existing=outcomes)
    return {"ok": True, "case": case, "config": config, "evidence": evidence, "outcome": outcome, "will_update_master": verification_status == "VERIFIED"}


def build_milestone_event(milestone: dict[str, Any], *, receipt_path: Path, actor: str) -> dict[str, Any]:
    return build_event(
        "execution.milestone_recorded",
        actor,
        case_id=clean_text(milestone["case_id"]),
        object_type="execution",
        object_id=clean_text(milestone["milestone_id"]),
        source="owner_operated_export_evidence",
        payload={
            "milestone_id": clean_text(milestone["milestone_id"]),
            "milestone_type": clean_text(milestone["milestone_type"]),
            "execution_sub_status": clean_text(milestone["execution_sub_status"]),
            "receipt_path": str(receipt_path),
            "evidence_sha256": clean_text(milestone["evidence_sha256"]),
            "verification_status": clean_text(milestone["verification_status"]),
        },
        citations=[clean_text(milestone["evidence_path"]), str(receipt_path)],
        idempotency_key=f"export-execution-milestone:{milestone['milestone_id']}",
    )


def write_master_projection(master_cases_path: Path, milestone: dict[str, Any]) -> None:
    with master_cases_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    case_id = clean_text(milestone["case_id"])
    found = False
    for row in rows:
        if clean_text(row.get("case_id")) != case_id:
            continue
        found = True
        row["execution_sub_status"] = clean_text(milestone["execution_sub_status"])
        row["updated_at"] = clean_text(milestone["recorded_at"])[:10]
    if not found:
        raise ValueError(f"unknown case_id in projection: {case_id}")
    temporary = master_cases_path.with_suffix(master_cases_path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.chmod(temporary, 0o600)
    os.replace(temporary, master_cases_path)


def write_receipt(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def append_run_log(path: Path, milestone: dict[str, Any], *, receipt_path: Path, master_updated: bool) -> None:
    fields = [
        "run_id", "run_date", "run_time", "agent_name", "trigger_type", "cases_processed", "cases_created",
        "cases_rejected", "cases_updated", "sources_checked", "sources_failed", "actions_taken", "approval_cards_created",
        "receipts_created", "errors", "warnings", "runtime_seconds", "status", "notes",
    ]
    existing_fields: list[str] | None = None
    if path.is_file():
        with path.open("r", newline="", encoding="utf-8") as handle:
            existing_fields = csv.DictReader(handle).fieldnames
    now = dt.datetime.now(dt.timezone.utc)
    row = {
        "run_id": f"RUN-EXPORT-MILESTONE-{now.strftime('%Y%m%d%H%M%S')}",
        "run_date": now.date().isoformat(), "run_time": now.strftime("%H:%M:%S"),
        "agent_name": "execution_tracker_agent", "trigger_type": "owner_operated_evidence_ingestion",
        "cases_processed": "1", "cases_created": "0", "cases_rejected": "0", "cases_updated": "1" if master_updated else "0",
        "sources_checked": "0", "sources_failed": "0", "actions_taken": f"export_milestone:{milestone['milestone_type']}",
        "approval_cards_created": "0", "receipts_created": "1", "errors": "0",
        "warnings": "0" if milestone["verification_status"] == "VERIFIED" else "1", "runtime_seconds": "0", "status": "SUCCESS",
        "notes": f"{milestone['case_id']} {milestone['milestone_type']} evidence recorded: {receipt_path}",
    }
    fields = existing_fields or fields
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if existing_fields is None:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})


def record_milestone(
    milestone: dict[str, Any],
    *,
    master_cases_path: Path = CASES_PATH,
    outcomes_path: Path = OUTCOMES_PATH,
    approvals_path: Path = APPROVALS_PATH,
    events_path: Path = EVENTS_PATH,
    receipts_dir: Path = RECEIPTS_DIR,
    run_log_path: Path | None = None,
    actor: str,
) -> dict[str, Any]:
    cases = load_csv(master_cases_path)
    outcomes = load_csv(outcomes_path)
    validation = validate_milestone(milestone, cases=cases, outcomes=outcomes, approvals=load_csv(approvals_path))
    receipt_path = receipts_dir / f"{milestone['milestone_id']}.json"
    event = append_event(
        "execution.milestone_recorded", actor, case_id=clean_text(milestone["case_id"]), object_type="execution",
        object_id=clean_text(milestone["milestone_id"]), source="owner_operated_export_evidence",
        payload=build_milestone_event(milestone, receipt_path=receipt_path, actor=actor)["payload"],
        citations=[clean_text(milestone["evidence_path"]), str(receipt_path)],
        idempotency_key=f"export-execution-milestone:{milestone['milestone_id']}", events_file=events_path,
    )
    outcome_event = append_outcome(validation["outcome"], outcomes_path=outcomes_path, events_path=events_path, actor=actor)
    case_event: dict[str, Any] | None = None
    if validation["will_update_master"]:
        case_event = append_event(
            "case.updated", actor, case_id=clean_text(milestone["case_id"]), object_type="case", object_id=clean_text(milestone["case_id"]),
            source="owner_operated_export_evidence",
            payload={"updates": {"execution_sub_status": clean_text(milestone["execution_sub_status"]), "updated_at": clean_text(milestone["recorded_at"])[:10]}},
            citations=[clean_text(milestone["evidence_path"])], idempotency_key=f"export-execution-case-update:{milestone['milestone_id']}", events_file=events_path,
        )
        write_master_projection(master_cases_path, milestone)
    receipt = {
        "schema_version": "export_execution_milestone_receipt.v1", "milestone": milestone, "outcome": validation["outcome"],
        "validation": {"status": "PASS", "will_update_master": validation["will_update_master"]},
        "canonical_event_ids": {"milestone": event["event_id"], "outcome": outcome_event["event_id"], "case_update": case_event["event_id"] if case_event else ""},
        "external_actions_executed": False,
    }
    write_receipt(receipt_path, receipt)
    if run_log_path is not None:
        append_run_log(run_log_path, milestone, receipt_path=receipt_path, master_updated=validation["will_update_master"])
    return {"receipt_path": str(receipt_path), "validation": validation, "receipt": receipt}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--milestone-type", required=True)
    parser.add_argument("--occurred-at", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--evidence-sha256", default="")
    parser.add_argument("--verification-status", required=True)
    parser.add_argument("--recorded-by", required=True)
    parser.add_argument("--approval-reference", default="")
    parser.add_argument("--outcome-value", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--milestone-id", default="")
    parser.add_argument("--outcome-id", default="")
    parser.add_argument("--recorded-at", default="")
    parser.add_argument("--supersedes-outcome-id", default="")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    contract = load_contract()
    config = milestone_config(args.milestone_type, contract)
    proof = validate_evidence(args.evidence, args.evidence_sha256)
    provisional = {"case_id": args.case_id, "outcome_type": config["outcome_type"], "occurred_at": args.occurred_at, "evidence_sha256": proof["sha256"]}
    milestone = {
        "schema_version": contract["schema_version"],
        "milestone_id": args.milestone_id or stable_id("MILESTONE", args.case_id, args.milestone_type, args.occurred_at, proof["sha256"]),
        "case_id": args.case_id, "workflow_type": "EXPORT", "milestone_type": args.milestone_type,
        "outcome_id": args.outcome_id or outcome_id_for(provisional), "outcome_type": config["outcome_type"],
        "execution_sub_status": config["execution_sub_status"],
        "outcome_value": args.outcome_value or f"Owner-operated EXPORT {args.milestone_type.replace('_', ' ').lower()} evidence recorded.",
        "occurred_at": args.occurred_at, "evidence_path": proof["path"], "evidence_sha256": proof["sha256"],
        "verification_status": args.verification_status, "recorded_by": args.recorded_by, "recorded_at": args.recorded_at or now_iso(),
        "approval_reference": args.approval_reference, "supersedes_outcome_id": args.supersedes_outcome_id, "notes": args.notes,
        "external_actions_executed": False,
    }
    cases = load_csv(CASES_PATH)
    outcomes = load_csv(OUTCOMES_PATH)
    validation = validate_milestone(milestone, cases=cases, outcomes=outcomes, approvals=load_csv(APPROVALS_PATH))
    receipt_path = RECEIPTS_DIR / f"{milestone['milestone_id']}.json"
    payload: dict[str, Any] = {
        "status": "PASS", "mode": "write" if args.write else "dry_run", "milestone": milestone,
        "validation": {"will_update_master": validation["will_update_master"], "evidence": validation["evidence"]},
        "milestone_event_preview": build_milestone_event(milestone, receipt_path=receipt_path, actor=args.recorded_by),
        "canonical_events_appended": False, "master_projection_updated": False, "external_actions_executed": False,
    }
    if args.write:
        result = record_milestone(milestone, actor=args.recorded_by, run_log_path=RUN_LOG_PATH)
        payload.update({"canonical_events_appended": True, "master_projection_updated": result["validation"]["will_update_master"], "receipt_path": result["receipt_path"]})
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
