from __future__ import annotations

from pathlib import Path

from scripts.verify_agentic_task_completion import validate_completion


def test_completion_verifier_requires_evidence_artifact_and_validator(tmp_path: Path) -> None:
    artifact = tmp_path / "review.json"
    validator = tmp_path / "validator.json"
    artifact.write_text("{}", encoding="utf-8")
    validator.write_text('{"status":"PASS"}', encoding="utf-8")

    result = validate_completion(
        {
            "status": "DONE",
            "case_id": "GOV-001",
            "evidence": [{"path": "packet.json", "sha256": "abc"}],
            "gate": "internal_review",
            "artifact_paths": [str(artifact)],
            "validator_receipt_path": str(validator),
            "stop_reason": "completed_internal_review",
            "retry_method": "requeue_with_fresh_packet",
            "smallest_safe_next_action": "owner_review",
            "approval_required": False,
            "external_actions_executed": False,
        }
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_completion_verifier_rejects_external_effect_and_missing_paths(tmp_path: Path) -> None:
    result = validate_completion(
        {
            "status": "DONE",
            "case_id": "GOV-001",
            "evidence": [],
            "gate": "internal_review",
            "artifact_paths": [str(tmp_path / "missing.json")],
            "validator_receipt_path": str(tmp_path / "missing-validator.json"),
            "stop_reason": "completed",
            "retry_method": "none",
            "smallest_safe_next_action": "owner_review",
            "approval_required": False,
            "external_actions_executed": True,
        }
    )

    assert result["valid"] is False
    assert "external_actions_executed must be false" in result["errors"]
    assert any("artifact" in error for error in result["errors"])
    assert any("validator" in error for error in result["errors"])
