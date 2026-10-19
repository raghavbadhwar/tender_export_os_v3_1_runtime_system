from __future__ import annotations

from scripts.validate_infrastructure_scale_gates import load_config, validate_scale_gates


def test_canonical_infrastructure_scale_gates_are_valid() -> None:
    result = validate_scale_gates(load_config())

    assert result["status"] == "PASS"
    assert result["gate_count"] == 5


def test_scale_gate_requires_owner_approval_and_off_by_default() -> None:
    config = load_config()
    config["owner_approval_required"] = False
    config["gates"]["postgres"]["current_state"] = "ON"

    result = validate_scale_gates(config)

    assert result["status"] == "FAIL"
    assert any("owner_approval_required" in error for error in result["errors"])
    assert any("postgres.current_state" in error for error in result["errors"])


def test_scale_gate_requires_measured_trigger_fields() -> None:
    config = load_config()
    config["gates"]["temporal"]["adopt_only_after"] = [{"metric": "workflow_volume_per_day"}]

    result = validate_scale_gates(config)

    assert result["status"] == "FAIL"
    assert any("threshold" in error for error in result["errors"])
    assert any("window" in error for error in result["errors"])
