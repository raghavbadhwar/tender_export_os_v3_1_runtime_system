from __future__ import annotations

import copy

from scripts.validate_trajectory_policy import load_policy, validate_policy


def test_trajectory_policy_is_privacy_controlled_and_rl_disabled() -> None:
    policy = load_policy()

    assert validate_policy(policy) == []
    assert policy["rl_training"]["enabled"] is False
    assert policy["retention"]["raw_sensitive_content_retention_days"] == 0


def test_trajectory_policy_rejects_sensitive_field_capture() -> None:
    policy = copy.deepcopy(load_policy())
    policy["trajectory_capture"]["allowed_fields"].append("email_body")

    errors = validate_policy(policy)

    assert any("overlap" in error for error in errors)


def test_trajectory_policy_rejects_enabled_rl_without_design_gate() -> None:
    policy = copy.deepcopy(load_policy())
    policy["rl_training"]["enabled"] = True

    errors = validate_policy(policy)

    assert any("rl_training.enabled must remain false" in error for error in errors)
