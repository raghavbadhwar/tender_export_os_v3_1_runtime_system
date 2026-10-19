from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts.record_export_execution_milestone import (
    milestone_config,
    outcome_id_for,
    record_milestone,
    stable_id,
    validate_milestone,
)


CASE_ID = "EXP-20990101-001"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def case_row(sub_status: str = "", status: str = "SENT_OR_SUBMITTED") -> dict[str, str]:
    return {
        "case_id": CASE_ID,
        "workflow_type": "EXPORT",
        "status": status,
        "execution_sub_status": sub_status,
        "updated_at": "2099-01-01",
    }


def approved_quote() -> dict[str, str]:
    return {
        "approval_id": "APR-EXP-QUOTE-001",
        "case_id": CASE_ID,
        "approval_status": "APPROVED",
        "action_approved": "send_export_quotation",
    }


def milestone(evidence: Path, milestone_type: str, *, verification_status: str = "VERIFIED") -> dict[str, object]:
    config = milestone_config(milestone_type)
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    value: dict[str, object] = {
        "schema_version": "export_execution_milestone.v1",
        "milestone_id": stable_id("MILESTONE", CASE_ID, milestone_type, "2099-01-02T10:00:00+00:00", digest),
        "case_id": CASE_ID,
        "workflow_type": "EXPORT",
        "milestone_type": milestone_type,
        "outcome_type": config["outcome_type"],
        "execution_sub_status": config["execution_sub_status"],
        "outcome_value": f"Verified {milestone_type}",
        "occurred_at": "2099-01-02T10:00:00+00:00",
        "evidence_path": str(evidence),
        "evidence_sha256": digest,
        "verification_status": verification_status,
        "recorded_by": "owner",
        "recorded_at": "2099-01-02T11:00:00+00:00",
        "approval_reference": "APR-EXP-QUOTE-001" if milestone_type == "ORDER_RECEIVED" else "",
        "supersedes_outcome_id": "",
        "notes": "Fixture evidence only.",
        "external_actions_executed": False,
    }
    value["outcome_id"] = outcome_id_for(value)
    return value


def test_verified_order_requires_a_real_approved_quote_scope(tmp_path: Path) -> None:
    evidence = tmp_path / "purchase_order.txt"
    evidence.write_text("Buyer purchase order", encoding="utf-8")
    value = milestone(evidence, "ORDER_RECEIVED")

    result = validate_milestone(value, cases=[case_row()], outcomes=[], approvals=[approved_quote()])

    assert result["will_update_master"] is True
    assert result["outcome"]["outcome_type"] == "ORDER_RECEIVED"
    with pytest.raises(ValueError, match="approval_reference"):
        validate_milestone(value | {"approval_reference": ""}, cases=[case_row()], outcomes=[], approvals=[])


def test_evidence_present_is_stored_but_does_not_change_export_execution_state(tmp_path: Path) -> None:
    evidence = tmp_path / "buyer_claim.txt"
    evidence.write_text("Buyer claim notice", encoding="utf-8")
    value = milestone(evidence, "CLAIM_OR_RETURN", verification_status="EVIDENCE_PRESENT")

    result = validate_milestone(value, cases=[case_row("DELIVERY")], outcomes=[], approvals=[])

    assert result["will_update_master"] is False


def test_verified_post_order_milestone_requires_verified_order_evidence(tmp_path: Path) -> None:
    evidence = tmp_path / "production_notice.txt"
    evidence.write_text("Production started", encoding="utf-8")
    value = milestone(evidence, "PRODUCTION_STARTED")

    with pytest.raises(ValueError, match="ORDER_RECEIVED"):
        validate_milestone(value, cases=[case_row()], outcomes=[], approvals=[])


def test_write_records_outcome_receipt_and_verified_projection_only(tmp_path: Path) -> None:
    evidence = tmp_path / "purchase_order.txt"
    evidence.write_text("Buyer purchase order", encoding="utf-8")
    master = tmp_path / "master_cases.csv"
    outcomes = tmp_path / "case_outcomes.csv"
    approvals = tmp_path / "approvals_receipts.csv"
    events = tmp_path / "events.jsonl"
    receipts = tmp_path / "receipts"
    run_log = tmp_path / "agent_run_log.csv"
    write_csv(master, list(case_row().keys()), [case_row()])
    write_csv(approvals, list(approved_quote().keys()), [approved_quote()])
    value = milestone(evidence, "ORDER_RECEIVED")

    result = record_milestone(
        value,
        master_cases_path=master,
        outcomes_path=outcomes,
        approvals_path=approvals,
        events_path=events,
        receipts_dir=receipts,
        run_log_path=run_log,
        actor="pytest",
    )

    receipt = json.loads(Path(result["receipt_path"]).read_text(encoding="utf-8"))
    with outcomes.open(newline="", encoding="utf-8") as handle:
        outcome_rows = list(csv.DictReader(handle))
    with master.open(newline="", encoding="utf-8") as handle:
        master_rows = list(csv.DictReader(handle))
    event_types = [json.loads(line)["event_type"] for line in events.read_text(encoding="utf-8").splitlines()]
    assert receipt["external_actions_executed"] is False
    assert outcome_rows[0]["outcome_type"] == "ORDER_RECEIVED"
    assert master_rows[0]["execution_sub_status"] == "ORDER_RECEIVED"
    assert event_types == ["execution.milestone_recorded", "case.outcome_recorded", "case.updated"]
    assert "owner_operated_evidence_ingestion" in run_log.read_text(encoding="utf-8")
