from __future__ import annotations

from scripts.build_weekly_forecast_quality_report import build_report


def test_weekly_forecast_quality_separates_gov_and_export_targets() -> None:
    forecasts = [
        {
            "forecast_id": "FC-GOV",
            "target_id": "GOV_PROGRESS_JUSTIFIED_KILL_30D",
            "workflow_type": "GOV",
            "feature_schema_hash": "aaa",
            "proof_gap": "document proof",
            "source_name": "GeM",
        },
        {
            "forecast_id": "FC-EXP",
            "target_id": "EXPORT_RFQ_CONVERSION_60D",
            "workflow_type": "EXPORT",
            "feature_schema_hash": "bbb",
            "proof_gap": "buyer proof",
            "source_name": "Alibaba",
        },
    ]
    report = build_report(
        forecasts=forecasts,
        backtests=[],
        source_health=[],
        week_ending="2099-01-07",
    )

    keys = {(row["target_id"], row["workflow_type"]) for row in report["target_populations"]}
    assert ("GOV_PROGRESS_JUSTIFIED_KILL_30D", "GOV") in keys
    assert ("EXPORT_RFQ_CONVERSION_60D", "EXPORT") in keys
    assert len(keys) == 2


def test_weekly_forecast_quality_flags_feature_and_source_drift() -> None:
    report = build_report(
        forecasts=[
            {
                "forecast_id": "FC-1",
                "target_id": "EXPORT_RFQ_CONVERSION_60D",
                "workflow_type": "EXPORT",
                "feature_schema_hash": "hash-1",
                "proof_gap": "buyer proof",
                "source_name": "Alibaba",
            },
            {
                "forecast_id": "FC-2",
                "target_id": "EXPORT_RFQ_CONVERSION_60D",
                "workflow_type": "EXPORT",
                "feature_schema_hash": "hash-2",
                "proof_gap": "supplier proof",
                "source_name": "TradeKey",
            },
        ],
        backtests=[{"forecast_id": "FC-1", "is_mature": "FALSE"}, {"forecast_id": "FC-2", "is_mature": "FALSE"}],
        source_health=[{"source_name": "TradeKey", "workflow": "EXPORT", "health_status": "FAILING", "consecutive_failures": "3"}],
        week_ending="2099-01-07",
    )

    population = report["target_populations"][0]
    assert population["feature_drift_status"] == "DRIFT_REVIEW"
    assert population["immature_count"] == 2
    assert report["source_drift"][0]["source_name"] == "TradeKey"
    assert report["actionable_collection_gaps"][0]["actionable_collection_gap"].startswith("Record verified")
