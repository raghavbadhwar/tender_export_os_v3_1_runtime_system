from __future__ import annotations

import copy

from scripts.validate_forecast_targets import (
    REQUIRED_TARGET_IDS,
    load_targets,
    maturity_status,
    validate_forecast_targets,
)


def test_forecast_target_registry_is_valid_and_complete() -> None:
    config = load_targets()
    target_ids = {target["target_id"] for target in config["targets"]}

    assert validate_forecast_targets(config) == []
    assert REQUIRED_TARGET_IDS <= target_ids


def test_forecast_targets_never_combine_gov_and_export_probability_claims() -> None:
    config = load_targets()

    for target in config["targets"]:
        assert target["workflow_type"] in {"GOV", "EXPORT", "SUPPLIER", "SOURCE"}
        assert target["workflow_type"] not in {"MIXED", "CROSS_WORKFLOW"}


def test_forecast_target_rejects_leaky_feature_overlap() -> None:
    config = load_targets()
    leaky = copy.deepcopy(config)
    leaky["targets"][0]["feature_list"].append("won_lost_after_prediction")
    leaky["targets"][0]["leakage_exclusions"].append("won_lost_after_prediction")

    errors = validate_forecast_targets(leaky)

    assert any("overlaps leakage_exclusions" in error for error in errors)


def test_forecast_target_requires_mature_samples_before_calibration_or_training() -> None:
    config = load_targets()

    prior = maturity_status(
        target_id="EXPORT_BUYER_REPLY_21D",
        mature_observations=29,
        positive_class_count=20,
        negative_class_count=9,
        config=config,
    )
    calibration_ready = maturity_status(
        target_id="EXPORT_BUYER_REPLY_21D",
        mature_observations=30,
        positive_class_count=20,
        negative_class_count=10,
        config=config,
    )
    training_ready = maturity_status(
        target_id="EXPORT_BUYER_REPLY_21D",
        mature_observations=100,
        positive_class_count=20,
        negative_class_count=80,
        config=config,
    )

    assert prior["status"] == "PRIOR_UNCALIBRATED"
    assert calibration_ready["status"] == "CALIBRATION_READY"
    assert training_ready["status"] == "TRAINING_READY"


def test_forecast_target_rejects_weak_maturity_gate() -> None:
    config = load_targets()
    weak = copy.deepcopy(config)
    weak["targets"][0]["maturity_rule"]["minimum_mature_observations_for_calibration"] = 10
    weak["targets"][0]["maturity_rule"]["minimum_mature_observations_for_model_training"] = 50
    weak["targets"][0]["maturity_rule"]["minimum_positive_class_for_model_training"] = 5

    errors = validate_forecast_targets(weak)

    assert any("calibration must be at least 30" in error for error in errors)
    assert any("model_training must be at least 100" in error for error in errors)
    assert any("positive_class_for_model_training must be at least 20" in error for error in errors)
