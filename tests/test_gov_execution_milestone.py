from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts.record_gov_execution_milestone import (
    milestone_config,
    outcome_id_for,
    record_milestone,
    stable_id,
    validate_milestone,
)


CASE_ID = "GOV-20990101-001"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def case_row(sub_status: str = "") -> dict[str, str]:
    return {
        "case_id": CASE_ID,
        "workflow_type": "GOV",
        "status": "APPROVED",
        "execution_sub_status": sub_status,
        "submitted_at": "",
        "updated_at": "2099-01-01",
    }


def approved_submission() -> dict[str, str]:
    return {
        "approval_id": "APR-GOV-SUBMIT-001",
        "case_id": CASE_ID,
        "approval_status": "APPROVED",
        "action_approved": "submit_tender_bid",
    }


def milestone(evidence: Path, milestone_type: str, *, verification_status: str = "VERIFIED") -> dict[str, object]:
    config = milestone_config(milestone_type)
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    value: dict[str, object] = {
        "schema_version": "gov_execution_milestone.v1",
        "milestone_id": stable_id("MILESTONE", CASE_ID, milestone_type, "2099-01-02T10:00:00+00:00", digest),
        "case_id": CASE_ID,
        "workflow_type": "GOV",
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
        "approval_reference": "APR-GOV-SUBMIT-001" if milestone_type == "SUBMISSION_ACKNOWLEDGED" else "",
        "portal_reference": "PORTAL-ACK-001" if milestone_type == "SUBMISSION_ACKNOWLEDGED" else "",
        "supersedes_outcome_id": "",
        "notes": "Fixture evidence only.",
        "external_actions_executed": False,
    }
    value["outcome_id"] = outcome_id_for(value)
    return value


def test_submission_evidence_requires_approved_submission_scope(tmp_path: Path) -> None:
    evidence = tmp_path / "portal_acknowledgement.txt"
    evidence.write_text("Portal acknowledgement", encoding="utf-8")
    value = milestone(evidence, "SUBMISSION_ACKNOWLEDGED")

    result = validate_milestone(value, cases=[case_row()], outcomes=[], approvals=[approved_submission()])

    assert result["will_update_master"] is True
    assert result["outcome"]["outcome_type"] == "SUBMISSION_ACKNOWLEDGED"
    with pytest.raises(ValueError, match="approval_reference"):
        validate_milestone(value | {"approval_reference": ""}, cases=[case_row()], outcomes=[], approvals=[])


def test_evidence_present_is_logged_but_does_not_move_execution_tracker(tmp_path: Path) -> None:
    evidence = tmp_path / "technical_notice.txt"
    evidence.write_text("Technical evaluation notice", encoding="utf-8")
    value = milestone(evidence, "TECHNICAL_EVALUATION_STARTED", verification_status="EVIDENCE_PRESENT")

    result = validate_milestone(value, cases=[case_row()], outcomes=[], approvals=[])

    assert result["will_update_master"] is False


def test_conflicting_verified_technical_result_is_rejected(tmp_path: Path) -> None:
    evidence = tmp_path / "technical_result.txt"
    evidence.write_text("Technical result", encoding="utf-8")
    value = milestone(evidence, "TECHNICAL_QUALIFIED")

    with pytest.raises(ValueError, match="conflicts"):
        validate_milestone(
            value,
            cases=[case_row("TECHNICAL_RESULT")],
            outcomes=[{"case_id": CASE_ID, "outcome_type": "TECHNICAL_DISQUALIFIED", "verification_status": "VERIFIED"}],
            approvals=[],
        )


def test_write_records_events_outcome_receipt_and_verified_projection_only(tmp_path: Path) -> None:
    evidence = tmp_path / "portal_acknowledgement.txt"
    evidence.write_text("Portal acknowledgement", encoding="utf-8")
    master = tmp_path / "master_cases.csv"
    outcomes = tmp_path / "case_outcomes.csv"
    approvals = tmp_path / "approvals_receipts.csv"
    events = tmp_path / "events.jsonl"
    receipts = tmp_path / "receipts"
    run_log = tmp_path / "agent_run_log.csv"
    write_csv(master, list(case_row().keys()), [case_row()])
    write_csv(approvals, list(approved_submission().keys()), [approved_submission()])
    value = milestone(evidence, "SUBMISSION_ACKNOWLEDGED")

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
    assert outcome_rows[0]["outcome_type"] == "SUBMISSION_ACKNOWLEDGED"
    assert master_rows[0]["execution_sub_status"] == "SUBMITTED"
    assert event_types == ["execution.milestone_recorded", "case.outcome_recorded", "case.updated"]
    assert "owner_operated_evidence_ingestion" in run_log.read_text(encoding="utf-8")
