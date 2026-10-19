from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

from scripts.apply_learning_proposal import build_promotion_receipt, validate_promotion_receipt


SCHEMA = json.loads(Path("config/schemas/learning_promotion_receipt.schema.json").read_text(encoding="utf-8"))


def test_promotion_receipt_is_typed_and_external_effect_free(tmp_path: Path) -> None:
    evaluation = tmp_path / "evaluation.json"
    checkpoint = tmp_path / "checkpoint.json"
    rollback = tmp_path / "rollback.json"
    for path in (evaluation, checkpoint, rollback):
        path.write_text("{}", encoding="utf-8")
    receipt = build_promotion_receipt(
        proposal={
            "proposal_id": "LP-RECEIPT-1",
            "proposal_type": "skill",
            "proposal_target": "skill:example",
            "proposed_version": "v2",
            "approval_id": "APR-1",
            "rollback_artifact_path": str(rollback),
        },
        evaluation_report_path=str(evaluation),
        checkpoint_path=str(checkpoint),
        artifact_hash=hashlib.sha256(b"candidate").hexdigest(),
        event_id="EVT-1",
        promoted_at="2026-07-14T00:00:00+00:00",
    )
    jsonschema.validate(receipt, SCHEMA)
    assert validate_promotion_receipt(receipt) == []
    assert receipt["external_actions_executed"] is False
    assert receipt["raw_content_persisted"] is False


def test_promotion_receipt_rejects_missing_approval_and_rollback() -> None:
    errors = validate_promotion_receipt(
        {
            "schema_version": "learning_promotion_receipt.v1",
            "proposal_id": "LP-1",
            "approval_id": "",
            "rollback_artifact_path": "missing.json",
            "external_actions_executed": True,
        }
    )
    assert any("approval_id" in error for error in errors)
    assert any("rollback" in error for error in errors)
    assert any("external_actions_executed" in error for error in errors)


def test_application_requires_three_passing_evaluation_rows(tmp_path: Path) -> None:
    from scripts.apply_learning_proposal import validate_application

    checkpoint = tmp_path / "checkpoint.json"
    rollback = tmp_path / "rollback.json"
    checkpoint.write_text("{}", encoding="utf-8")
    rollback.write_text("{}", encoding="utf-8")
    proposal = {
        "proposal_id": "LP-1",
        "proposal_target": "skill example scope",
        "affected_workflows": "EXPORT",
        "current_version": "v1",
        "proposed_version": "v2",
        "fixtures": "fixture-hash",
        "status": "APPROVED",
        "approval_id": "APR-1",
        "rollback_artifact_path": str(rollback),
    }
    errors = validate_application(
        proposal=proposal,
        evaluation_report={
            "proposal_id": "LP-1",
            "evaluation_status": "PASS",
            "rows": [{"status": "PASS"}, {"status": "PASS"}],
        },
        approval_scope="scope",
        target="skill",
        version="v2",
        artifact_hash="fixture-hash",
        checkpoint_path=str(checkpoint),
    )
    assert any("three passing" in error for error in errors)
