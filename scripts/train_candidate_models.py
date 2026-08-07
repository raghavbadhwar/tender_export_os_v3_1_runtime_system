#!/usr/bin/env python3
"""Prepare candidate forecast models only after target-specific gates pass.

This script intentionally starts with an interpretable baseline plan and refuses
training when the exact target/workflow maturity gates are not met.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.evaluate_forecast_calibration import evaluate_rows
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from evaluate_forecast_calibration import evaluate_rows


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FORECASTS = PROJECT_ROOT / "data" / "forecast_candidates.csv"
DEFAULT_BACKTESTS = PROJECT_ROOT / "data" / "forecast_backtests.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "models"

MODEL_FAMILY = "interpretable_logistic_baseline"
FEATURE_PIPELINE_VERSION = "forecast-target-features-v1"
FORBIDDEN_FEATURE_PATTERNS = {
    "owner_decision_after_prediction",
    "reply_after_prediction",
    "quote_after_prediction",
    "won_lost_after_prediction",
    "future_",
    "password",
    "token",
    "cookie",
    "session",
    "email_body",
    "phone",
    "aadhaar",
    "pan",
    "bank",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def parse_date(value: Any) -> dt.date | None:
    text = clean(value)
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        return None


def safe_feature_keys(forecast_rows: list[dict[str, Any]], target_id: str, workflow_type: str) -> tuple[list[str], list[str]]:
    keys: set[str] = set()
    violations: set[str] = set()
    for row in forecast_rows:
        if clean(row.get("target_id")) != target_id or clean(row.get("workflow_type")).upper() != workflow_type.upper():
            continue
        try:
            features = json.loads(clean(row.get("feature_snapshot_json")) or "{}")
        except json.JSONDecodeError:
            violations.add("malformed_feature_snapshot_json")
            continue
        if not isinstance(features, dict):
            violations.add("feature_snapshot_json_not_object")
            continue
        for key in features:
            key_text = clean(key)
            keys.add(key_text)
            lower = key_text.lower()
            if any(pattern in lower for pattern in FORBIDDEN_FEATURE_PATTERNS):
                violations.add(key_text)
    return sorted(keys), sorted(violations)


def time_windows(backtest_rows: list[dict[str, Any]], target_id: str, workflow_type: str) -> dict[str, str]:
    dates = sorted(
        date
        for row in backtest_rows
        if clean(row.get("target_id")) == target_id and clean(row.get("workflow_type")).upper() == workflow_type.upper()
        for date in [parse_date(row.get("forecast_date"))]
        if date is not None
    )
    if not dates:
        return {}
    train_end_index = max(0, int(len(dates) * 0.6) - 1)
    validation_end_index = max(train_end_index, int(len(dates) * 0.8) - 1)
    return {
        "training_window_start": dates[0].isoformat(),
        "training_window_end": dates[train_end_index].isoformat(),
        "validation_window_start": dates[min(train_end_index + 1, len(dates) - 1)].isoformat(),
        "validation_window_end": dates[validation_end_index].isoformat(),
        "test_window_start": dates[min(validation_end_index + 1, len(dates) - 1)].isoformat(),
        "test_window_end": dates[-1].isoformat(),
    }


def build_candidate_training_report(
    *,
    backtest_rows: list[dict[str, Any]],
    forecast_rows: list[dict[str, Any]],
    as_of: str,
) -> dict[str, Any]:
    calibration = evaluate_rows(backtest_rows, forecast_rows=forecast_rows)
    eligible: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for target in calibration.get("target_evaluations", []):
        target_id = target["target_id"]
        workflow_type = target["workflow_type"]
        feature_keys, feature_violations = safe_feature_keys(forecast_rows, target_id, workflow_type)
        if target["training_ready"] and not feature_violations:
            split = time_windows(backtest_rows, target_id, workflow_type)
            feature_schema_hash = hashlib.sha256(
                json.dumps(
                    {
                        "target_id": target_id,
                        "workflow_type": workflow_type,
                        "feature_pipeline_version": FEATURE_PIPELINE_VERSION,
                        "features": feature_keys,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            eligible.append(
                {
                    "target_id": target_id,
                    "workflow_type": workflow_type,
                    "model_family": MODEL_FAMILY,
                    "feature_pipeline_version": FEATURE_PIPELINE_VERSION,
                    "feature_schema_hash": feature_schema_hash,
                    "feature_keys": feature_keys,
                    "split_strategy": "time_based_60_20_20",
                    "time_windows": split,
                    "mature_sample_size": target["mature_sample_size"],
                    "positive_class_count": target["positive_class_count"],
                    "negative_class_count": target["negative_class_count"],
                    "next_step": "Run candidate evaluation on fixed holdout before model registry promotion.",
                }
            )
        else:
            blocked.append(
                {
                    "target_id": target_id,
                    "workflow_type": workflow_type,
                    "status": target["status"],
                    "training_ready": target["training_ready"],
                    "feature_violations": feature_violations,
                    "reason": "training gate not met" if not target["training_ready"] else "unsafe feature keys present",
                }
            )
    return {
        "status": "CANDIDATE_TRAINING_READY" if eligible else "BLOCKED_INSUFFICIENT_MATURE_SAMPLE",
        "as_of": as_of,
        "model_family": MODEL_FAMILY,
        "feature_pipeline_version": FEATURE_PIPELINE_VERSION,
        "eligible_candidates": eligible,
        "blocked_targets": blocked,
        "calibration_status": calibration["status"],
        "safety_boundary": "No model is promoted, registered as champion, or used for external/financial/legal action by this script.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backtests", default=str(DEFAULT_BACKTESTS))
    parser.add_argument("--forecasts", default=str(DEFAULT_FORECASTS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--as-of", default=dt.date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    backtests = Path(args.backtests).expanduser().resolve()
    forecasts = Path(args.forecasts).expanduser().resolve()
    report = build_candidate_training_report(
        backtest_rows=load_csv(backtests),
        forecast_rows=load_csv(forecasts),
        as_of=args.as_of,
    )
    outputs: dict[str, str] = {}
    if args.write:
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"candidate_training_{args.as_of.replace('-', '')}.json"
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        outputs["json"] = rel(output)
    payload = report | {"outputs": outputs}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else payload["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
