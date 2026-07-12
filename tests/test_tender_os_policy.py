from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

import pytest
import yaml

from scripts.tender_os_policy import DEFAULT_CONFIG, DEFAULT_REGO, TenderPolicyEngine


NOW = dt.datetime(2026, 7, 12, 6, 0, tzinfo=dt.timezone.utc)


def build_approval_engine(
    tmp_path: Path,
    *,
    action: str = "send_buyer_introductory_outreach",
    external_effect: str = "PENDING_APPROVED_EXECUTION",
    timeout: dt.datetime | None = None,
    row_scope_hash: str = "scope-123",
    card_scope_hash: str = "scope-123",
    controls: dict[str, bool] | None = None,
) -> TenderPolicyEngine:
    (tmp_path / "data").mkdir()
    (tmp_path / "receipts" / "approvals").mkdir(parents=True)
    (tmp_path / "receipts" / "owner_decisions").mkdir(parents=True)
    approval_id = "APR-TEST-001"
    case_id = "EXP-TEST-001"
    card_html = "receipts/approvals/EXP-TEST-001_approval_card.html"
    card_json = tmp_path / "receipts" / "approvals" / "EXP-TEST-001_approval_card.json"
    owner_receipt = "receipts/owner_decisions/EXP-TEST-001_APR-TEST-001.json"
    expiry = timeout or (NOW + dt.timedelta(hours=24))
    row = {
        "approval_id": approval_id,
        "case_id": case_id,
        "workflow_type": "EXPORT",
        "action_approved": action,
        "proposed_by_agent": "test",
        "approval_card_path": card_html,
        "approved_by": "Raghav",
        "approved_at": (NOW - dt.timedelta(hours=1)).isoformat(),
        "approval_status": "APPROVED",
        "receipt_id": "ODR-TEST-001",
        "receipt_path": owner_receipt,
        "external_effect": external_effect,
        "requested_at": (NOW - dt.timedelta(hours=2)).isoformat(),
        "approval_timeout_at": expiry.isoformat(),
        "scope_hash": row_scope_hash,
    }
    approvals = tmp_path / "data" / "approvals_receipts.csv"
    with approvals.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    card_json.write_text(
        json.dumps(
            {
                "approval_id": approval_id,
                "case_id": case_id,
                "proposed_action": action,
                "scope_hash": card_scope_hash,
                "approval_timeout_at": expiry.isoformat(),
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / owner_receipt).write_text(
        json.dumps(
            {
                "receipt_id": "ODR-TEST-001",
                "approval_id": approval_id,
                "case_id": case_id,
                "decision_status": "APPROVED",
                "action_approved": action,
                "external_effect": external_effect,
                "controls": controls or {},
            }
        ),
        encoding="utf-8",
    )
    return TenderPolicyEngine(
        config_path=DEFAULT_CONFIG,
        rego_path=DEFAULT_REGO,
        approvals_path=approvals,
        receipt_root=tmp_path / "receipts" / "policy_decisions",
        events_file=tmp_path / "data" / "events.jsonl",
        project_root=tmp_path,
        clock=lambda: NOW,
    )


def test_t0_internal_action_is_allowed() -> None:
    decision = TenderPolicyEngine(clock=lambda: NOW).evaluate("mcp.get_case")
    assert decision["allow"] is True
    assert decision["reason_code"] == "LOW_RISK_INTERNAL_ACTION"
    assert decision["tier"] == 0


@pytest.mark.parametrize("action", ["captcha_bypass", "otp_bypass", "unknown_action"])
def test_prohibited_or_unknown_action_is_fail_closed(action: str) -> None:
    decision = TenderPolicyEngine(clock=lambda: NOW).evaluate(action)
    assert decision["allow"] is False
    assert decision["reason_code"] == "PROHIBITED_ACTION"


def test_unapproved_external_action_requires_real_local_receipt() -> None:
    decision = TenderPolicyEngine(clock=lambda: NOW).evaluate(
        "send_buyer_introductory_outreach", case_id="EXP-NOT-FOUND"
    )
    assert decision["allow"] is False
    assert decision["status"] == "approval_required"
    assert "no matching local approval" in decision["reason"]


def test_opa_action_registry_covers_every_canonical_approval_gate() -> None:
    approval_policy = yaml.safe_load(
        (DEFAULT_CONFIG.parent / "approval_policy.yaml").read_text(encoding="utf-8")
    )
    tool_policy = yaml.safe_load(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    required = set(
        approval_policy["standing_authorizations"][
            "hard_limits_still_requiring_specific_owner_approval"
        ]
    )
    required.update(
        item["action"]
        for item in approval_policy["mode_b_approval_gated"]["approval_required_for"]
    )
    actions = tool_policy["actions"]
    assert required <= set(actions)
    for action in required:
        assert actions[action]["approval_required"] is True
        assert actions[action]["tier"] >= 3


def test_valid_scoped_t4_approval_can_be_verified(tmp_path: Path) -> None:
    engine = build_approval_engine(tmp_path)
    decision = engine.evaluate(
        "send_buyer_introductory_outreach",
        case_id="EXP-TEST-001",
        approval_id="APR-TEST-001",
    )
    assert decision["allow"] is True
    assert decision["reason_code"] == "SCOPED_APPROVAL_VERIFIED"
    assert decision["approval"]["receipt_id"] == "ODR-TEST-001"


def test_consumed_approval_cannot_be_reused(tmp_path: Path) -> None:
    engine = build_approval_engine(tmp_path, external_effect="EXECUTED_AFTER_APPROVAL")
    decision = engine.evaluate(
        "send_buyer_introductory_outreach",
        case_id="EXP-TEST-001",
        approval_id="APR-TEST-001",
    )
    assert decision["allow"] is False
    assert "already executed" in decision["reason"]


def test_scope_hash_mismatch_is_blocked(tmp_path: Path) -> None:
    engine = build_approval_engine(tmp_path, card_scope_hash="different")
    decision = engine.evaluate(
        "send_buyer_introductory_outreach",
        case_id="EXP-TEST-001",
        approval_id="APR-TEST-001",
    )
    assert decision["allow"] is False
    assert "scope hash" in decision["reason"]


def test_expired_approval_is_blocked(tmp_path: Path) -> None:
    engine = build_approval_engine(tmp_path, timeout=NOW - dt.timedelta(seconds=1))
    decision = engine.evaluate(
        "send_buyer_introductory_outreach",
        case_id="EXP-TEST-001",
        approval_id="APR-TEST-001",
    )
    assert decision["allow"] is False
    assert "expired" in decision["reason"]


def test_t5_requires_explicit_special_controls(tmp_path: Path) -> None:
    blocked_engine = build_approval_engine(tmp_path, action="submit_tender_bid")
    blocked = blocked_engine.evaluate(
        "submit_tender_bid", case_id="EXP-TEST-001", approval_id="APR-TEST-001"
    )
    assert blocked["allow"] is False
    assert blocked["reason_code"] == "REQUIRED_CONTROLS_MISSING"
    assert set(blocked["required_controls"]["missing"]) == {"fresh_owner_command", "dsc_owner_present"}


def test_t5_can_only_unlock_when_receipt_contains_all_controls(tmp_path: Path) -> None:
    engine = build_approval_engine(
        tmp_path,
        action="submit_tender_bid",
        controls={"fresh_owner_command": True, "dsc_owner_present": True},
    )
    decision = engine.evaluate(
        "submit_tender_bid", case_id="EXP-TEST-001", approval_id="APR-TEST-001"
    )
    assert decision["allow"] is True


def test_missing_opa_fails_closed() -> None:
    engine = TenderPolicyEngine(opa_binary="/definitely/missing/opa", clock=lambda: NOW)
    decision = engine.evaluate("mcp.get_case")
    assert decision["allow"] is False
    assert decision["reason_code"] == "POLICY_ENGINE_UNAVAILABLE"


def test_recorded_decision_writes_receipt_and_canonical_event(tmp_path: Path) -> None:
    engine = TenderPolicyEngine(
        receipt_root=tmp_path / "receipts",
        events_file=tmp_path / "events.jsonl",
        clock=lambda: NOW,
    )
    decision = engine.evaluate("mcp.get_case", record=True)
    assert decision["allow"] is True
    assert (tmp_path / "receipts" / f"{decision['decision_id']}.json").is_file()
    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8").strip())
    assert event["event_type"] == "policy.decision_recorded"
    assert event["payload"]["decision_id"] == decision["decision_id"]
    assert event["payload"]["allowed"] is True
