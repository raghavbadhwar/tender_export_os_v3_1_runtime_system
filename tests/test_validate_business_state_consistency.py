from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.validate_business_state_consistency import load_execution_receipts, validate_business_state


def strict_quote(case_id: str, quote_id: str, supplier_id: str) -> dict[str, str]:
    return {
        "quote_id": quote_id,
        "case_id": case_id,
        "supplier_id": supplier_id,
        "supplier_name": supplier_id,
        "quote_received_at": "2099-01-02T00:00:00+00:00",
        "quote_proof_type": "supplier_written_quote",
        "quote_proof_path": f"receipts/{quote_id}.pdf",
        "quote_proof_sha256": "a" * 64,
        "quote_verification_status": "VERIFIED",
        "case_spec_match": "TRUE",
        "product_description": "Verified tender supply",
        "quantity": "100",
        "unit": "set",
        "unit_price_inr": "100",
        "currency": "INR",
        "gst_rate_pct": "18",
        "lead_time_days": "7",
        "delivery_terms": "Delivered at site",
        "payment_terms_offered": "30 days",
        "validity_days": "30",
        "supplier_specific_quote": "TRUE",
        "supplier_specific_quote": "TRUE",
    }


def verified_outcome(case_id: str, outcome_type: str) -> dict[str, str]:
    return {
        "outcome_id": f"OUT-{case_id}-{outcome_type}",
        "case_id": case_id,
        "outcome_type": outcome_type,
        "verification_status": "VERIFIED",
        "evidence_path": f"receipts/{case_id}-{outcome_type}.json",
        "evidence_sha256": "a" * 64,
    }


def test_business_state_rejects_unproved_submission_pricing_payment_and_closure() -> None:
    cases = [
        {"case_id": "GOV-SENT", "status": "SENT_OR_SUBMITTED", "execution_sub_status": "SUBMITTED"},
        {"case_id": "GOV-PRICE", "status": "PRICING_READY", "execution_sub_status": ""},
        {"case_id": "GOV-PAID", "status": "WON", "execution_sub_status": "PAYMENT_RECEIVED"},
        {"case_id": "GOV-LOST", "status": "LOST", "execution_sub_status": ""},
    ]

    report = validate_business_state(cases, quotes=[], approvals=[], outcomes=[], execution_receipts=[])
    codes = {finding["code"] for finding in report["findings"]}

    assert report["status"] == "FAIL"
    assert "SENT_WITHOUT_RECEIPT" in codes
    assert "PRICING_WITHOUT_TWO_STRICT_QUOTES" in codes
    assert "PAYMENT_WITHOUT_VERIFIED_EVIDENCE" in codes
    assert "CLOSED_WITHOUT_OUTCOME" in codes


def test_business_state_accepts_evidenced_transitions_and_detects_contradictions() -> None:
    cases = [
        {"case_id": "GOV-1", "status": "PRICING_READY", "execution_sub_status": ""},
        {"case_id": "EXP-1", "status": "SENT_OR_SUBMITTED", "execution_sub_status": "SUBMITTED"},
        {"case_id": "GOV-2", "status": "WON", "execution_sub_status": "PAYMENT_RECEIVED"},
    ]
    quotes = [strict_quote("GOV-1", "Q1", "S1"), strict_quote("GOV-1", "Q2", "S2")]
    outcomes = [verified_outcome("GOV-2", "WON"), verified_outcome("GOV-2", "PAYMENT_RECEIVED")]
    receipts = [{"case_id": "EXP-1", "receipt_id": "R1", "verification_status": "VERIFIED", "external_effect_status": "SENT"}]
    approvals = [{"approval_id": "APR-1", "case_id": "EXP-1", "approval_status": "PENDING"}]

    report = validate_business_state(cases, quotes, approvals, outcomes, receipts)
    codes = {finding["code"] for finding in report["findings"]}

    assert "PRICING_WITHOUT_TWO_STRICT_QUOTES" not in codes
    assert "SENT_WITHOUT_RECEIPT" not in codes
    assert "PAYMENT_WITHOUT_VERIFIED_EVIDENCE" not in codes
    assert "PENDING_APPROVAL_AFTER_EXECUTION" in codes

    contradictory = validate_business_state(
        [{"case_id": "EXP-2", "status": "SENT_OR_SUBMITTED", "execution_sub_status": "SUBMITTED"}],
        [],
        [],
        [],
        [
            {"case_id": "EXP-2", "receipt_id": "R2", "verification_status": "VERIFIED", "external_effect_status": "SENT"},
            {"case_id": "EXP-2", "receipt_id": "R3", "verification_status": "VERIFIED", "external_effect_status": "NOT_SENT"},
        ],
    )
    assert any(row["code"] == "CONFLICTING_EXECUTION_CLAIMS" for row in contradictory["findings"])


def test_business_state_blocks_downstream_stage_when_corrigendum_review_is_open() -> None:
    report = validate_business_state(
        [
            {
                "case_id": "GOV-CORR",
                "status": "PRICING_READY",
                "execution_sub_status": "",
                "corrigenda_status": "CHANGED_REVIEW_REQUIRED",
            }
        ],
        [strict_quote("GOV-CORR", "Q1", "S1"), strict_quote("GOV-CORR", "Q2", "S2")],
        [],
        [],
        [],
    )

    assert any(row["code"] == "CORRIGENDUM_REVIEW_REQUIRED" for row in report["findings"])


