import csv
import datetime as dt

from scripts.backtest_v5_demand_forecasts import build_rows as build_backtest_rows
from scripts.backtest_v5_demand_forecasts import label_forecast, write_backtest_rows
from scripts.build_buyer_purchase_history import build_rows as build_buyer_rows
from scripts.build_category_demand_history import build_rows as build_category_rows
from scripts.evaluate_forecast_calibration import evaluate_rows
from scripts.generate_v5_demand_forecast_low_competition import (
    estimate_operational_probability,
    filter_terminal_candidates,
    write_forecast_candidates,
)


def test_one_buyer_case_does_not_invent_a_repeat_window() -> None:
    rows = build_buyer_rows(
        [
            {
                "case_id": "EXP-20990101-001",
                "buyer_name": "Example Importer",
                "product_or_service": "Spices",
                "workflow_type": "EXPORT",
                "created_at": "2099-01-01",
                "updated_at": "2099-01-03",
                "deadline_date": "2099-02-01",
            }
        ],
        dt.date(2099, 1, 4),
    )

    assert rows[0]["past_case_count"] == "1"
    assert rows[0]["repeat_interval_days"] == ""
    assert rows[0]["next_likely_window_start"] == ""
    assert rows[0]["next_likely_window_end"] == ""
    assert rows[0]["confidence"] == "LOW"


def test_research_only_category_demand_is_capped_without_verified_rfq() -> None:
    demand_rows = [
        {
            "research_id": f"DEM-{index}",
            "category_name": "Handicrafts",
            "country": "UK",
            "source_name": f"Source {index}",
            "market_fit_score": "100",
            "created_at": "2099-01-01",
        }
        for index in range(1, 5)
    ]

    rows = build_category_rows([], demand_rows, [], {}, dt.date(2099, 1, 2))

    assert float(rows[0]["demand_score"]) <= 55
    assert rows[0]["confidence"] == "LOW"
    assert rows[0]["verified_rfq_count"] == "0"


def test_same_day_weak_forecast_is_not_mature_blocked_outcome() -> None:
    forecast = {
        "forecast_date": "2099-01-01",
        "horizon": "7-30 days",
        "evidence_level": "PUBLIC_LISTING_ONLY",
        "proof_gap": "document proof",
    }
    case = {"status": "NEW", "evidence_level": "PUBLIC_LISTING_ONLY"}

    label, *_ = label_forecast(forecast, case, dt.date(2099, 1, 1))

    assert label == "NOT_ENOUGH_TIME"


def test_same_day_preexisting_rejection_is_not_counted_as_forecast_success() -> None:
    forecast = {
        "forecast_date": "2099-01-01",
        "eligible_for_backtest_at": "2099-01-15",
        "horizon": "0-7 days",
        "evidence_level": "PUBLIC_LISTING_ONLY",
        "proof_gap": "document proof",
    }
    case = {"status": "REJECTED", "kill_reason": "DEADLINE_PASSED", "updated_at": "2099-01-01"}

    label, *_ = label_forecast(forecast, case, dt.date(2099, 1, 1))

    assert label == "NOT_ENOUGH_TIME"


def test_advanced_case_status_alone_never_matures_forecast() -> None:
    forecast = {
        "forecast_id": "FC-1",
        "forecast_date": "2099-01-01",
        "eligible_for_backtest_at": "2099-01-08",
        "horizon": "0-7 days",
        "case_or_research_id": "GOV-1",
        "forecast_type": "ACTIVE_CASE",
        "predicted_probability": "0.7",
    }
    case = {"case_id": "GOV-1", "status": "WON", "updated_at": "2099-01-09"}

    row = build_backtest_rows([forecast], [case], dt.date(2099, 1, 10), outcomes=[], events=[])[0]

    assert row["is_mature"] == "FALSE"
    assert row["outcome_label"] == "BLOCKED_BY_PROOF"
    assert "verified" in row["observed_outcome"].lower()


