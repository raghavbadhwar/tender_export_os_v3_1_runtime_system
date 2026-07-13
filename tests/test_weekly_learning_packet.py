from __future__ import annotations

from scripts.build_weekly_learning_packet import proposal_effectiveness, reply_results, status_counts


def test_weekly_learning_packet_helpers_summarize_proposals_and_replies() -> None:
    proposals = [{"status": "APPROVED"}, {"status": "APPLIED"}, {"status": "REJECTED"}]
    replies = reply_results(
        communication_rows=[{"message_type": "INBOUND_REPLY"}, {"direction": "OUTBOUND"}],
        outreach_rows=[{"send_status": "SENT"}, {"send_status": "PENDING"}],
    )
    effectiveness = proposal_effectiveness(proposals)

    assert replies["reply_like_rows"] == 1
    assert replies["outreach_status_counts"] == {"SENT": 1, "PENDING": 1}
    assert effectiveness["approved"] == 1
    assert effectiveness["applied"] == 1
    assert effectiveness["failed_or_rejected"] == 1


def test_status_counts_uses_unknown_for_blank_values() -> None:
    assert status_counts([{"status": ""}, {"status": "pass"}], "status") == {"UNKNOWN": 1, "PASS": 1}
