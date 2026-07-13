from __future__ import annotations

from scripts.validate_contact_form_lane import load_config, validate_contact_form_lane


def test_canonical_contact_form_lane_is_disabled_and_safe() -> None:
    config = load_config()
    result = validate_contact_form_lane(config)

    assert result["status"] == "PASS"
    assert result["production_enabled"] is False
    assert result["has_approved_design"] is True
    assert config["status"] == "APPROVED_DESIGN_EXECUTION_DISABLED"


def test_contact_form_lane_cannot_enable_without_approved_design_and_maps() -> None:
    config = load_config()
    config["production_enabled"] = True
    config["status"] = "ENABLED"
    config["approved_connector_design"] = {
        "approval_id": "",
        "design_doc": "",
        "approved_at": "",
    }

    result = validate_contact_form_lane(config)

    assert result["status"] == "FAIL"
    assert any("approved_connector_design" in error for error in result["errors"])
    assert any("domain_allowlist" in error for error in result["errors"])
    assert any("form_field_maps" in error for error in result["errors"])


def test_contact_form_lane_allows_approved_design_while_execution_disabled() -> None:
    config = load_config()
    config["status"] = "APPROVED_DESIGN_EXECUTION_DISABLED"
    config["approved_connector_design"] = {
        "approval_id": "CFCD-1",
        "design_doc": "config/contact_form_connector_design.yaml",
        "approved_at": "2026-07-13T00:00:00+00:00",
    }

    result = validate_contact_form_lane(config)

    assert result["status"] == "PASS"
    assert result["production_enabled"] is False
    assert result["has_approved_design"] is True


def test_contact_form_lane_rejects_unrestricted_or_captcha_bypass_flags() -> None:
    config = load_config()
    config["runtime_boundaries"]["unrestricted_form_automation_allowed"] = True
    config["runtime_boundaries"]["captcha_bypass_allowed"] = True

    result = validate_contact_form_lane(config)

    assert result["status"] == "FAIL"
    assert any("unrestricted_form_automation_allowed" in error for error in result["errors"])
    assert any("captcha_bypass_allowed" in error for error in result["errors"])
