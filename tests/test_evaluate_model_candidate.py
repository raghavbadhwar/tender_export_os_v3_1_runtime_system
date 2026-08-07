from __future__ import annotations

from scripts.evaluate_model_candidate import evaluate_candidate, mature_scored_rows, metric_summary


def _rows() -> list[dict[str, object]]:
    return [
        {
            "forecast_id": "FC-1",
            "target_id": "EXPORT_BUYER_REPLY_21D",
            "workflow_type": "EXPORT",
            "forecast_type": "ACTIVE_CASE",
            "is_mature": "TRUE",
            "predicted_probability": "0.8",
            "binary_outcome": "1",
        },
        {
            "forecast_id": "FC-2",
            "target_id": "EXPORT_BUYER_REPLY_21D",
            "workflow_type": "EXPORT",
            "forecast_type": "ACTIVE_CASE",
            "is_mature": "TRUE",
            "predicted_probability": "0.7",
            "binary_outcome": "0",
        },
        {
            "forecast_id": "FC-3",
            "target_id": "EXPORT_BUYER_REPLY_21D",
            "workflow_type": "EXPORT",
            "forecast_type": "RESEARCH_LANE",
            "is_mature": "FALSE",
            "predicted_probability": "0.6",
            "binary_outcome": "",
        },
    ]


def test_model_candidate_metrics_include_brier_log_loss_precision_recall() -> None:
    metrics = metric_summary(mature_scored_rows(_rows(), target_id="EXPORT_BUYER_REPLY_21D", workflow_type="EXPORT"), threshold=0.75)

    assert metrics["count"] == 2
    assert metrics["brier_score"] == 0.265
    assert metrics["log_loss"] is not None
    assert metrics["calibration_error"] is not None
    assert metrics["precision_at_threshold"] == 1.0
    assert metrics["recall_at_threshold"] == 1.0


def test_model_candidate_evaluation_compares_current_champion() -> None:
    report = evaluate_candidate(
        rows=_rows(),
        model_registry_rows=[
            {
                "model_id": "CHAMPION-1",
                "target_id": "EXPORT_BUYER_REPLY_21D",
                "workflow_type": "EXPORT",
                "status": "CHAMPION",
                "brier_score": "0.300000",
            }
        ],
        candidate_model_id="CAND-1",
        target_id="EXPORT_BUYER_REPLY_21D",
        workflow_type="EXPORT",
        threshold=0.75,
    )

    assert report["metrics"]["count"] == 2
    assert report["coverage"] == 0.666667
    assert report["current_champion"] == "CHAMPION-1"
    assert report["brier_improvement_vs_champion"] == 0.035
    assert "workflow:EXPORT" in report["subgroup_breakdown"]
    assert report["promotion_decision"] == "NOT_PROMOTED_BY_EVALUATION_SCRIPT"
