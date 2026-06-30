import datetime as dt
from pathlib import Path

import yaml

from scripts.approval_lifecycle import classify_approval, timeout_hours


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


def test_pending_approval_expires_after_timeout_window() -> None:
    created = "2026-06-30T00:00:00+00:00"
    now = dt.datetime.fromisoformat("2026-07-02T01:00:00+00:00")
    result = classify_approval({"approval_status": "PENDING", "created_at": created}, now=now, policy={"approval_timeout_policy": {"default_timeout_hours": 48}})
    assert result["expired"] is True
    assert result["state"] == "EXPIRED_APPROVAL"
    assert result["next_status"] == "CHANGES_REQUESTED"
