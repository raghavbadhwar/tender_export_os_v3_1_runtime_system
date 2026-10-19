from __future__ import annotations

import json

from scripts.supplier_performance_projection import build_projection


def strict_quote(**updates):
    value = {
        "quote_id": "Q-1",
        "case_id": "EXP-TEST-001",
        "supplier_id": "SUP-1",
        "supplier_name": "Verified Supplier",
        "quote_received_at": "2099-01-01T10:00:00+00:00",
        "response_hrs": "6",
        "product_description": "Handmade brass decor",
        "quantity": "100",
        "unit_price_usd": "4.25",
        "currency": "USD",
        "tax_treatment": "export zero-rated candidate",
        "lead_time_days": "12",
        "delivery_terms": "FOB Nhava Sheva",
        "payment_terms_offered": "30% advance, 70% before dispatch",
        "validity_days": "30",
        "quote_clarity_score": "86",
        "selected_for_pricing": "TRUE",
        "quote_proof_type": "quotation_pdf",
        "quote_proof_path": "receipts/supplier_quotes/q1.pdf",
        "quote_proof_sha256": "b" * 64,
        "quote_verification_status": "VERIFIED",
        "case_spec_match": "TRUE",
        "supplier_specific_quote": "TRUE",
    }
    value.update(updates)
    return value


def test_public_listing_supplier_is_weak_evidence_only() -> None:
    report = build_projection(
        suppliers=[
            {
                "supplier_id": "SUP-PUBLIC",
                "supplier_name": "Public Listing Supplier",
                "source_type": "india_b2b",
                "source_platform": "IndiaMART",
                "is_indicative_price_only": "TRUE",
                "notes": "Public listing only.",
            }
        ],
        quotes=[
            {
                "quote_id": "Q-PUBLIC",
                "case_id": "EXP-TEST-001",
                "supplier_id": "SUP-PUBLIC",
                "supplier_name": "Public Listing Supplier",
                "quote_proof_type": "marketplace_listing",
                "quote_proof_path": "outputs/source_evidence/listing.html",
                "indicative_price_only": "TRUE",
                "marketplace_listing_price": "TRUE",
            }
        ],
        outcomes=[],
    )

    supplier = report["suppliers"][0]
    assert supplier["projection_status"] == "WEAK_PUBLIC_SIGNAL_ONLY"
    assert supplier["evidence_counts"]["verified_quote_responses"] == 0
    assert supplier["weak_evidence"]["not_counted_as_delivery_history"] is True
    assert "public listing or marketplace signal is weak evidence only" in supplier["blockers"]
    proposal = supplier["recommendation_proposal"]
    assert proposal["proposal_status"] == "RECOMMENDATION_ONLY_NOT_APPLIED"
    assert proposal["automatic_change_allowed"] is False
    assert proposal["uncertainty"] == "HIGH"
    assert "false_positive_impact" in proposal
    assert "rollback_plan" in proposal


def test_verified_quote_and_delivery_evidence_create_operational_projection() -> None:
    report = build_projection(
        suppliers=[{"supplier_id": "SUP-1", "supplier_name": "Verified Supplier", "source_platform": "direct"}],
        quotes=[strict_quote()],
        outcomes=[
            {
                "outcome_id": "OUT-1",
                "case_id": "EXP-TEST-001",
                "outcome_type": "DELIVERED",
                "verification_status": "VERIFIED",
            },
            {
                "outcome_id": "OUT-2",
                "case_id": "EXP-TEST-001",
                "outcome_type": "PAYMENT_RECEIVED",
                "verification_status": "VERIFIED",
            },
        ],
    )

    supplier = report["suppliers"][0]
    assert supplier["projection_status"] == "OPERATIONAL_EVIDENCE"
    assert supplier["evidence_counts"]["verified_quote_responses"] == 1
    assert supplier["evidence_counts"]["delivery_evidence"] == 1
    assert supplier["evidence_counts"]["payment_terms_evidence"] == 1
    assert supplier["operational_signals"]["avg_response_hrs"] == 6
    assert supplier["score"] > 70
    assert supplier["recommendation_proposal"]["sample_size"] == 3
    assert supplier["recommendation_proposal"]["proposal_type"] == "SUPPLIER_RANKING_RECOMMENDATION"


def test_defect_or_negative_owner_correction_requires_owner_review() -> None:
    report = build_projection(
        suppliers=[{"supplier_id": "SUP-1", "supplier_name": "Verified Supplier", "source_platform": "direct"}],
        quotes=[strict_quote()],
        outcomes=[
            {
                "outcome_id": "OUT-CLAIM",
                "case_id": "EXP-TEST-001",
                "outcome_type": "CLAIM_OR_RETURN",
                "verification_status": "VERIFIED",
            }
        ],
        owner_corrections=[
            {
                "supplier_id": "SUP-1",
                "direction": "NEGATIVE",
                "verification_status": "VERIFIED",
                "summary": "Owner observed late documentation in verified shipment file.",
            }
        ],
    )

    supplier = report["suppliers"][0]
    assert supplier["projection_status"] == "OWNER_REVIEW"
    assert supplier["evidence_counts"]["defect_or_claim_evidence"] == 1
    assert supplier["evidence_counts"]["owner_corrections"] == 1
    assert "Owner observed late documentation" in json.dumps(supplier["owner_correction_notes"])
