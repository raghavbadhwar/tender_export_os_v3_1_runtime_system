from __future__ import annotations

import pytest

from scripts.ingest_buyer_replies import classify_reply, resolve_outreach, validate_connector_payload


def test_connector_contract_accepts_only_gmail_plugin() -> None:
    validate_connector_payload({"connector": "GMAIL_PLUGIN", "messages": []})
    with pytest.raises(ValueError, match="GMAIL_PLUGIN"):
        validate_connector_payload({"connector": "GWS", "messages": []})
    with pytest.raises(ValueError, match="messages"):
        validate_connector_payload({"connector": "GMAIL_PLUGIN"})


@pytest.mark.parametrize(
    ("text", "expected", "owner_action"),
    [
        ("Please remove us from your list and do not contact again.", "OPT_OUT", False),
        ("Delivery Status Notification: address not found", "BOUNCE", False),
        ("Automatic reply: I am out of office", "AUTO_REPLY", False),
        ("Thanks, please send the catalogue and MOQ details.", "POSITIVE_INTEREST", True),
        ("Can you quote FOB and advise payment terms?", "NEGOTIATION", True),
        ("Who produces these items?", "QUESTION", True),
        ("Thank you for writing.", "NEEDS_REVIEW", True),
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