def test_verified_time_separated_outcome_matures_forecast() -> None:
    forecast = {
        "forecast_id": "FC-1",
        "forecast_date": "2099-01-01",
        "eligible_for_backtest_at": "2099-01-08",
        "horizon": "0-7 days",
        "case_or_research_id": "GOV-1",
        "forecast_type": "ACTIVE_CASE",
        "predicted_probability": "0.7",
    }
    outcome = {
        "outcome_id": "OUT-1",
        "case_id": "GOV-1",
        "outcome_type": "WON",
        "outcome_value": "Awarded",
        "occurred_at": "2099-01-09T09:00:00+00:00",
        "recorded_at": "2099-01-09T10:00:00+00:00",
        "verification_status": "VERIFIED",
        "evidence_path": "receipts/award.json",
        "evidence_sha256": "a" * 64,
    }
    event = {
        "event_id": "EVT-OUT-1",
        "event_type": "case.outcome_recorded",
        "object_id": "OUT-1",
        "case_id": "GOV-1",
        "event_time": "2099-01-09T10:00:00+00:00",
    }

    row = build_backtest_rows(
        [forecast],
        [{"case_id": "GOV-1", "status": "WON"}],
        dt.date(2099, 1, 10),
        outcomes=[outcome],
        events=[event],
    )[0]

    assert row["is_mature"] == "TRUE"
    assert row["binary_outcome"] == 1
    assert row["outcome_label"] == "HIT"


def test_outcome_that_predates_forecast_is_excluded() -> None:
    forecast = {
        "forecast_id": "FC-1",
        "forecast_date": "2099-01-10",
        "eligible_for_backtest_at": "2099-01-11",
        "horizon": "0-7 days",
        "case_or_research_id": "GOV-1",
        "forecast_type": "ACTIVE_CASE",
    }
    outcome = {
        "outcome_id": "OUT-OLD",
        "case_id": "GOV-1",
        "outcome_type": "WON",
        "occurred_at": "2099-01-09T09:00:00+00:00",
        "recorded_at": "2099-01-09T10:00:00+00:00",
        "verification_status": "VERIFIED",
        "evidence_path": "receipts/award.json",
        "evidence_sha256": "a" * 64,
    }
    event = {
        "event_id": "EVT-OLD",
        "event_type": "case.outcome_recorded",
        "object_id": "OUT-OLD",
        "case_id": "GOV-1",
        "event_time": "2099-01-09T10:00:00+00:00",
    }

    row = build_backtest_rows(
        [forecast],
        [{"case_id": "GOV-1", "status": "WON"}],
        dt.date(2099, 1, 20),
        outcomes=[outcome],
        events=[event],
    )[0]

    assert row["is_mature"] == "FALSE"
    assert row["outcome_label"] == "BLOCKED_BY_PROOF"


def test_terminal_cases_are_removed_from_stale_low_competition_candidates() -> None:
    candidates = [{"case_id": "GOV-1"}, {"case_id": "GOV-2"}, {"case_id": ""}]
    cases = [{"case_id": "GOV-1", "status": "REJECTED"}, {"case_id": "GOV-2", "status": "WATCHLIST"}]

    assert filter_terminal_candidates(candidates, cases) == [{"case_id": "GOV-2"}, {"case_id": ""}]


def _payload(date: str, case_id: str, evidence: str = "PUBLIC_LISTING_ONLY") -> dict:
    item = {
        "type": "active_case_forecast",
        "case_id": case_id,
        "workflow_type": "GOV",
        "buyer": "Example Buyer",
        "country_or_location": "India",
        "product_or_category": "Office Supplies",
        "source": "CPPP",
        "source_url": "https://example.test/tender",
        "horizon": "7-30 days",
        "forecast_score": 70,
        "confidence": "MEDIUM",
        "repeat_probability": 20,
        "low_competition_signal_score": 30,
        "supplier_readiness_score": 40,
        "evidence_label": evidence,
        "proof_gap": "document proof" if evidence == "PUBLIC_LISTING_ONLY" else "none",
        "next_safe_action": "Review internally",
        "status": "NEW",
    }
    return {
        "date": date.replace("-", ""),
        "run_id": f"RUN-{date}",
        "active_case_forecasts": [item],
        "research_forecasts": [],
        "low_competition_candidates": [],
        "buyer_repeat_predictions": [],
        "category_demand_predictions": [],
    }


def test_forecast_history_is_upserted_without_erasing_prior_dates(tmp_path) -> None:
    output = tmp_path / "forecasts.csv"

    write_forecast_candidates(output, _payload("2099-01-01", "GOV-1"))
    write_forecast_candidates(output, _payload("2099-01-02", "GOV-1"))
    write_forecast_candidates(output, _payload("2099-01-02", "GOV-1", "RFQ_VERIFIED"))

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert {row["forecast_date"] for row in rows} == {"2099-01-01", "2099-01-02"}
    assert next(row for row in rows if row["forecast_date"] == "2099-01-02")["evidence_level"] == "RFQ_VERIFIED"


