from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.pricing_scenario_builder import build_scenarios, validate_report, write_report


def test_pricing_scenarios_include_required_decision_cases() -> None:
    report = build_scenarios(
        case_id="EXP-1",
        workflow_type="EXPORT",
        base_cost=1000,
        currency="USD",
        target_margin_pct=20,
        quote_validity_days=30,
        working_capital_need=100,
        stress_cost_increase_pct=30,
        owner_min_margin_pct=10,
    )

    assert validate_report(report) == []
    assert [row["name"] for row in report["scenarios"]] == ["base", "conservative", "stress", "walk_away"]
    assert report["external_actions_executed"] is False
    assert all(row["final_commitment"] is False for row in report["scenarios"])
    stress = next(row for row in report["scenarios"] if row["name"] == "stress")
    assert stress["downside_loss"] > 0
    assert report["owner_decision_threshold"]["minimum_price"] == 1210


def test_pricing_scenarios_reject_invalid_or_externalized_cases() -> None:
    with pytest.raises(ValueError, match="base_cost must be positive"):
        build_scenarios(
            case_id="GOV-1",
            workflow_type="GOV",
            base_cost=0,
            currency="INR",
            target_margin_pct=15,
            quote_validity_days=30,
        )

    report = build_scenarios(
        case_id="GOV-1",
        workflow_type="GOV",
        base_cost=10000,
        currency="INR",
        target_margin_pct=15,
        quote_validity_days=30,
    )
    report["scenarios"][0]["final_commitment"] = True

    assert any("final_commitment must be false" in error for error in validate_report(report))


def test_write_pricing_scenarios_creates_internal_event(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    report = build_scenarios(
        case_id="GOV-1",
        workflow_type="GOV",
        base_cost=10000,
        currency="INR",
        target_margin_pct=15,
        quote_validity_days=20,
    )

    result = write_report(report, output_dir=tmp_path / "case", events_path=events)

    assert Path(result["json_path"]).is_file()
    event = json.loads(events.read_text(encoding="utf-8").strip())
    assert event["event_type"] == "pricing.scenarios_drafted"
    assert event["payload"]["scenario_count"] == 4
