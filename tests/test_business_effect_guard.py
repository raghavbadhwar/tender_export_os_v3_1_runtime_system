from __future__ import annotations

import json
from pathlib import Path

from scripts.business_effect_guard import classify_decision, guard_business_effect
from scripts.tender_os_policy import SingleUseApprovalStore
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



def test_approval_claim_is_single_use_and_intent_drift_is_blocked(tmp_path: Path) -> None:
    class FakeEngine:
        events_file = tmp_path / "events.jsonl"

        def evaluate(self, action: str, **kwargs: object) -> dict:
            return {
                "allow": True,
                "approval_required": True,
                "action": action,
                "decision_id": "POL-TEST",
                "reason_code": "SCOPED_APPROVAL_VERIFIED",
                "approval": {"receipt_id": "ODR-1", "scope_hash": "scope-1"},
                "receipt_path": "receipts/policy/ODR-1.json",
            }

    first = guard_business_effect(
        "send_buyer_rfq_reply",
        case_id="CASE-1",
        approval_id="APR-1",
        engine=FakeEngine(),
        receipt_root=tmp_path / "attempts",
        record_event=False,
        intent={"body_sha256": "a" * 64},
    )
    replay = guard_business_effect(
        "send_buyer_rfq_reply",
        case_id="CASE-1",
        approval_id="APR-1",
        engine=FakeEngine(),
        receipt_root=tmp_path / "attempts",
        record_event=False,
        intent={"body_sha256": "a" * 64},
    )
    drift = guard_business_effect(
        "send_buyer_rfq_reply",
        case_id="CASE-1",
        approval_id="APR-1",
        engine=FakeEngine(),
        receipt_root=tmp_path / "attempts",
        record_event=False,
        intent={"body_sha256": "b" * 64},
    )
    assert first["status"] == "allowed"
    assert replay["status"] == "blocked_replay"
    assert drift["status"] == "blocked_intent_drift"
    assert first["external_action_executed"] is False


def test_concurrent_claims_have_at_most_one_success(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    store = SingleUseApprovalStore(tmp_path / "claims.sqlite3")

    def claim(_: int) -> bool:
        return store.claim(
            approval_id="APR-CONCURRENT",
            intent_hash="i" * 64,
            scope_hash="s" * 64,
            claimed_at="2026-07-12T06:00:00+00:00",
        )["claimed"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(claim, range(8)))
    assert sum(outcomes) == 1
