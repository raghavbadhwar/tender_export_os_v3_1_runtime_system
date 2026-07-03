from scripts.supplier_matcher_from_tender import is_quote_proof
from scripts.quote_proof import classify_quote_proof, strict_quote_proofs


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


def test_quote_received_at_without_supplier_specific_proof_is_not_strict() -> None:
    row = {
        "quote_id": "Q-OLD",
        "case_id": "GOV-TEST-001",
        "supplier_id": "SUP-1",
        "quote_received_at": "2026-07-01T10:00:00",
    }
    result = classify_quote_proof(row)
    assert result["is_strict_quote_proof"] is False
    assert "quote_proof_type <blank> is not supplier-specific" in result["blockers"]


def test_strict_quote_proofs_dedupes_supplier_identity() -> None:
    rows = [
        {
            "quote_id": "Q-1",
            "case_id": "GOV-TEST-001",
            "supplier_id": "SUP-1",
            "quote_received_at": "2026-07-01T10:00:00",
            "quote_proof_type": "quotation_pdf",
            "quote_proof_path": "receipts/supplier_quotes/q1.pdf",
        },
        {
            "quote_id": "Q-2",
            "case_id": "GOV-TEST-001",
            "supplier_id": "SUP-1",
            "quote_received_at": "2026-07-01T11:00:00",
            "quote_proof_type": "email_quote",
            "quote_proof_path": "receipts/supplier_quotes/q2.eml",
        },
        {
            "quote_id": "Q-3",
            "case_id": "GOV-TEST-001",
            "supplier_id": "SUP-2",
            "quote_received_at": "2026-07-01T12:00:00",
            "quote_proof_type": "marketplace_listing",
            "quote_proof_path": "outputs/listing.html",
            "indicative_price_only": "TRUE",
        },
    ]
    proofs = strict_quote_proofs("GOV-TEST-001", rows)
    assert [row["quote_id"] for row in proofs] == ["Q-1"]