def test_forecast_candidates_store_explicit_target_and_maturity_metadata(tmp_path) -> None:
    output = tmp_path / "forecasts.csv"

    new_rows = write_forecast_candidates(output, _payload("2099-01-01", "GOV-1"))

    assert new_rows[0]["target_id"] == "GOV_PROGRESS_JUSTIFIED_KILL_30D"
    assert new_rows[0]["horizon_days"] == 30
    assert new_rows[0]["prediction_timestamp"] == "2099-01-01T00:00:00+00:00"
    assert new_rows[0]["maturity_timestamp"] == "2099-01-31T23:59:59+00:00"
    assert len(new_rows[0]["feature_schema_hash"]) == 64
    assert new_rows[0]["probability_status"] == "PRIOR_UNCALIBRATED"
    assert new_rows[0]["eligible_for_backtest_at"] == "2099-01-31"


def test_export_forecasts_use_export_rfq_conversion_target(tmp_path) -> None:
    payload = _payload("2099-01-01", "EXP-1", "RFQ_VERIFIED")
    payload["active_case_forecasts"][0]["workflow_type"] = "EXPORT"
    output = tmp_path / "forecasts.csv"

    new_rows = write_forecast_candidates(output, payload)

    assert new_rows[0]["target_id"] == "EXPORT_RFQ_CONVERSION_60D"
    assert new_rows[0]["horizon_days"] == 60
    assert new_rows[0]["eligible_for_backtest_at"] == "2099-03-02"


def test_expert_prior_probability_is_monotonic_and_bounded() -> None:
    weak, _ = estimate_operational_probability(
        {
            "forecast_score": 30,
            "evidence_label": "PUBLIC_LISTING_ONLY",
            "source": "One source",
            "supplier_readiness_score": 0,
            "repeat_probability": 0,
            "low_competition_signal_score": 0,
        }
    )
    strong, features = estimate_operational_probability(
        {
            "forecast_score": 90,
            "evidence_label": "RFQ_VERIFIED",
            "source": "CPPP; GeM; Buyer site",
            "supplier_readiness_score": 90,
            "repeat_probability": 80,
            "low_competition_signal_score": 70,
        }
    )

    assert 0.03 <= weak < strong <= 0.78
    assert features["source_count"] == 3


def test_backtest_history_upserts_by_backtest_id(tmp_path) -> None:
    output = tmp_path / "backtests.csv"
    first = {"backtest_id": "FBT-1", "forecast_id": "FC-1", "outcome_label": "MISS"}
    updated = {"backtest_id": "FBT-1", "forecast_id": "FC-1", "outcome_label": "HIT"}
    second = {"backtest_id": "FBT-2", "forecast_id": "FC-2", "outcome_label": "MISS"}

    write_backtest_rows(output, [first])
    write_backtest_rows(output, [updated, second])

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert next(row for row in rows if row["backtest_id"] == "FBT-1")["outcome_label"] == "HIT"


def test_calibration_requires_enough_mature_outcomes() -> None:
    report = evaluate_rows(
        [
            {
                "is_mature": "TRUE",
                "predicted_probability": "0.7",
                "binary_outcome": "1",
                "model_version": "teos-expert-prior-v1",
                "target_id": "GOV_PROGRESS_JUSTIFIED_KILL_30D",
                "workflow_type": "GOV",
            }
        ],
        minimum_sample=30,
    )

    assert report["status"] == "INSUFFICIENT_MATURE_SAMPLE"
    assert report["mature_sample_size"] == 1
    assert report["brier_score"] is None
    assert report["target_evaluations"][0]["brier_score"] is None
    assert report["target_evaluations"][0]["status"] == "PRIOR_UNCALIBRATED"


def test_calibration_is_reported_only_per_exact_target_workflow_after_gate() -> None:
    rows = [
        {
            "forecast_id": f"FC-{index}",
            "is_mature": "TRUE",
            "predicted_probability": "0.7",
            "binary_outcome": "1" if index < 20 else "0",
            "model_version": "teos-expert-prior-v1",
            "target_id": "EXPORT_BUYER_REPLY_21D",
            "workflow_type": "EXPORT",
        }
        for index in range(30)
    ]

    report = evaluate_rows(rows, minimum_sample=30)

    assert report["status"] == "CALIBRATION_MEASURED"
    target = report["target_evaluations"][0]
    assert target["target_id"] == "EXPORT_BUYER_REPLY_21D"
    assert target["workflow_type"] == "EXPORT"
    assert target["calibration_ready"] is True
    assert target["training_ready"] is False
    assert target["brier_score"] is not None
    assert report["brier_score"] is None
