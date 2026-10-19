from scripts.evaluate_western_premium_proof_lane import evaluate_case


def test_western_premium_without_buyer_proof_stays_research_lane() -> None:
    review = evaluate_case(
        {
            "case_id": "EXP-WEST-001",
            "workflow_type": "EXPORT",
            "buyer_country": "USA",
            "product_or_service": "Premium Indian handicrafts corporate gifting",
            "hsn_itchs_candidate": "8306 draft",
            "export_policy": "Draft free subject to tariff check",
            "notes": "landed_margin_pct=42",
        },
        rfqs=[],
        quotes=[],
        suppliers=[],
    )

    assert review["lane_stage"] == "RESEARCH_LANE_ONLY"
    assert any("buyer-specific" in blocker for blocker in review["blockers"])


def test_western_premium_spices_require_food_safety_docs() -> None:
    review = evaluate_case(
        {
            "case_id": "EXP-WEST-002",
            "workflow_type": "EXPORT",
            "buyer_country": "Germany",
            "product_or_service": "Premium spices corporate gifting",
            "hsn_itchs_candidate": "0904 draft",
            "export_policy": "Draft free subject to tariff check",
            "notes": "landed_margin_pct=45",
        },
        rfqs=[{"case_id": "EXP-WEST-002", "evidence_status": "RFQ_VERIFIED", "rfq_stage": "RFQ_VERIFIED"}],
        quotes=[
            {
                "quote_id": "Q-1",
                "case_id": "EXP-WEST-002",
                "supplier_id": "SUP-1",
                "quote_received_at": "2026-07-01T10:00:00",
                "quote_proof_type": "quotation_pdf",
                "quote_proof_path": "receipts/supplier_quotes/q1.pdf",
                "packaging_details": "Retail gift tin",
                "fob_price_usd": "10",
            }
        ],
        suppliers=[{"supplier_id": "SUP-1", "supplier_name": "Supplier One", "other_certs": "Handmade provenance"}],
    )

    assert review["lane_stage"] == "BLOCKED_BEFORE_QUOTE"
    assert any("food-safety" in blocker for blocker in review["blockers"])
