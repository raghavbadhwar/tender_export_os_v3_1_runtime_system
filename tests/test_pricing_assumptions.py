from __future__ import annotations

from scripts.pricing_assumptions import (
    load_assumptions,
    validate_assumption_config,
    validate_assumption_reference,
)


def test_pricing_assumption_registry_is_valid_for_current_rollout() -> None:
    errors = validate_assumption_config(load_assumptions(), as_of="2026-07-13")

    assert errors == []


def test_assumption_reference_rejects_missing_or_expired_assumption() -> None:
    config = load_assumptions()

    missing = validate_assumption_reference(
        assumption_id="MISSING",
        workflow_type="GOV",
        component_key="freight",
        amount=10,
        as_of="2026-07-13",
        config=config,
    )
    expired = validate_assumption_reference(
        assumption_id="GOV-FREIGHT-2026Q3",
        workflow_type="GOV",
        component_key="freight",
        amount=10,
        as_of="2026-12-01",
        config=config,
    )

    assert any("does not reference" in error for error in missing)
    assert any("expired on" in error for error in expired)


def test_zero_amount_requires_assumption_zero_reason() -> None:
    config = {
        "required_fields": load_assumptions()["required_fields"],
        "allowed_statuses": ["ACTIVE"],
        "allowed_workflows": ["EXPORT"],
        "assumptions": [
            {
                "assumption_id": "EXPORT-ZERO",
                "workflow_type": "EXPORT",
                "component_key": "insurance",
                "source": "fixture",
                "observed_date": "2026-07-13",
                "expiry_date": "2026-10-13",
                "currency": "USD",
                "tax_treatment": "fixture",
                "default_value": 0,
                "conservative_value": 0,
                "responsible_profile": "pricing-risk",
                "status": "ACTIVE",
            }
        ],
    }

    errors = validate_assumption_config(config, as_of="2026-07-13")

    assert any("zero_value_reason is required" in error for error in errors)

