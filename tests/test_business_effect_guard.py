from __future__ import annotations

import json
from pathlib import Path

from scripts.business_effect_guard import classify_decision, guard_business_effect
from scripts.tender_os_policy import DEFAULT_CONFIG, DEFAULT_REGO, TenderPolicyEngine


def test_decision_statuses_are_normalized() -> None:
    assert classify_decision({"allow": True}) == "allowed"
    assert (
        classify_decision({"allow": False, "reason_code": "APPROVAL_REQUIRED"})
        == "blocked_missing_approval"
    )
    assert (
        classify_decision(
            {"allow": False, "reason_code": "POLICY_ENGINE_UNAVAILABLE"}
        )
        == "failed"
    )


def test_internal_preparation_is_allowed_and_receipted(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    engine = TenderPolicyEngine(
        config_path=DEFAULT_CONFIG,
        rego_path=DEFAULT_REGO,
        receipt_root=tmp_path / "policy",
        events_file=events,
    )
    result = guard_business_effect(
        "mcp.get_case",
        engine=engine,
        receipt_root=tmp_path / "attempts",
    )
    assert result["status"] == "allowed"
    assert result["external_action_executed"] is False
    assert Path(result["receipt_path"]).is_file()


def test_external_action_without_approval_is_blocked_and_sanitized(
    tmp_path: Path,
) -> None:
    events = tmp_path / "events.jsonl"
    engine = TenderPolicyEngine(
        config_path=DEFAULT_CONFIG,
        rego_path=DEFAULT_REGO,
        receipt_root=tmp_path / "policy",
        events_file=events,
    )
    result = guard_business_effect(
        "send_buyer_introductory_outreach",
        case_id="EXP-NOT-FOUND",
        engine=engine,
        receipt_root=tmp_path / "attempts",
    )
    assert result["status"] == "blocked_missing_approval"
    receipt = json.loads(Path(result["receipt_path"]).read_text(encoding="utf-8"))
    assert receipt["external_action_executed"] is False
    assert "payload" not in receipt
    assert "credentials" not in receipt
    assert "raw_payload" not in receipt
