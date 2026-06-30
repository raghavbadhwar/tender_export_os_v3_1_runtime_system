from scripts.supplier_matcher_from_tender import is_quote_proof


def test_marketplace_listing_price_is_not_quote_proof() -> None:
    candidate = {
        "quote_proof_type": "marketplace_listing",
        "quote_proof_path": "outputs/example/listing.html",
        "indicative_price_only": True,
        "not_a_quote_warning": True,
    }
    assert is_quote_proof(candidate) is False


def test_supplier_specific_pdf_is_quote_proof() -> None:
    candidate = {
        "quote_proof_type": "quotation_pdf",
        "quote_proof_path": "receipts/supplier_quotes/q1.pdf",
        "indicative_price_only": False,
        "not_a_quote_warning": False,
    }
    assert is_quote_proof(candidate) is True
