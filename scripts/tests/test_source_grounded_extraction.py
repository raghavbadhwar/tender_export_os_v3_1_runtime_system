from __future__ import annotations

from pathlib import Path

from scripts.extract_case_evidence import extract_quote_evidence, extract_tender_evidence, render_review_html


def test_tender_extraction_returns_source_grounded_fields() -> None:
    text = """
    Bid Number: GEM/2026/B/123456
    Buyer Organisation: Delhi Jal Board
    Tender Value: INR 12,50,000
    EMD: Rs. 25,000
    Bid End Date: 20 July 2026 15:00
    Delivery Location: New Delhi warehouse
    Payment Terms: 30 days after delivery and inspection.
    Documents Required: GST certificate, PAN, past experience certificate.
    BOQ: Supply of 500 stainless steel bottles.
    """
    result = extract_tender_evidence(text, case_id="GOV-20260704-001", source_name="unit_fixture")

    assert result["case_id"] == "GOV-20260704-001"
    assert result["extraction_kind"] == "tender"
    assert result["fields"]["bid_number"]["value"] == "GEM/2026/B/123456"
    assert result["fields"]["emd_amount"]["value"] == "Rs. 25,000"
    assert result["fields"]["delivery_location"]["value"] == "New Delhi warehouse"
    assert result["fields"]["payment_terms"]["value"].startswith("30 days")
    assert result["fields"]["bid_number"]["source_span"]["start"] >= 0
    assert "documents_required" in result["fields"]
    assert result["evidence_level"] == "SOURCE_GROUNDED"
    assert "quote_proof" not in result["missing_fields"]


def test_quote_extraction_classifies_marketplace_listing_as_indicative() -> None:
    text = """
    Supplier: Example Traders
    Product: PET bottle 330 ml
    Price: Rs. 7.50 per piece
    MOQ: 1000 pieces
    Lead Time: 4 days
    Source: Indiamart public listing only, not a written quote.
    """
    result = extract_quote_evidence(text, case_id="EXP-20260704-001", source_name="unit_fixture")

    assert result["fields"]["supplier"]["value"] == "Example Traders"
    assert result["fields"]["unit_price"]["value"] == "Rs. 7.50"
    assert result["quote_proof_classification"] == "INDICATIVE_SIGNAL"
    assert result["approval_gate"] == "DO_NOT_USE_FOR_FINAL_PRICING"


def test_review_html_contains_highlighted_source(tmp_path: Path) -> None:
    text = "Bid Number: GEM/2026/B/123456\nEMD: Rs. 25,000\n"
    result = extract_tender_evidence(text, case_id="GOV-20260704-002", source_name="unit_fixture")
    html = render_review_html(result, text)
    assert "GOV-20260704-002" in html
    assert "source-highlight" in html
    assert "GEM/2026/B/123456" in html
