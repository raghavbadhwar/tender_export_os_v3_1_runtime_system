from __future__ import annotations

import json
from pathlib import Path

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


def test_contact_form_lane_requires_a_verifiable_approval_receipt() -> None:
    config = load_config()
    config["status"] = "APPROVED_DESIGN_EXECUTION_DISABLED"
    config["approved_connector_design"] = {
        "approval_id": "CFCD-1",
        "design_doc": "config/contact_form_connector_design.yaml",
        "approved_at": "2026-07-13T00:00:00+00:00",
    }

    result = validate_contact_form_lane(config)

    assert result["status"] == "FAIL"
    assert "approved_connector_design approval_receipt is missing" in result["errors"]


def test_contact_form_lane_rejects_tampered_approval_receipt(tmp_path) -> None:
    config = load_config()
    project_root = Path(__file__).resolve().parents[1]
    source_receipt = project_root / config["approved_connector_design"]["approval_receipt"]
    receipt = json.loads(source_receipt.read_text(encoding="utf-8"))
    receipt["form_submission_authorized"] = True
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    config["approved_connector_design"]["approval_receipt"] = str(receipt_path)

    result = validate_contact_form_lane(config)

    assert result["status"] == "FAIL"
    assert "approved_connector_design approval_receipt must not authorize external actions" in result["errors"]


def test_contact_form_lane_rejects_unrestricted_or_captcha_bypass_flags() -> None:
    config = load_config()
    config["runtime_boundaries"]["unrestricted_form_automation_allowed"] = True
    config["runtime_boundaries"]["captcha_bypass_allowed"] = True

    result = validate_contact_form_lane(config)

    assert result["status"] == "FAIL"
    assert any("unrestricted_form_automation_allowed" in error for error in result["errors"])
    assert any("captcha_bypass_allowed" in error for error in result["errors"])
