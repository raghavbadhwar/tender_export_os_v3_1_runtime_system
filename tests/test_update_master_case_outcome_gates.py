from __future__ import annotations

from scripts.update_master_case import validate_protected_state


def test_force_cannot_bypass_closed_case_or_payment_evidence() -> None:
    won = validate_protected_state(
        {"case_id": "GOV-1", "status": "WON", "execution_sub_status": ""},
        quotes=[],
        approvals=[],
        outcomes=[],
        execution_receipts=[],
    )
    paid = validate_protected_state(
        {"case_id": "GOV-2", "status": "WON", "execution_sub_status": "PAYMENT_RECEIVED"},
        quotes=[],
        approvals=[],
        outcomes=[],
        execution_receipts=[],
    )

    assert won["ok"] is False
    assert "CLOSED_WITHOUT_OUTCOME" in won["codes"]
    assert paid["ok"] is False
    assert "PAYMENT_WITHOUT_VERIFIED_EVIDENCE" in paid["codes"]


def test_protected_state_accepts_matching_verified_evidence() -> None:
    evidence = {
        "case_id": "GOV-1",
        "outcome_type": "WON",
        "verification_status": "VERIFIED",
        "evidence_path": "receipts/award.json",
        "evidence_sha256": "a" * 64,
    }

    result = validate_protected_state(
        {"case_id": "GOV-1", "status": "WON", "execution_sub_status": ""},
        quotes=[],
        approvals=[],
        outcomes=[evidence],
        execution_receipts=[],
    )

    assert result == {"ok": True, "codes": [], "findings": []}
