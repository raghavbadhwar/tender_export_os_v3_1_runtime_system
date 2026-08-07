from scripts.run_critic_gate import build_critic_report


def test_critic_gate_blocks_pricing_ready_without_two_strict_quotes() -> None:
    cases = [
        {
            "case_id": "EXP-TEST-001",
            "workflow_type": "EXPORT",
            "opportunity_title": "Premium artisan textiles",
            "source_name": "Example RFQ",
            "product_or_service": "Artisan textile gift set",
            "status": "PRICING_READY",
            "pricing_done": "TRUE",
            "hsn_itchs_candidate": "6304 draft",
            "export_policy": "Draft free subject to checks",
        }
    ]
    quotes = [
        {
            "quote_id": "Q-1",
            "case_id": "EXP-TEST-001",
            "supplier_id": "SUP-1",
            "supplier_name": "Supplier One",
            "quote_received_at": "2026-07-01T10:00:00",
            "quote_proof_type": "quotation_pdf",
            "quote_proof_path": "receipts/supplier_quotes/q1.pdf",
            "quote_proof_sha256": "a" * 64,
            "quote_verification_status": "VERIFIED",
            "case_spec_match": "TRUE",
            "product_description": "Artisan textile gift set",
            "quantity": "100",
            "unit": "set",
            "unit_price_inr": "100",
            "currency": "INR",
            "gst_rate_pct": "18",
            "lead_time_days": "7",
            "delivery_terms": "Ex works",
            "payment_terms_offered": "30 days",
            "validity_days": "30",
            "quote_validity_date": "2099-12-31",
            "supplier_specific_quote": "TRUE",
        }
    ]
    report = build_critic_report(
        cases,
        quotes,
        suppliers=[{"supplier_id": "SUP-1", "supplier_name": "Supplier One", "blacklisted": "FALSE"}],
        approvals=[],
        rfqs=[{"case_id": "EXP-TEST-001", "evidence_status": "RFQ_VERIFIED", "rfq_stage": "RFQ_VERIFIED"}],
        include_all=True,
    )

    assert report["status"] == "BLOCKED"
    assert report["reviews"][0]["strict_quote_proof_count"] == 1
    assert any("2 strict supplier-specific quote proofs" in item for item in report["reviews"][0]["blockers"])
