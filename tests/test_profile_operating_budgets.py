from __future__ import annotations

import copy

from scripts.validate_profile_operating_budgets import load_registry, validate_operating_budgets


def test_profile_operating_budgets_are_complete_and_telemetry_declared() -> None:
    registry = load_registry()

    assert validate_operating_budgets(registry) == []


def test_profile_operating_budget_rejects_missing_stop_threshold() -> None:
    registry = copy.deepcopy(load_registry())
    del registry["profiles"]["learning-evaluation"]["operating_budget"]["stop_on_no_progress_turns"]

    errors = validate_operating_budgets(registry)

    assert any("stop_on_no_progress_turns" in error for error in errors)


def test_profile_operating_budget_must_match_legacy_limits() -> None:
    registry = copy.deepcopy(load_registry())
    registry["profiles"]["pricing-risk"]["operating_budget"]["max_runtime_seconds"] = 999

    errors = validate_operating_budgets(registry)

    assert any("must match task_timeout_seconds" in error for error in errors)
