from __future__ import annotations

import datetime as dt
import json

from scripts.train_candidate_models import build_candidate_training_report


def _training_fixture(count: int = 100) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    backtests: list[dict[str, str]] = []
    forecasts: list[dict[str, str]] = []
    base = dt.date(2099, 1, 1)
    for index in range(count):
        forecast_id = f"FC-{index:03d}"
        forecast_date = base + dt.timedelta(days=index)
        target_id = "EXPORT_BUYER_REPLY_21D"
        workflow_type = "EXPORT"
        binary = "1" if index < 20 else "0"
        backtests.append(
            {
                "forecast_id": forecast_id,
                "forecast_date": forecast_date.isoformat(),
                "target_id": target_id,
                "workflow_type": workflow_type,
                "is_mature": "TRUE",
                "predicted_probability": "0.65",
                "binary_outcome": binary,
                "model_version": "teos-expert-prior-v1",
            }
        )
        forecasts.append(
            {
                "forecast_id": forecast_id,
                "target_id": target_id,
                "workflow_type": workflow_type,
                "feature_snapshot_json": json.dumps({"source_count": 2, "evidence_score": 0.6}),
            }
        )
    return backtests, forecasts


def test_training_report_blocks_when_target_gate_is_not_met() -> None:
    backtests, forecasts = _training_fixture(count=29)

    report = build_candidate_training_report(backtest_rows=backtests, forecast_rows=forecasts, as_of="2099-05-01")

    assert report["status"] == "BLOCKED_INSUFFICIENT_MATURE_SAMPLE"
    assert report["eligible_candidates"] == []


def test_training_report_creates_candidate_plan_after_training_gate() -> None:
    backtests, forecasts = _training_fixture()

    report = build_candidate_training_report(backtest_rows=backtests, forecast_rows=forecasts, as_of="2099-05-01")

    assert report["status"] == "CANDIDATE_TRAINING_READY"
    candidate = report["eligible_candidates"][0]
    assert candidate["target_id"] == "EXPORT_BUYER_REPLY_21D"
    assert candidate["workflow_type"] == "EXPORT"
    assert candidate["model_family"] == "interpretable_logistic_baseline"
    assert candidate["split_strategy"] == "time_based_60_20_20"
    assert len(candidate["feature_schema_hash"]) == 64


def test_training_report_blocks_unsafe_feature_keys() -> None:
    backtests, forecasts = _training_fixture()
    forecasts[0]["feature_snapshot_json"] = json.dumps({"future_reply_after_prediction": 1})

    report = build_candidate_training_report(backtest_rows=backtests, forecast_rows=forecasts, as_of="2099-05-01")

    assert report["status"] == "BLOCKED_INSUFFICIENT_MATURE_SAMPLE"
    assert report["eligible_candidates"] == []
    assert report["blocked_targets"][0]["reason"] == "unsafe feature keys present"
