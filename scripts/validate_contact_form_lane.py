#!/usr/bin/env python3
"""Validate that contact-form automation remains disabled until an approved design exists."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "contact_form_lane.yaml"
REQUIRED_CONTROLS = {
    "domain_allowlist",
    "exact_form_field_map",
    "screenshot_receipt",
    "html_receipt",
    "content_sha256",
    "idempotency_key",
    "anti_csrf_session_handling",
    "human_captcha_stop",
    "post_submit_confirmation",
    "owner_approval_receipt",
}


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def _resolve_path(value: str, *, project_root: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else project_root / path


def _approval_receipt_errors(approved_design: dict[str, Any], *, project_root: Path) -> list[str]:
    receipt_value = str(approved_design.get("approval_receipt") or "")
    if not receipt_value:
        return ["approved_connector_design approval_receipt is missing"]
    receipt_path = _resolve_path(receipt_value, project_root=project_root)
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["approved_connector_design approval_receipt is missing or unreadable"]
    if not isinstance(receipt, dict):
        return ["approved_connector_design approval_receipt is not an object"]
    errors: list[str] = []
    for field in ("approval_id", "approved_at", "design_doc"):
        if receipt.get(field) != approved_design.get(field):
            errors.append(f"approved_connector_design approval_receipt {field} mismatch")
    if receipt.get("approved") is not True or not receipt.get("approved_by"):
        errors.append("approved_connector_design approval_receipt is not owner-approved")
    if receipt.get("production_enabled") is not False:
        errors.append("approved_connector_design approval_receipt must keep production disabled")
    if receipt.get("external_actions_authorized") is not False or receipt.get("form_submission_authorized") is not False:
        errors.append("approved_connector_design approval_receipt must not authorize external actions")
    design_path = _resolve_path(str(approved_design.get("design_doc") or ""), project_root=project_root)
    try:
        design_sha256 = hashlib.sha256(design_path.read_bytes()).hexdigest()
    except OSError:
        errors.append("approved_connector_design design_doc is missing or unreadable")
    else:
        if receipt.get("design_sha256") != design_sha256:
            errors.append("approved_connector_design approval_receipt design hash mismatch")
    return errors


def validate_contact_form_lane(config: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    controls = set(config.get("required_controls_before_enable") or [])
    missing_controls = sorted(REQUIRED_CONTROLS - controls)
    if missing_controls:
        errors.append(f"missing required controls: {', '.join(missing_controls)}")

    boundaries = config.get("runtime_boundaries") if isinstance(config.get("runtime_boundaries"), dict) else {}
    for key in (
        "unrestricted_form_automation_allowed",
        "captcha_bypass_allowed",
        "credential_capture_allowed",
        "payment_or_purchase_allowed",
        "final_quote_or_commitment_allowed",
        "public_service_exposure_allowed",
    ):
        if boundaries.get(key) is not False:
            errors.append(f"runtime_boundaries.{key} must be false")

    production_enabled = config.get("production_enabled") is True
    approved_design = config.get("approved_connector_design") if isinstance(config.get("approved_connector_design"), dict) else {}
    approval_fields = ("approval_id", "approval_receipt", "design_doc", "approved_at")
    has_approved_design = all(approved_design.get(field) for field in approval_fields)
    if approved_design:
        errors.extend(_approval_receipt_errors(approved_design, project_root=PROJECT_ROOT))
    if not production_enabled:
        if has_approved_design:
            if config.get("status") != "APPROVED_DESIGN_EXECUTION_DISABLED":
                errors.append("approved disabled lane status must be APPROVED_DESIGN_EXECUTION_DISABLED")
        elif config.get("status") != "DISABLED_PENDING_APPROVED_CONNECTOR_DESIGN":
            errors.append("unapproved disabled lane status must be DISABLED_PENDING_APPROVED_CONNECTOR_DESIGN")
    else:
        if not has_approved_design:
            errors.append("production_enabled requires approved_connector_design approval_id, approval_receipt, design_doc, and approved_at")
        if not config.get("domain_allowlist"):
            errors.append("production_enabled requires non-empty domain_allowlist")
        if not config.get("form_field_maps"):
            errors.append("production_enabled requires exact form_field_maps")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "production_enabled": production_enabled,
        "has_approved_design": has_approved_design,
        "required_controls": sorted(REQUIRED_CONTROLS),
        "safety_note": "Validation only; no form is opened or submitted.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = validate_contact_form_lane(load_config(Path(args.config).expanduser()))
    print(json.dumps(result, indent=2) if args.json else f"Contact-form lane {result['status']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
