from __future__ import annotations

import pytest

import json

from scripts.ingest_buyer_replies import classify_reply, resolve_outreach, validate_connector_payload, write_owner_action_card


def test_connector_contract_accepts_only_gmail_plugin() -> None:
    validate_connector_payload({"connector": "GMAIL_PLUGIN", "messages": []})
    with pytest.raises(ValueError, match="GMAIL_PLUGIN"):
        validate_connector_payload({"connector": "GWS", "messages": []})
    with pytest.raises(ValueError, match="messages"):
        validate_connector_payload({"connector": "GMAIL_PLUGIN"})


def test_reply_classification_stops_negative_replies_and_routes_rfq_to_owner() -> None:
    assert classify_reply("Please unsubscribe us")["classification"] == "OPT_OUT"
    assert classify_reply("We are not interested")["classification"] == "NOT_INTERESTED"
    rfq = classify_reply("Please send an RFQ response for the attached requirements")
    assert rfq["classification"] == "RFQ"
    assert rfq["requires_owner_action"] is True


def test_owner_action_card_keeps_raw_reply_content_out_of_the_card(tmp_path) -> None:
    path = tmp_path / "owner_action.json"
    write_owner_action_card(
        {
            "communication_id": "COM-1",
            "case_id": "EXP-1",
            "buyer_id": "BUY-1",
            "classification": "RFQ",
            "recommended_next_action": "Verify RFQ.",
            "source_receipt": "receipts/reply.json",
            "content_path": "receipts/private_reply.txt",
        },
        path=path,
    )

    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["content_path"] == "receipts/private_reply.txt"
    assert "raw reply" in value["privacy_note"].lower()


@pytest.mark.parametrize(
    ("text", "expected", "owner_action"),
    [
        ("Please remove us from your list and do not contact again.", "OPT_OUT", False),
        ("Delivery Status Notification: address not found", "BOUNCE", False),
        ("Automatic reply: I am out of office", "AUTO_REPLY", False),
        ("Thanks, please send the catalogue and MOQ details.", "SUBSTANTIVE", True),
        ("Can you quote FOB and advise payment terms?", "SUBSTANTIVE", True),
        ("Who produces these items?", "QUESTION", True),
        ("Thank you for writing.", "UNKNOWN", True),
    ],
)
def test_reply_classification(text: str, expected: str, owner_action: bool) -> None:
    result = classify_reply(text)
    assert result["classification"] == expected
    assert result["requires_owner_action"] is owner_action


def test_resolve_outreach_prefers_id_then_thread() -> None:
    rows = [
        {"outreach_id": "OUT-1", "external_thread_id": "THREAD-1"},
        {"outreach_id": "OUT-2", "external_thread_id": "THREAD-2"},
    ]
    assert resolve_outreach({"outreach_id": "OUT-2", "external_thread_id": "THREAD-1"}, rows)["outreach_id"] == "OUT-2"
    assert resolve_outreach({"external_thread_id": "THREAD-1"}, rows)["outreach_id"] == "OUT-1"
    assert resolve_outreach({"external_thread_id": "UNKNOWN"}, rows) is None
