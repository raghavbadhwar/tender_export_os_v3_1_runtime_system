#!/usr/bin/env python3
"""Validate owner-channel delivery readiness without reading or enabling credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "owner_channel_delivery.yaml"
DEFAULT_CRON = PROJECT_ROOT / "config" / "hermes_cron.yaml"
SUPPORTED_PLATFORMS = {"telegram", "ntfy", "slack", "discord", "email"}
REFERENCE_PREFIXES = ("profile-secret:", "keychain:")


def _load(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def _canary_status(config: dict[str, Any]) -> tuple[bool, str]:
    receipt_value = str(config.get("canary_receipt") or "").strip()
    if not receipt_value:
        return False, "canary_receipt_required"
    path = (PROJECT_ROOT / receipt_value).resolve()
    try:
        path.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return False, "canary_receipt_escapes_workspace"
    if not path.is_file():
        return False, "canary_receipt_missing"
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "canary_receipt_invalid"
    if not isinstance(receipt, dict) or receipt.get("status") != "PASS":
        return False, "canary_receipt_not_pass"
    return True, ""


def validate_delivery(config_path: Path = DEFAULT_CONFIG, cron_path: Path = DEFAULT_CRON) -> dict[str, Any]:
    config = _load(config_path)
    cron = _load(cron_path)
    blockers: list[str] = []
    enabled = bool(config.get("enabled", False))
    platform = str(config.get("platform") or "").strip().lower()
    credential_ref = str(config.get("credential_ref") or "").strip()
    allowed_owner_ids = config.get("allowed_owner_ids") or []

    cron_target = str(cron.get("owner_gateway") or "")
    if cron_target != "local":
        blockers.append("cron_owner_gateway_must_remain_local_until_canary")
    if cron.get("default_delivery_fallback") != "local_file":
        blockers.append("local_file_fallback_required")
    if cron.get("rules", {}).get("deliver_scheduled_briefs_to_telegram") is not False:
        blockers.append("scheduled_telegram_delivery_must_remain_disabled")
    if config.get("owner_only_delivery") is not True:
        blockers.append("owner_only_delivery_required")
    if config.get("local_fallback") is not True:
        blockers.append("local_fallback_required")
    if config.get("external_business_actions_allowed") is not False:
        blockers.append("external_business_actions_must_remain_false")
    if config.get("external_actions_executed") is not False:
        blockers.append("external_actions_executed_must_remain_false")

    credential_values_present = False
    if credential_ref and not credential_ref.startswith(REFERENCE_PREFIXES):
        blockers.append("inline_credential_value_forbidden")
    if enabled:
        if platform not in SUPPORTED_PLATFORMS:
            blockers.append("supported_owner_channel_platform_required")
        if not credential_ref:
            blockers.append("profile_local_credential_reference_required")
        if not isinstance(allowed_owner_ids, list) or not allowed_owner_ids:
            blockers.append("owner_allowlist_required")
        if not str(config.get("approval_interaction") or "") == "approve_reject_ask_changes":
            blockers.append("typed_approval_interaction_required")
        _, canary_blocker = _canary_status(config)
        if canary_blocker:
            blockers.append(canary_blocker)
    else:
        blockers.extend(["owner_channel_selection_required", "canary_receipt_required"])

    if not enabled and credential_ref:
        blockers.append("disabled_channel_must_not_have_credential_ref")

    status = "READY_FOR_OWNER_SELECTION" if not enabled and not any(
        item in blockers
        for item in (
            "cron_owner_gateway_must_remain_local_until_canary",
            "local_file_fallback_required",
            "scheduled_telegram_delivery_must_remain_disabled",
            "owner_only_delivery_required",
            "local_fallback_required",
            "external_business_actions_must_remain_false",
            "external_actions_executed_must_remain_false",
        )
    ) else ("PASS" if enabled and not blockers else "BLOCKED")
    return {
        "schema_version": "owner_channel_delivery.v1",
        "status": status,
        "enabled": enabled,
        "platform_configured": bool(platform),
        "platform": platform if platform in SUPPORTED_PLATFORMS else "",
        "credential_reference_configured": bool(credential_ref),
        "credential_reference_kind": "profile_local_secret_reference" if credential_ref.startswith(REFERENCE_PREFIXES) else "",
        "credential_values_present": credential_values_present,
        "allowed_owner_count": len(allowed_owner_ids) if isinstance(allowed_owner_ids, list) else 0,
        "cron_delivery_target": cron_target,
        "blockers": sorted(set(blockers)),
        "local_fallback": config.get("local_fallback") is True,
        "owner_only_delivery": config.get("owner_only_delivery") is True,
        "external_actions_executed": False,
        "safety_note": "Credentialless validation only. No .env, token, gateway send, or external message was read or attempted.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--cron", default=str(DEFAULT_CRON))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_delivery(Path(args.config).expanduser(), Path(args.cron).expanduser())
    print(json.dumps(result, indent=2) if args.json else f"Owner channel delivery {result['status']}")
    return 0 if result["status"] in {"READY_FOR_OWNER_SELECTION", "PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
