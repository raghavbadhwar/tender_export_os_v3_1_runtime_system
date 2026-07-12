import csv
import datetime as dt

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
            }
        ],
        minimum_sample=30,
    )

    assert report["status"] == "INSUFFICIENT_MATURE_SAMPLE"
    assert report["mature_sample_size"] == 1
    assert report["brier_score"] == 0.09
