from __future__ import annotations

from scripts.validate_contact_form_connector_design import load_design, validate_design


def test_canonical_contact_form_connector_design_is_approval_ready_but_disabled() -> None:
    result = validate_design(load_design())

    assert result["status"] == "PASS"
    assert result["design_status"] == "DRAFT_APPROVAL_REQUIRED"
    assert result["production_enabled_by_this_design"] is False


def test_contact_form_connector_design_rejects_unsafe_flags() -> None:
    design = load_design()
    design["hard_stops"]["captcha_bypass_allowed"] = True
    design["hard_stops"]["payment_or_purchase_allowed"] = True

    result = validate_design(design)

    assert result["status"] == "FAIL"
    assert any("captcha_bypass_allowed" in error for error in result["errors"])
    assert any("payment_or_purchase_allowed" in error for error in result["errors"])


def test_contact_form_connector_design_rejects_fake_draft_approval() -> None:
    design = load_design()
    design["approval"]["approval_id"] = "APPROVED-WITHOUT-OWNER"

    result = validate_design(design)

    assert result["status"] == "FAIL"
    assert any("must not contain approval fields" in error for error in result["errors"])
