from __future__ import annotations

from pathlib import Path

import yaml

from scripts.validate_owner_channel_delivery import validate_delivery


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "owner_channel_delivery.yaml"


def test_default_owner_channel_is_safe_and_not_configured() -> None:
    result = validate_delivery(CONFIG, ROOT / "config" / "hermes_cron.yaml")

    assert result["status"] == "READY_FOR_OWNER_SELECTION"
    assert result["enabled"] is False
    assert result["credential_values_present"] is False
    assert result["external_actions_executed"] is False
    assert "owner_channel_selection_required" in result["blockers"]
    assert "canary_receipt_required" in result["blockers"]
    assert result["cron_delivery_target"] == "local"


def test_enabled_channel_requires_owner_allowlist_and_canary(tmp_path: Path) -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    config["enabled"] = True
    config["platform"] = "telegram"
    config["credential_ref"] = "profile-secret:owner_channel_token"
    config_path = tmp_path / "owner_channel.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    result = validate_delivery(config_path, ROOT / "config" / "hermes_cron.yaml")

    assert result["status"] == "BLOCKED"
    assert "owner_allowlist_required" in result["blockers"]
    assert "canary_receipt_required" in result["blockers"]
    assert result["credential_values_present"] is False


def test_validator_rejects_inline_secret_and_external_business_actions(tmp_path: Path) -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    config.update(
        {
            "enabled": True,
            "platform": "ntfy",
            "credential_ref": "token-value-that-must-not-be-inline",
            "allowed_owner_ids": ["owner-1"],
            "canary_receipt": "receipts/mobile_delivery/canary.json",
            "external_business_actions_allowed": True,
        }
    )
    config_path = tmp_path / "owner_channel.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    result = validate_delivery(config_path, ROOT / "config" / "hermes_cron.yaml")

    assert result["status"] == "BLOCKED"
    assert "inline_credential_value_forbidden" in result["blockers"]
    assert "external_business_actions_must_remain_false" in result["blockers"]
    assert result["credential_values_present"] is False
