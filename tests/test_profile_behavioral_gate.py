from __future__ import annotations

from scripts.evaluate_hermes_behavioral_contracts import load_spec, validate_spec
from scripts.validate_profile_behavioral_gate import (
    DEFAULT_BEHAVIORAL_SPEC,
    DEFAULT_PROFILE_REGISTRY,
    load_yaml,
    validate_behavioral_gate,
)


def test_canonical_behavioral_eval_spec_is_valid() -> None:
    spec = load_spec(DEFAULT_BEHAVIORAL_SPEC)

    assert validate_spec(spec) == []


def test_canonical_behavioral_gate_covers_every_profile_and_required_type() -> None:
    result = validate_behavioral_gate(
        load_yaml(DEFAULT_BEHAVIORAL_SPEC),
        load_yaml(DEFAULT_PROFILE_REGISTRY),
    )

    assert result["status"] == "PASS"
    assert result["profile_count"] == 9
    assert result["required_repeats"] == 3
    assert result["critical_scenario_pass_rate"] == 1.0
    assert result["covered_scenario_types"] == result["required_scenario_types"]


def test_behavioral_gate_fails_if_live_work_can_start_without_pass() -> None:
    spec = load_yaml(DEFAULT_BEHAVIORAL_SPEC)
    registry = load_yaml(DEFAULT_PROFILE_REGISTRY)
    spec["live_work_gate"]["live_work_requires_pass"] = False
    spec["profile_scope"]["live_work_default"] = "LIVE"

    result = validate_behavioral_gate(spec, registry)

    assert result["status"] == "FAIL"
    assert any("live_work_requires_pass" in error for error in result["errors"])
    assert any("SHADOW_ONLY_UNTIL_GATE_PASS" in error for error in result["errors"])


def test_behavioral_gate_fails_if_required_scenario_class_is_missing() -> None:
    spec = load_yaml(DEFAULT_BEHAVIORAL_SPEC)
    registry = load_yaml(DEFAULT_PROFILE_REGISTRY)
    spec["scenarios"] = [
        row for row in spec["scenarios"] if row.get("scenario_type") != "PROMPT_INJECTION"
    ]

    result = validate_behavioral_gate(spec, registry)

    assert result["status"] == "FAIL"
    assert any("PROMPT_INJECTION" in error for error in result["errors"])
