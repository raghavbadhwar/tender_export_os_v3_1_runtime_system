from scripts.buyer_verification_engine import verify_buyer_stage


def test_marketplace_only_buyer_cannot_be_ready() -> None:
    result = verify_buyer_stage({"marketplace_only": True, "rfq_source_url": "https://example.com/rfq"})
    assert result["ready"] is False
    assert result["stage"] == "RAW_LEAD"
    assert result["demand_status"] == "MARKETPLACE_LEAD_ONLY"


def test_catalogue_fit_and_public_contact_are_not_promoted_to_rfq() -> None:
    result = verify_buyer_stage(
        {
            "buyer_name": "Example Buyer",
            "company_website": "https://example.com",
            "contact_path": "https://example.com/contact",
            "catalogue_fit": "artisan homeware",
        }
    )

    assert result["contact_ready"] is True
    assert result["rfq_ready"] is False
    assert result["demand_status"] == "CATALOGUE_HYPOTHESIS"


def test_full_buyer_evidence_reaches_ready_for_approval() -> None:
    result = verify_buyer_stage(
        {
            "buyer_name": "Example Buyer",
            "company_website": "https://example.com",
            "contact_path": "portal",
            "rfq_source_url": "https://example.com/rfq",
            "payment_terms": "LC at sight",
        }
    )
    assert result["ready"] is True
    assert result["stage"] == "READY_FOR_APPROVAL"
