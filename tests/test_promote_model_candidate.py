from __future__ import annotations

from scripts.promote_model_candidate import promote_rows, validate_promotion


def _candidate(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "model_id": "CAND-1",
        "target_id": "EXPORT_BUYER_REPLY_21D",
        "workflow_type": "EXPORT",
        "horizon_days": "21",
        "model_version": "candidate-v1",
        "feature_schema_hash": "a" * 64,
        "mature_sample_count": "100",
        "positive_class_count": "20",
        "negative_class_count": "80",
        "primary_metric": "brier_score",
        "metric_value": "0.20",
        "brier_score": "0.20",
        "log_loss": "0.50",
        "calibration_error": "0.05",
        "calibration_status": "CALIBRATED",
        "status": "CANDIDATE",
        "artifact_path": "outputs/models/cand.json",
        "approval_id": "",
        "rollback_version": "champion-v0",
        "registered_at": "2099-01-01T00:00:00+00:00",
    }
    row.update(overrides)
    return row


def _proposal(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "proposal_id": "LP-1",
        "proposal_type": "MODEL",
        "proposal_target": "CAND-1 EXPORT_BUYER_REPLY_21D EXPORT",
        "affected_workflows": "EXPORT",
        "proposed_version": "CAND-1",
        "status": "APPROVED",
        "approval_id": "APR-1",
        "rollback_artifact_path": "outputs/models/rollback.json",
    }
    row.update(overrides)
    return row


def _evaluation(**overrides: object) -> dict[str, object]:
    report: dict[str, object] = {
        "candidate_model_id": "CAND-1",
        "target_id": "EXPORT_BUYER_REPLY_21D",
        "workflow_type": "EXPORT",
        "coverage": 0.9,
        "current_champion": "CHAMP-0",
        "brier_improvement_vs_champion": 0.05,
        "promotion_decision": "NOT_PROMOTED_BY_EVALUATION_SCRIPT",
        "deterministic_tests_passed": True,
        "behavioral_tests_passed": True,
        "metrics": {"brier_score": 0.2},
    }
    report.update(overrides)
    return report


def test_promotion_validation_requires_approved_learning_proposal() -> None:
    errors = validate_promotion(
        model_registry_rows=[_candidate()],
        learning_proposals=[_proposal(status="PASS")],
        evaluation_report=_evaluation(),
        candidate_model_id="CAND-1",
        proposal_id="LP-1",
    )

    assert any("APPROVED MODEL learning proposal" in error for error in errors)


def test_promotion_validation_requires_improvement_and_tests() -> None:
    errors = validate_promotion(
        model_registry_rows=[_candidate()],
        learning_proposals=[_proposal()],
        evaluation_report=_evaluation(brier_improvement_vs_champion=-0.01, deterministic_tests_passed=False),
        candidate_model_id="CAND-1",
        proposal_id="LP-1",
    )

    assert any("improve brier" in error for error in errors)
    assert any("deterministic tests must pass" in error for error in errors)


def test_promotion_validation_passes_for_fully_gated_candidate() -> None:
    errors = validate_promotion(
        model_registry_rows=[_candidate()],
        learning_proposals=[_proposal()],
        evaluation_report=_evaluation(),
        candidate_model_id="CAND-1",
        proposal_id="LP-1",
    )

    assert errors == []


def test_promote_rows_retires_existing_champion_and_marks_candidate() -> None:
    rows = [
        _candidate(model_id="CHAMP-0", model_version="champion-v0", status="CHAMPION", rollback_version="champion-v-1"),
        _candidate(),
    ]

    promoted = promote_rows(rows, candidate_model_id="CAND-1", approval_id="APR-1", promoted_at="2099-02-01T00:00:00+00:00")

    assert next(row for row in promoted if row["model_id"] == "CAND-1")["status"] == "CHAMPION"
    assert next(row for row in promoted if row["model_id"] == "CAND-1")["approval_id"] == "APR-1"
    assert next(row for row in promoted if row["model_id"] == "CHAMP-0")["status"] == "RETIRED"
