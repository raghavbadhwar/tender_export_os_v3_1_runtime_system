import datetime as dt
from pathlib import Path

import yaml

from scripts.approval_lifecycle import classify_approval, timeout_hours
from scripts.generate_approval_cards import structured_card
from scripts.process_owner_decision import next_case_status


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_approval_policy_declares_timeout() -> None:
    policy = yaml.safe_load((PROJECT_ROOT / "config" / "approval_policy.yaml").read_text(encoding="utf-8"))
    assert timeout_hours(policy) == 48
    assert policy["approval_timeout_policy"]["on_timeout_status"] == "CHANGES_REQUESTED"


def test_supplier_quote_request_is_approval_gated() -> None:
    policy = yaml.safe_load((PROJECT_ROOT / "config" / "approval_policy.yaml").read_text(encoding="utf-8"))
    allowed = set(policy["mode_a_autopilot"]["allowed_actions"])
    gated = {item["action"] for item in policy["mode_b_approval_gated"]["approval_required_for"]}
    assert "send_supplier_quote_request" not in allowed
    assert "send_supplier_quote_request" in gated
    assert "send_buyer_introductory_outreach" in gated


def test_pending_approval_expires_after_timeout_window() -> None:
    created = "2026-06-30T00:00:00+00:00"
    now = dt.datetime.fromisoformat("2026-07-02T01:00:00+00:00")
    result = classify_approval({"approval_status": "PENDING", "created_at": created}, now=now, policy={"approval_timeout_policy": {"default_timeout_hours": 48}})
    assert result["expired"] is True
    assert result["state"] == "EXPIRED_APPROVAL"
    assert result["next_status"] == "CHANGES_REQUESTED"


def test_pending_approval_without_request_timestamp_is_not_silently_fresh() -> None:
    result = classify_approval(
        {"approval_status": "PENDING"},
        now=dt.datetime.fromisoformat("2026-07-02T01:00:00+00:00"),
        policy={"approval_timeout_policy": {"default_timeout_hours": 48}},
    )

    assert result["state"] == "PENDING_UNDATED"
    assert result["timeout_at"] == ""
    assert result["requires_reissue"] is True


def test_ask_changes_cli_spelling_moves_approval_required_case() -> None:
    assert next_case_status("APPROVAL_REQUIRED", "send_export_quotation", "ask-changes") == "CHANGES_REQUESTED"


def test_structured_approval_card_binds_scope_and_expiry() -> None:
    approval = {
        "approval_id": "APR-TEST-001",
        "case_id": "EXP-TEST-001",
        "workflow_type": "EXPORT",
        "action_approved": "send_export_quotation",
        "approval_status": "PENDING",
        "requested_at": "2026-07-12T06:00:00+00:00",
        "amount_usd": "500",
    }
    case = {"case_id": "EXP-TEST-001", "workflow_type": "EXPORT", "buyer_name": "Example Buyer"}

    card = structured_card(
        approval,
        case,
        PROJECT_ROOT / "receipts" / "approvals" / "card.html",
        PROJECT_ROOT / "receipts" / "approvals" / "card.json",
    )

    assert card["requested_at"] == "2026-07-12T06:00:00+00:00"
    assert card["approval_timeout_at"] == "2026-07-14T06:00:00+00:00"
    assert len(card["scope_hash"]) == 64
    assert card["scope"]["proposed_action"] == "send_export_quotation"
