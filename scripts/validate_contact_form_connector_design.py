#!/usr/bin/env python3
"""Validate the draft contact-form connector design packet without enabling it."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DESIGN = PROJECT_ROOT / "config" / "contact_form_connector_design.yaml"

REQUIRED_INPUTS = {
    "case_id",
    "approval_id",
    "approval_receipt",
    "recipient_organization",
    "official_contact_form_url",
    "domain_allowlist_match",
    "exact_form_field_map",
    "message_subject",
    "message_body",
    "content_sha256",
    "idempotency_key",
}

REQUIRED_RUNTIME_CONTROLS = {
    "domain_allowlist_required",
    "exact_form_field_map_required",
    "screenshot_receipt_required",
    "html_receipt_required",
    "content_hash_required",
    "idempotency_key_required",
    "anti_csrf_session_handling_required",
    "human_captcha_stop_required",
    "post_submit_confirmation_required",
    "owner_approval_receipt_required",
    "prior_receipt_duplicate_check_required",
}

FORBIDDEN_TRUE_FLAGS = {
    "unrestricted_form_automation_allowed",
    "captcha_bypass_allowed",
    "credential_capture_allowed",
    "login_required_forms_allowed",
    "payment_or_purchase_allowed",
    "portal_upload_allowed",
    "tender_bid_submit_allowed",
    "final_quote_or_commitment_allowed",
    "public_service_exposure_allowed",
}


def load_design(path: Path = DEFAULT_DESIGN) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def validate_design(design: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if design.get("status") != "DRAFT_APPROVAL_REQUIRED":
        errors.append("status must remain DRAFT_APPROVAL_REQUIRED until owner approval is recorded")
    if design.get("production_enabled_by_this_design") is not False:
        errors.append("production_enabled_by_this_design must be false")

    approval = design.get("approval") if isinstance(design.get("approval"), dict) else {}
    if any(approval.get(field) for field in ("approval_id", "approved_at", "approved_by")):
        errors.append("draft design must not contain approval fields before owner approval")

    scope = design.get("scope") if isinstance(design.get("scope"), dict) else {}
    if scope.get("case_scoped_only") is not True:
        errors.append("scope.case_scoped_only must be true")
    if scope.get("one_submission_per_approval") is not True:
        errors.append("scope.one_submission_per_approval must be true")

    inputs = set(design.get("required_inputs_per_submission") or [])
    missing_inputs = sorted(REQUIRED_INPUTS - inputs)
    if missing_inputs:
        errors.append(f"missing required inputs: {', '.join(missing_inputs)}")

    controls = design.get("runtime_controls") if isinstance(design.get("runtime_controls"), dict) else {}
    for key in sorted(REQUIRED_RUNTIME_CONTROLS):
        if controls.get(key) is not True:
            errors.append(f"runtime_controls.{key} must be true")

    hard_stops = design.get("hard_stops") if isinstance(design.get("hard_stops"), dict) else {}
    for key in sorted(FORBIDDEN_TRUE_FLAGS):
        if hard_stops.get(key) is not False:
            errors.append(f"hard_stops.{key} must be false")

    receipt = design.get("receipt_contract") if isinstance(design.get("receipt_contract"), dict) else {}
    required_receipt_fields = set(receipt.get("required_receipt_fields") or [])
    for field in ("case_id", "approval_id", "submitted_content_sha256", "idempotency_key", "screenshot_path", "html_path", "external_action_executed"):
        if field not in required_receipt_fields:
            errors.append(f"receipt_contract.required_receipt_fields missing {field}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "design_status": design.get("status"),
        "production_enabled_by_this_design": design.get("production_enabled_by_this_design"),
        "required_inputs_count": len(inputs),
        "runtime_control_count": len(controls),
        "hard_stop_count": len(hard_stops),
        "safety_note": "Design validation only. No browser is opened and no form is submitted.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", default=str(DEFAULT_DESIGN))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_design(load_design(Path(args.design).expanduser()))
    print(json.dumps(result, indent=2) if args.json else f"Contact-form connector design {result['status']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
