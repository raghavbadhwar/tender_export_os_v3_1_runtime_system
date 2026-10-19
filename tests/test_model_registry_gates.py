from __future__ import annotations

from scripts.validate_model_registry_gates import validate_model_registry_gates


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "model_id": "MODEL-1",
        "target_id": "GOV_PROGRESS_JUSTIFIED_KILL_30D",
        "workflow_type": "GOV",
        "mature_sample_count": "29",
        "positive_class_count": "20",
        "negative_class_count": "9",
        "calibration_status": "CALIBRATED",
        "status": "PRIOR",
        "rollback_version": "",
    }
    row.update(overrides)
    return row


def test_model_registry_rejects_calibrated_status_before_target_gate() -> None:
    errors = validate_model_registry_gates([_row()])

    assert any("requires at least 30 mature observations" in error for error in errors)


def test_model_registry_rejects_candidate_before_training_and_class_gates() -> None:
    errors = validate_model_registry_gates(
        [
            _row(
                mature_sample_count="99",
                positive_class_count="79",
                negative_class_count="20",
                calibration_status="EVALUATED",
                status="CANDIDATE",
            )
        ]
    )

    assert any("requires at least 100 mature observations" in error for error in errors)


def test_model_registry_accepts_training_ready_candidate_for_exact_target_workflow() -> None:
    errors = validate_model_registry_gates(
        [
            _row(
                mature_sample_count="100",
                positive_class_count="20",
                negative_class_count="80",
                calibration_status="CALIBRATED",
                status="CANDIDATE",
            )
        ]
    )

    assert errors == []


def test_model_registry_rejects_cross_workflow_population_mix() -> None:
    errors = validate_model_registry_gates(
        [
            _row(
                workflow_type="CROSS_WORKFLOW",
                mature_sample_count="100",
                positive_class_count="20",
                negative_class_count="80",
                calibration_status="CALIBRATED",
                status="CANDIDATE",
            )
        ]
    )

    assert any("must not mix forecast populations" in error for error in errors)


def test_champion_requires_rollback_version() -> None:
    errors = validate_model_registry_gates(
        [
            _row(
                mature_sample_count="100",
                positive_class_count="20",
                negative_class_count="80",
                calibration_status="CALIBRATED",
                status="CHAMPION",
                rollback_version="",
            )
        ]
    )

    assert any("rollback_version is required" in error for error in errors)
