#!/usr/bin/env python3
"""Validate forecast model registry rows against target-specific maturity gates."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

try:
    from scripts.validate_forecast_targets import load_targets, maturity_status, target_index
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from validate_forecast_targets import load_targets, maturity_status, target_index


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_REGISTRY_PATH = PROJECT_ROOT / "data" / "model_registry.csv"

CALIBRATION_STATUSES_REQUIRING_CALIBRATION = {"EVALUATED", "CALIBRATED", "DRIFTED"}
MODEL_STATUSES_REQUIRING_TRAINING = {"CANDIDATE", "CHAMPION"}


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def upper(value: Any) -> str:
    return clean(value).upper()


def safe_int(value: Any) -> int:
    try:
        return int(float(clean(value) or "0"))
    except ValueError:
        return 0


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_model_registry_gates(rows: list[dict[str, Any]], *, target_config: dict[str, Any] | None = None) -> list[str]:
    config = target_config or load_targets()
    targets = target_index(config)
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        model_id = clean(row.get("model_id")) or f"row[{index}]"
        target_id = clean(row.get("target_id"))
        workflow_type = upper(row.get("workflow_type"))
        target = targets.get(target_id)
        if target is None:
            errors.append(f"{model_id}.target_id is not registered: {target_id}")
            continue
        if workflow_type != upper(target.get("workflow_type")):
            errors.append(f"{model_id}.workflow_type does not match target registry")
        if workflow_type in {"MIXED", "CROSS_WORKFLOW"}:
            errors.append(f"{model_id}.workflow_type must not mix forecast populations")
        gate = maturity_status(
            target_id=target_id,
            mature_observations=safe_int(row.get("mature_sample_count")),
            positive_class_count=safe_int(row.get("positive_class_count")),
            negative_class_count=safe_int(row.get("negative_class_count")),
            config=config,
        )
        calibration_status = upper(row.get("calibration_status"))
        model_status = upper(row.get("status"))
        if calibration_status in CALIBRATION_STATUSES_REQUIRING_CALIBRATION and not gate["calibration_ready"]:
            errors.append(f"{model_id}.{calibration_status} requires at least {gate['calibration_required']} mature observations for exact target/workflow")
        if model_status in MODEL_STATUSES_REQUIRING_TRAINING and not gate["training_ready"]:
            errors.append(
                f"{model_id}.{model_status} requires at least {gate['training_required']} mature observations and "
                f"{gate['positive_class_required']}/{gate['negative_class_required']} class counts"
            )
        if model_status == "CHAMPION" and not clean(row.get("rollback_version")):
            errors.append(f"{model_id}.rollback_version is required for CHAMPION")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-registry", default=str(DEFAULT_MODEL_REGISTRY_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    rows = load_csv(Path(args.model_registry))
    errors = validate_model_registry_gates(rows)
    payload = {"status": "PASS" if not errors else "FAIL", "model_count": len(rows), "errors": errors}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"Model registry gates: {payload['status']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
