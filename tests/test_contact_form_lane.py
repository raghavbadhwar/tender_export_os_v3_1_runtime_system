from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.validate_contact_form_lane import load_config, validate_contact_form_lane


def synthetic_approved_disabled_config(tmp_path: Path) -> dict:
    config = load_config()
    project_root = Path(__file__).resolve().parents[1]
    design_doc = "config/contact_form_connector_design.yaml"
    design_sha256 = hashlib.sha256((project_root / design_doc).read_bytes()).hexdigest()
    receipt_path = tmp_path / "approved_design.json"
    receipt_path.write_text(
        json.dumps(
            {
                "approval_id": "CFCD-TEST-001",
                "approved_at": "2099-01-01T00:00:00+00:00",
                "approved_by": "owner@example.test",
                "design_doc": design_doc,
                "design_sha256": design_sha256,
                "approved": True,
                "production_enabled": False,
                "external_actions_authorized": False,
                "form_submission_authorized": False,
            }
        ),
        encoding="utf-8",
    )
    config["status"] = "APPROVED_DESIGN_EXECUTION_DISABLED"
    config["approved_connector_design"] = {
        "approval_id": "CFCD-TEST-001",
        "approval_receipt": str(receipt_path),
        "design_doc": design_doc,
        "approved_at": "2099-01-01T00:00:00+00:00",
    }
    return config


def test_canonical_contact_form_lane_is_disabled_and_safe() -> None:
    config = load_config()
    result = validate_contact_form_lane(config)

    assert result["status"] == "PASS"
    assert result["production_enabled"] is False
    assert result["has_approved_design"] is False
    assert config["status"] == "DISABLED_PENDING_APPROVED_CONNECTOR_DESIGN"


def test_contact_form_lane_accepts_a_synthetic_approved_disabled_design(tmp_path: Path) -> None:
    result = validate_contact_form_lane(synthetic_approved_disabled_config(tmp_path))

    assert result["status"] == "PASS"
    assert result["production_enabled"] is False
    assert result["has_approved_design"] is True


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
    config = synthetic_approved_disabled_config(tmp_path)
    receipt_path = Path(config["approved_connector_design"]["approval_receipt"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["form_submission_authorized"] = True
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

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