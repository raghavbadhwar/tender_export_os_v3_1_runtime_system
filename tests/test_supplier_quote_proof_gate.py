from scripts.supplier_matcher_from_tender import is_quote_proof
from scripts.quote_proof import classify_quote_proof, strict_quote_proofs
from scripts.run_morning_opportunity_intelligence import pipeline_outcome, quote_counts


def verified_quote(**updates):
    value = {
        "quote_id": "Q-VALID",
        "case_id": "GOV-TEST-001",
        "supplier_id": "SUP-1",
        "supplier_name": "Supplier One",
        "quote_received_at": "2099-07-01T10:00:00+00:00",
        "quote_proof_type": "quotation_pdf",
        "quote_proof_path": "receipts/supplier_quotes/q1.pdf",
        "quote_proof_sha256": "a" * 64,
        "quote_verification_status": "VERIFIED",
        "case_spec_match": "TRUE",
        "product_description": "Verified stationery set",
        "quantity": "10",
        "unit": "set",
        "unit_price_inr": "100",
        "currency": "INR",
        "gst_rate_pct": "18",
        "lead_time_days": "7",
        "delivery_terms": "Ex works Pune",
        "payment_terms_offered": "30 days",
        "validity_days": "30",
        "supplier_specific_quote": "TRUE",
    }
    value.update(updates)
    return value


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
        verified_quote(quote_id="Q-1"),
        verified_quote(quote_id="Q-2", quote_proof_type="email_quote", quote_proof_path="receipts/supplier_quotes/q2.eml"),
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


def test_expired_quote_is_not_strict_quote_proof() -> None:
    row = verified_quote(
        quote_id="Q-EXPIRED",
        quote_received_at="2026-07-01T10:00:00+00:00",
        quote_validity_date="2026-07-05",
        validity_days="",
    )

    result = classify_quote_proof(row, as_of="2026-07-06")

    assert result["is_strict_quote_proof"] is False
    assert "quote is expired as of readiness check" in result["blockers"]


def test_missing_proof_hash_is_not_strict_quote_proof() -> None:
    result = classify_quote_proof(verified_quote(quote_id="Q-NO-HASH", quote_proof_sha256=""))

    assert result["is_strict_quote_proof"] is False
    assert "quote_proof_sha256 must be a 64-character SHA-256 hash" in result["blockers"]


def test_case_spec_mismatch_is_not_strict_quote_proof() -> None:
    result = classify_quote_proof(verified_quote(quote_id="Q-SPEC-MISMATCH", case_spec_match="FALSE"))

    assert result["is_strict_quote_proof"] is False
    assert "case_spec_match must be TRUE" in result["blockers"]


def test_generic_catalogue_listing_with_quote_like_fields_is_not_strict_quote_proof() -> None:
    row = verified_quote(
        quote_id="Q-CATALOGUE",
        quote_proof_type="public_catalog",
        quote_proof_path="outputs/public/catalogue.html",
        indicative_price_only="TRUE",
        marketplace_listing_price="TRUE",
    )

    result = classify_quote_proof(row)

    assert result["classification"] == "INDICATIVE_SIGNAL"
    assert result["is_strict_quote_proof"] is False
    assert "indicative marketplace/public listing signals are not quote proof" in result["blockers"]


def test_missing_supplier_name_is_not_strict_quote_proof() -> None:
    result = classify_quote_proof(verified_quote(quote_id="Q-NO-NAME", supplier_name=""))

    assert result["is_strict_quote_proof"] is False
    assert "supplier identity requires supplier_id and supplier_name" in result["blockers"]


def test_morning_quote_counts_use_canonical_strict_proof_semantics() -> None:
    rows = [
        {
            "quote_id": "Q-LEGACY",
            "case_id": "GOV-TEST-001",
            "supplier_id": "SUP-1",
            "quote_request_sent_at": "2026-07-01T09:00:00",
            "quote_received_at": "2026-07-01T10:00:00",
            "unit_price_inr": "100",
        },
        verified_quote(quote_id="Q-STRICT", supplier_id="SUP-2", supplier_name="Supplier Two", quote_proof_path="receipts/supplier_quotes/q2.pdf", unit_price_inr="110"),
    ]

    counts = quote_counts(rows)

    assert counts["formal_quote_proofs"] == 1
    assert counts["public_price_proofs"] == 1
    assert counts["price_proofs_total"] == 2


def test_morning_pipeline_propagates_substep_failure() -> None:
    outcome = pipeline_outcome([
        {"label": "schema", "ok": True},
        {"label": "source intake", "ok": False},
    ])

    assert outcome == {"errors": 1, "status": "PARTIAL_FAILURE", "exit_code": 1}