def test_business_state_requires_passing_gov_supplier_532_gate_before_pricing() -> None:
    candidates = []
    for index, source_type in enumerate(["india_b2b", "local_cluster", "past_history", "india_b2b", "gem_seller"], start=1):
        candidates.append(
            {
                "supplier_id": f"S{index}",
                "supplier_name": f"Supplier {index}",
                "source_type": source_type,
                "blacklisted": "FALSE",
                "watchlisted": "FALSE",
                "source_evidence_path": f"outputs/evidence/{index}.json",
                "source_evidence_sha256": "a" * 64,
                "product_fit_status": "MATCHED",
                "capacity_delivery_evidence_path": f"outputs/evidence/{index}-capacity.json",
                "capacity_delivery_evidence_sha256": "a" * 64,
            }
        )
    quotes = [strict_quote("GOV-532", "Q1", "S1"), strict_quote("GOV-532", "Q2", "S2")]
    report = validate_business_state(
        [{"case_id": "GOV-532", "workflow_type": "GOV", "source_name": "CPPP", "status": "PRICING_READY", "execution_sub_status": ""}],
        quotes,
        [],
        [],
        [],
        suppliers=[],
        supplier_candidates_by_case={"GOV-532": candidates},
    )

    assert not any(row["code"] == "GOV_SUPPLIER_532_NOT_READY" for row in report["findings"])

    blocked = validate_business_state(
        [{"case_id": "GOV-532", "workflow_type": "GOV", "source_name": "CPPP", "status": "PRICING_READY", "execution_sub_status": ""}],
        quotes,
        [],
        [],
        [],
        suppliers=[],
        supplier_candidates_by_case={"GOV-532": candidates[:4]},
    )
    assert any(row["code"] == "GOV_SUPPLIER_532_NOT_READY" for row in blocked["findings"])


def test_gov_execution_sub_status_requires_matching_verified_milestone_outcome() -> None:
    missing = validate_business_state(
        [{"case_id": "GOV-MILESTONE", "workflow_type": "GOV", "status": "FOLLOW_UP", "execution_sub_status": "L1_DECLARED"}],
        [],
        [],
        [],
        [],
    )
    matching = validate_business_state(
        [{"case_id": "GOV-MILESTONE", "workflow_type": "GOV", "status": "FOLLOW_UP", "execution_sub_status": "L1_DECLARED"}],
        [],
        [],
        [verified_outcome("GOV-MILESTONE", "L1_DECLARED")],
        [],
    )

    assert any(row["code"] == "GOV_EXECUTION_MILESTONE_NOT_READY" for row in missing["findings"])
    assert not any(row["code"] == "GOV_EXECUTION_MILESTONE_NOT_READY" for row in matching["findings"])


def test_export_execution_sub_status_requires_matching_verified_milestone_outcome() -> None:
    missing = validate_business_state(
        [{"case_id": "EXP-MILESTONE", "workflow_type": "EXPORT", "status": "FOLLOW_UP", "execution_sub_status": "CUSTOMS_CLEARED"}],
        [],
        [],
        [],
        [],
    )
    matching = validate_business_state(
        [{"case_id": "EXP-MILESTONE", "workflow_type": "EXPORT", "status": "FOLLOW_UP", "execution_sub_status": "CUSTOMS_CLEARED"}],
        [],
        [],
        [verified_outcome("EXP-MILESTONE", "CUSTOMS_CLEARED")],
        [],
    )

    assert any(row["code"] == "EXPORT_EXECUTION_MILESTONE_NOT_READY" for row in missing["findings"])
    assert not any(row["code"] == "EXPORT_EXECUTION_MILESTONE_NOT_READY" for row in matching["findings"])


def test_business_state_validator_is_directly_executable() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "validate_business_state_consistency.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Reject business-state transitions" in completed.stdout


def test_consolidated_gmail_plugin_receipt_is_normalized(tmp_path: Path) -> None:
    path = tmp_path / "outreach.json"
    path.write_text(
        '{"receipt_id":"R1","connector":"GMAIL_PLUGIN","verified_by":["sent_message_readback"],'
        '"sent":[{"case_id":"EXP-1","external_message_id":"M1","sent_at":"2099-01-01T00:00:00Z"}]}',
        encoding="utf-8",
    )

    receipts = load_execution_receipts([path])

    assert receipts[0]["case_id"] == "EXP-1"
    assert receipts[0]["external_effect_status"] == "SENT"
    assert receipts[0]["verification_status"] == "VERIFIED"


def test_export_outreach_approval_is_not_mistaken_for_a_quote_pack_approval() -> None:
    early_outreach = validate_business_state(
        [{"case_id": "EXP-EARLY", "workflow_type": "EXPORT", "status": "APPROVAL_REQUIRED", "execution_sub_status": ""}],
        [],
        [{"approval_id": "APR-OUTREACH", "case_id": "EXP-EARLY", "approval_status": "PENDING", "proposed_action": "buyer_introductory_outreach"}],
        [],
        [],
    )
    quote = validate_business_state(
        [{"case_id": "EXP-QUOTE", "workflow_type": "EXPORT", "status": "APPROVAL_REQUIRED", "execution_sub_status": ""}],
        [],
        [{"approval_id": "APR-QUOTE", "case_id": "EXP-QUOTE", "approval_status": "PENDING", "proposed_action": "send_export_quotation"}],
        [],
        [],
    )

    assert not any(row["code"] == "EXPORT_QUOTE_PACK_NOT_READY" for row in early_outreach["findings"])
    assert any(row["code"] == "EXPORT_QUOTE_PACK_NOT_READY" for row in quote["findings"])
