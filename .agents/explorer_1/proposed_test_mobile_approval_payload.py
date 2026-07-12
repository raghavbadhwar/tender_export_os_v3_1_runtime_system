"""Proposed test cases to validate mobile approval payload rendering."""

import csv
from pathlib import Path
from scripts.render_mobile_approval_payload import render


def test_render_mobile_approval_payload() -> None:
    row = {
        "approval_id": "APR-999",
        "case_id": "EXP-20260706-999",
        "workflow_type": "EXPORT",
        "action_approved": "send_export_quotation",
        "approval_card_path": "",
        "business_object": "Brass Handicrafts Quote",
        "amount": "INR 500000",
        "deadline_date": "2026-07-31",
        "expected_benefit": "High margin deal",
        "concrete_risk": "Currency fluctuation",
        "recovery_rollback_path": "Revert to local supplier",
        "missing_information": "Buyer verification proof"
    }
    
    payload = render(row)
    assert "APPROVAL REQUIRED — APR-999" in payload
    assert "Case: EXP-20260706-999" in payload
    assert "Workflow: EXPORT" in payload
    assert "Action: send_export_quotation" in payload
    assert "Amount/price: INR 500000" in payload
    assert "Deadline: 2026-07-31" in payload
    assert "Benefit: High margin deal" in payload
    assert "Risk: Currency fluctuation" in payload
    assert "Recovery: Revert to local supplier" in payload
    assert "Reply options: APPROVE APR-999" in payload
