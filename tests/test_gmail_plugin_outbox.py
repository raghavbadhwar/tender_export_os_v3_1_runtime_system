from __future__ import annotations

import csv

import pytest

from scripts.generate_gmail_plugin_outbox import build_packet, eligibility, preflight_packet
from scripts import ingest_gmail_send_receipts as send_receipts
from scripts.ingest_gmail_send_receipts import validate_payload


def approved_outreach() -> tuple[dict, dict]:
    outreach = {
        "outreach_id": "OUT-1",
        "case_id": "EXP-1",
        "buyer_id": "BUY-1",
        "channel": "EMAIL",
        "verified_contact": "public@example.com",
        "subject": "Indian artisan homeware",
        "draft_path": "outputs/draft.md",
        "approval_id": "APR-1",
        "approval_status": "APPROVED",
        "send_status": "READY_AFTER_APPROVAL",
    }
    approval = {
        "approval_id": "APR-1",
        "case_id": "EXP-1",
        "action_approved": "send_buyer_introductory_outreach",
        "approval_status": "APPROVED",
        "receipt_path": "receipts/owner_decisions/APR-1.json",
        "scope_hash": "abc123",
    }
    return outreach, approval


def test_outbox_requires_approved_email_scope() -> None:
    outreach, approval = approved_outreach()
    assert eligibility(outreach, approval) == []
    outreach["approval_status"] = "PENDING"
    assert "outreach approval_status is not APPROVED" in eligibility(outreach, approval)
    outreach["approval_status"] = "APPROVED"
    outreach["channel"] = "CONTACT_FORM"
    assert "channel is not EMAIL" in eligibility(outreach, approval)


def test_outbox_packet_is_a_handoff_not_a_send() -> None:
    outreach, approval = approved_outreach()
    packet = build_packet(outreach, approval, body="Hello")
    assert packet["connector"] == "GMAIL_PLUGIN"
    assert packet["sender_account"] == "raghavbadhwar7@gmail.com"
    assert packet["send_authorized_by_owner"] is True
    assert packet["external_action_executed"] is False
    assert packet["recipient"] == "public@example.com"
    assert len(packet["content_sha256"]) == 64
    assert packet["attachments"] == []


def test_outbox_preflight_passes_only_exact_gmail_plugin_scope() -> None:
    outreach, approval = approved_outreach()
    packet = build_packet(outreach, approval, body="Hello")

    result = preflight_packet(packet, outreach=outreach, approval=approval, communication_rows=[])

    assert result["ok"] is True
    assert result["external_action_executed"] is False


def test_outbox_preflight_blocks_account_hash_and_ambiguous_connector_state() -> None:
    outreach, approval = approved_outreach()
    packet = build_packet(outreach, approval, body="Hello")
    packet["sender_account"] = "wrong@example.com"
    packet["content_sha256"] = "bad"

    result = preflight_packet(
        packet,
        outreach=outreach,
        approval=approval,
        communication_rows=[],
        connector_status="UNKNOWN",
    )

    assert result["ok"] is False
    assert "sender account mismatch" in result["blockers"]
    assert "content hash mismatch" in result["blockers"]
    assert "ambiguous or disconnected Gmail plugin state" in result["blockers"]


def test_outbox_preflight_blocks_prior_sent_receipts() -> None:
    outreach, approval = approved_outreach()
    packet = build_packet(outreach, approval, body="Hello")

    result = preflight_packet(
        packet,
        outreach=outreach,
        approval=approval | {"external_effect": "EXECUTED_AFTER_APPROVAL"},
        communication_rows=[],
    )
    replay = preflight_packet(
        packet,
        outreach=outreach,
        approval=approval,
        communication_rows=[{"outreach_id": "OUT-1", "source_connector": "GMAIL_PLUGIN"}],
    )

    assert result["ok"] is False
    assert replay["ok"] is False
    assert "prior sent receipt or executed approval exists" in result["blockers"]
    assert "prior sent receipt or executed approval exists" in replay["blockers"]


