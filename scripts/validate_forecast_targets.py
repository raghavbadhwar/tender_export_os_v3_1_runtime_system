#!/usr/bin/env python3
"""Validate the forecast target registry and maturity gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - direct CLI dependency error
    yaml = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS_PATH = PROJECT_ROOT / "config" / "forecast_targets.yaml"

REQUIRED_TARGET_IDS = {
    "GOV_PROGRESS_JUSTIFIED_KILL_30D",
    "GOV_L1_COMPETITION_RISK_45D",
    "EXPORT_BUYER_REPLY_21D",
    "EXPORT_RFQ_CONVERSION_60D",
    "SUPPLIER_QUOTE_RESPONSE_14D",
    "SUPPLIER_RELIABILITY_90D",
    "PAYMENT_DELAY_RISK_120D",
    "SOURCE_YIELD_30D",
}

REQUIRED_TARGET_FIELDS = {
    "target_id",
    "workflow_type",
    "horizon_days",
    "target_family",
    "prediction_target",
    "positive_label",
    "negative_label",
    "label_rule",
    "eligible_population",
    "feature_list",
    "leakage_exclusions",
    "maturity_rule",
    "business_use",
    "allowed_use",
    "forbidden_use",
}

REQUIRED_MATURITY_FIELDS = {
    "label_available_after_days",
    "minimum_mature_observations_for_calibration",
    "minimum_mature_observations_for_model_training",
    "minimum_positive_class_for_model_training",
    "minimum_negative_class_for_model_training",
    "time_separated_evaluation_required",
}


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def upper(value: Any) -> str:
    return clean(value).upper()


def load_targets(path: Path = DEFAULT_TARGETS_PATH) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load forecast targets")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"forecast targets must be a mapping: {path}")
    return value


def _nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and all(clean(item) for item in value)


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate_forecast_targets(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    targets = config.get("targets", [])
    if not isinstance(targets, list) or not targets:
        return ["targets must be a non-empty list"]

    allowed_workflows = {upper(item) for item in config.get("allowed_workflow_types", [])}
    global_leakage = set(clean(item) for item in config.get("global_leakage_exclusions", []) if clean(item))
    global_forbidden = set(clean(item) for item in config.get("global_forbidden_use", []) if clean(item))
    if not allowed_workflows:
        errors.append("allowed_workflow_types must be non-empty")
    if not global_leakage:
        errors.append("global_leakage_exclusions must be non-empty")
    if not global_forbidden:
        errors.append("global_forbidden_use must be non-empty")

    seen: set[str] = set()
    families_by_workflow: dict[str, set[str]] = {}
    for index, target in enumerate(targets, start=1):
        if not isinstance(target, dict):
            errors.append(f"targets[{index}] must be an object")
            continue
        target_id = clean(target.get("target_id"))
        label = target_id or f"targets[{index}]"
        missing = sorted(field for field in REQUIRED_TARGET_FIELDS if target.get(field) in (None, ""))
        for field in missing:
            errors.append(f"{label}.{field} is required")
        if target_id in seen:
            errors.append(f"duplicate target_id: {target_id}")
        seen.add(target_id)

        workflow_type = upper(target.get("workflow_type"))
        if workflow_type not in allowed_workflows:
            errors.append(f"{label}.workflow_type is not allowed")
        families_by_workflow.setdefault(workflow_type, set()).add(clean(target.get("target_family")))

        horizon_days = target.get("horizon_days")
        if not _positive_int(horizon_days):
            errors.append(f"{label}.horizon_days must be a positive integer")

        for list_field in ("feature_list", "leakage_exclusions", "allowed_use", "forbidden_use"):
            if not _nonempty_list(target.get(list_field)):
                errors.append(f"{label}.{list_field} must be a non-empty list of strings")
        features = {clean(item) for item in target.get("feature_list", []) if clean(item)}
        leakage = {clean(item) for item in target.get("leakage_exclusions", []) if clean(item)}
        if features & leakage:
            errors.append(f"{label}.feature_list overlaps leakage_exclusions: {sorted(features & leakage)}")
        if len(features) < 5:
            errors.append(f"{label}.feature_list must include at least 5 pre-outcome features")
        if len(leakage) < 3:
            errors.append(f"{label}.leakage_exclusions must include at least 3 post-outcome exclusions")
        if not any("after_prediction" in item or item.startswith("future_") for item in leakage):
            errors.append(f"{label}.leakage_exclusions must explicitly block future/post-prediction fields")

        maturity = target.get("maturity_rule")
        if not isinstance(maturity, dict):
            errors.append(f"{label}.maturity_rule must be an object")
            continue
        for field in REQUIRED_MATURITY_FIELDS:
            if field not in maturity:
                errors.append(f"{label}.maturity_rule.{field} is required")
        if maturity.get("time_separated_evaluation_required") is not True:
            errors.append(f"{label}.maturity_rule.time_separated_evaluation_required must be true")
        if maturity.get("label_available_after_days") != horizon_days:
            errors.append(f"{label}.maturity_rule.label_available_after_days must equal horizon_days")
        if not _positive_int(maturity.get("minimum_mature_observations_for_calibration")):
            errors.append(f"{label}.maturity_rule.minimum_mature_observations_for_calibration must be positive")
        elif maturity["minimum_mature_observations_for_calibration"] < 30:
            errors.append(f"{label}.maturity_rule.minimum_mature_observations_for_calibration must be at least 30")
        if not _positive_int(maturity.get("minimum_mature_observations_for_model_training")):
            errors.append(f"{label}.maturity_rule.minimum_mature_observations_for_model_training must be positive")
        elif maturity["minimum_mature_observations_for_model_training"] < 100:
            errors.append(f"{label}.maturity_rule.minimum_mature_observations_for_model_training must be at least 100")
        for field in ("minimum_positive_class_for_model_training", "minimum_negative_class_for_model_training"):
            if not _positive_int(maturity.get(field)):
                errors.append(f"{label}.maturity_rule.{field} must be positive")
            elif maturity[field] < 20:
                errors.append(f"{label}.maturity_rule.{field} must be at least 20")

    missing_targets = REQUIRED_TARGET_IDS - seen
    extra_required_targets = seen & REQUIRED_TARGET_IDS
    if missing_targets:
        errors.append(f"missing required target_ids: {sorted(missing_targets)}")
    if len(extra_required_targets) != len(REQUIRED_TARGET_IDS):
        errors.append("forecast target registry must cover all required target families")
    if "CROSS_WORKFLOW" in families_by_workflow or "MIXED" in families_by_workflow:
        errors.append("forecast targets must not use CROSS_WORKFLOW or MIXED workflow probabilities")
    if any("," in clean(target.get("workflow_type")) for target in targets if isinstance(target, dict)):
        errors.append("forecast targets must not combine multiple workflows in one target")
    return errors


def target_index(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        clean(target.get("target_id")): dict(target)
        for target in config.get("targets", [])
        if isinstance(target, dict) and clean(target.get("target_id"))
    }


def maturity_status(
    *,
    target_id: str,
    mature_observations: int,
    positive_class_count: int,
    negative_class_count: int,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or load_targets()
    target = target_index(config).get(clean(target_id))
    if target is None:
        raise KeyError(f"unknown forecast target: {target_id}")
    maturity = target["maturity_rule"]
    calibration_ready = mature_observations >= int(maturity["minimum_mature_observations_for_calibration"])
    training_ready = (
        mature_observations >= int(maturity["minimum_mature_observations_for_model_training"])
        and positive_class_count >= int(maturity["minimum_positive_class_for_model_training"])
        and negative_class_count >= int(maturity["minimum_negative_class_for_model_training"])
    )
    status = "TRAINING_READY" if training_ready else "CALIBRATION_READY" if calibration_ready else "PRIOR_UNCALIBRATED"
    return {
        "target_id": clean(target_id),
        "status": status,
        "calibration_ready": calibration_ready,
        "training_ready": training_ready,
        "mature_observations": mature_observations,
        "positive_class_count": positive_class_count,
        "negative_class_count": negative_class_count,
        "calibration_required": maturity["minimum_mature_observations_for_calibration"],
        "training_required": maturity["minimum_mature_observations_for_model_training"],
        "positive_class_required": maturity["minimum_positive_class_for_model_training"],
        "negative_class_required": maturity["minimum_negative_class_for_model_training"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_TARGETS_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    config = load_targets(Path(args.config))
    errors = validate_forecast_targets(config)
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "target_count": len(config.get("targets", [])) if isinstance(config.get("targets"), list) else 0,
        "errors": errors,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"Forecast targets: {payload['status']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
