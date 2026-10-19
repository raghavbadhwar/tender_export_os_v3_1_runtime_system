from __future__ import annotations

from pathlib import Path

from scripts.apply_learning_proposal import apply_rows, validate_application


def _proposal(tmp_path: Path, **overrides: object) -> dict[str, object]:
    rollback = tmp_path / "rollback.json"
    rollback.write_text("{}", encoding="utf-8")
    row: dict[str, object] = {
        "proposal_id": "LP-1",
        "proposal_target": "MODEL EXPORT_BUYER_REPLY_21D candidate-v1 hash-abc scope-model",
        "affected_workflows": "EXPORT",
        "current_version": "champion-v0",
        "proposed_version": "candidate-v1",
        "fixtures": "hash-abc",
        "status": "APPROVED",
        "approval_id": "APR-1",
        "rollback_artifact_path": str(rollback),
    }
    row.update(overrides)
    return row


def test_apply_learning_proposal_requires_approved_scope_and_passed_eval(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text("{}", encoding="utf-8")
    errors = validate_application(
        proposal=_proposal(tmp_path),
        evaluation_report={"proposal_id": "LP-1", "evaluation_status": "PASS", "rows": [{"status": "PASS"}, {"status": "PASS"}, {"status": "PASS"}]},
        approval_scope="scope-model",
        target="EXPORT_BUYER_REPLY_21D",
        version="candidate-v1",
        artifact_hash="hash-abc",
        checkpoint_path=str(checkpoint),
    )

    assert errors == []


def test_apply_learning_proposal_rejects_missing_checkpoint_or_wrong_status(tmp_path: Path) -> None:
    errors = validate_application(
        proposal=_proposal(tmp_path, status="PASS"),
        evaluation_report={"proposal_id": "LP-1", "evaluation_status": "FAIL"},
        approval_scope="scope-model",
        target="EXPORT_BUYER_REPLY_21D",
        version="candidate-v1",
        artifact_hash="hash-abc",
        checkpoint_path=str(tmp_path / "missing.json"),
    )

    assert any("status must be APPROVED" in error for error in errors)
    assert any("evaluation status must be PASS" in error for error in errors)
    assert any("checkpoint path must exist" in error for error in errors)


def test_apply_rows_marks_only_target_proposal_applied() -> None:
    rows = [{"proposal_id": "LP-1", "status": "APPROVED"}, {"proposal_id": "LP-2", "status": "APPROVED"}]

    updated = apply_rows(rows, "LP-1", "2099-01-01T00:00:00+00:00")

    assert updated[0]["status"] == "APPLIED"
    assert updated[0]["applied_at"] == "2099-01-01T00:00:00+00:00"
    assert updated[1]["status"] == "APPROVED"