def test_send_receipts_accept_only_gmail_plugin() -> None:
    validate_payload({"connector": "GMAIL_PLUGIN", "sends": []})
    with pytest.raises(ValueError, match="GMAIL_PLUGIN"):
        validate_payload({"connector": "GWS", "sends": []})


def test_send_receipt_replay_keeps_one_immutable_communication(tmp_path, monkeypatch) -> None:
    def write_rows(name: str, headers: list[str], rows: list[dict[str, str]]) -> None:
        with (tmp_path / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    write_rows(
        "outreach_queue.csv",
        [
            "outreach_id", "case_id", "buyer_id", "approval_id", "draft_path",
            "subject", "send_status", "sent_at", "external_message_id",
            "external_thread_id", "updated_at", "stop_reason",
        ],
        [{
            "outreach_id": "OUT-1", "case_id": "EXP-1", "buyer_id": "BUY-1",
            "approval_id": "APR-1", "draft_path": "outputs/draft.md",
            "subject": "Hello", "send_status": "READY_AFTER_APPROVAL",
        }],
    )
    write_rows(
        "approvals_receipts.csv",
        ["approval_id", "case_id", "approval_status", "receipt_path", "external_effect", "notes"],
        [{
            "approval_id": "APR-1", "case_id": "EXP-1", "approval_status": "APPROVED",
            "receipt_path": "receipts/APR-1.json", "external_effect": "PENDING_APPROVED_EXECUTION",
        }],
    )
    write_rows(
        "master_cases.csv",
        ["case_id", "status", "submitted_at", "updated_at"],
        [{"case_id": "EXP-1", "status": "APPROVED"}],
    )
    write_rows(
        "buyer_demand_signals.csv",
        ["signal_id", "case_id", "next_safe_action", "updated_at"],
        [{"signal_id": "SIG-1", "case_id": "EXP-1", "next_safe_action": "DRAFT_OUTREACH_FOR_APPROVAL"}],
    )
    communication_headers = [
        "communication_id", "outreach_id", "case_id", "buyer_id", "direction",
        "channel", "external_message_id", "external_thread_id", "occurred_at",
        "subject", "content_path", "classification", "requires_owner_action",
        "recommended_next_action", "source_connector", "source_receipt", "created_at",
    ]
    write_rows("communication_log.csv", communication_headers, [])
    monkeypatch.setattr(send_receipts, "DATA_DIR", tmp_path)
    events: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        send_receipts,
        "event_for_row",
        lambda object_type, _object_id, _row, created, _citations, **_kwargs: events.append((object_type, created)),
    )
    payload = {
        "connector": "GMAIL_PLUGIN",
        "sends": [{
            "outreach_id": "OUT-1", "status": "SENT", "external_message_id": "msg-1",
            "external_thread_id": "thread-1", "sent_at": "2026-07-12T04:00:00+00:00",
        }],
    }
    receipt_path = tmp_path / "receipt.json"

    first = send_receipts.ingest(payload, input_path=receipt_path, persist=True)
    second = send_receipts.ingest(payload, input_path=receipt_path, persist=True)

    with (tmp_path / "communication_log.csv").open(newline="", encoding="utf-8") as handle:
        communications = list(csv.DictReader(handle))
    with (tmp_path / "approvals_receipts.csv").open(newline="", encoding="utf-8") as handle:
        approvals = list(csv.DictReader(handle))
    with (tmp_path / "master_cases.csv").open(newline="", encoding="utf-8") as handle:
        cases = list(csv.DictReader(handle))
    with (tmp_path / "buyer_demand_signals.csv").open(newline="", encoding="utf-8") as handle:
        signals = list(csv.DictReader(handle))
    assert len(communications) == 1
    assert approvals[0]["external_effect"] == "EXECUTED_AFTER_APPROVAL"
    assert cases[0]["status"] == "SENT_OR_SUBMITTED"
    assert cases[0]["submitted_at"] == "2026-07-12T04:00:00+00:00"
    assert signals[0]["next_safe_action"] == "AWAIT_BUYER_REPLY"
    assert first["duplicate_count"] == 0
    assert second["duplicate_count"] == 1
    assert events.count(("communication", True)) == 1
    assert ("communication", False) not in events
