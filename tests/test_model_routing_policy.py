from __future__ import annotations

from pathlib import Path

import yaml

from scripts.model_routing_policy import choose_route, validate_policy


POLICY_PATH = Path("config/model_routing_policy.yaml")


def test_policy_passes_and_preserves_same_provider_fallback() -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    assert validate_policy(policy) == []
    assert policy["fallback"]["cross_provider"]["enabled"] is False
    assert policy["fallback"]["same_provider"]["model"] == "gpt-5.5"


def test_high_risk_work_uses_proven_model() -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    route = choose_route(policy, work_type="case_analysis", risk_tier="high")
    assert route["route"] == "high_reasoning"
    assert route["model"] == "gpt-5.6-terra"
    assert route["external_actions_executed"] is False


def test_low_risk_work_can_use_cheaper_same_provider_model() -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    route = choose_route(policy, work_type="bounded_classification", risk_tier="low")
    assert route["route"] == "low_risk_classification"
    assert route["model"] == "gpt-5.5"


def test_high_risk_work_cannot_be_forced_to_low_risk_route() -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    try:
        choose_route(policy, work_type="case_analysis", risk_tier="high", requested_route="low_risk_classification")
    except ValueError as exc:
        assert "high-risk" in str(exc) or "not allowed" in str(exc)
    else:
        raise AssertionError("high-risk work must not use low-risk route")


def test_invalid_cross_provider_fallback_is_rejected() -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    policy["fallback"]["cross_provider"]["enabled"] = True
    assert any("cross-provider" in error for error in validate_policy(policy))
