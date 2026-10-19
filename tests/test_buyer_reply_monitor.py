from scripts.generate_buyer_reply_monitor import apply_approval_state


def test_outreach_becomes_connector_ready_only_after_approval() -> None:
    row = {"outreach_id": "OUT-1", "approval_status": "PENDING", "send_status": "DRAFT_ONLY", "stop_reason": ""}
    approved = apply_approval_state(row, {"approval_status": "APPROVED"})
    assert approved["approval_status"] == "APPROVED"
    assert approved["send_status"] == "READY_AFTER_APPROVAL"


def test_rejected_outreach_is_stopped() -> None:
    row = {"outreach_id": "OUT-1", "approval_status": "PENDING", "send_status": "DRAFT_ONLY", "stop_reason": ""}
    rejected = apply_approval_state(row, {"approval_status": "REJECTED"})
    assert rejected["send_status"] == "STOPPED"
    assert rejected["stop_reason"] == "APPROVAL_REJECTED"
