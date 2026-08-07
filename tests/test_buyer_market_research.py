from __future__ import annotations

from scripts.stage_buyer_market_research import build_outreach_draft, normalize_item, upsert_csv, validate_item


def sample_item() -> dict:
    return {
        "company_name": "Example Ethical Home Store",
        "country": "United Kingdom",
        "company_type": "Retailer",
        "website_url": "https://example.com",
        "catalog_url": "https://example.com/catalogue",
        "matching_products": [
            {
                "product_name": "Handmade terracotta mug",
                "product_url": "https://example.com/products/mug",
                "evidence": "Product page identifies handmade terracotta craft.",
            }
        ],
        "assortment_evidence": "Public catalogue carries handmade homeware.",
        "price_positioning": "MID",
        "contact_page_url": "https://example.com/contact",
        "public_contact": "hello@example.com",
        "contact_scope": "GENERAL_CONTACT",
        "evidence_level": "CONTACT_PATH_VERIFIED",
        "market_fit_score": 74,
        "demand_confidence": "MEDIUM",
        "source_citations": [
            "https://example.com/catalogue",
            "https://example.com/products/mug",
            "https://example.com/contact",
        ],
    }


def test_valid_item_preserves_catalog_signal_as_hypothesis() -> None:
    item = normalize_item(sample_item(), category_name="Handicrafts and Artisan Products")
    assert validate_item(item) == []
    assert item["contact_status"] == "PUBLIC_GENERAL_CONTACT"
    assert item["next_safe_action"] == "DRAFT_OUTREACH_FOR_APPROVAL"
    assert "not an RFQ" in item["assortment_evidence_note"]


def test_contact_must_have_public_contact_page_evidence() -> None:
    raw = sample_item()
    raw["source_citations"].remove(raw["contact_page_url"])
    item = normalize_item(raw, category_name="Handicrafts and Artisan Products")
    assert "public_contact requires cited contact_page_url" in validate_item(item)


def test_outreach_draft_is_personalized_and_non_committal() -> None:
    item = normalize_item(sample_item(), category_name="Handicrafts and Artisan Products")
    draft = build_outreach_draft(item, outreach_id="OUT-EXAMPLE")
    assert "Handmade terracotta mug" in draft["body"]
    assert "person responsible for sourcing or buying" in draft["body"]
    assert "No price, delivery date, payment term, certification, origin, or product availability is being committed" in draft["body"]
    assert draft["prohibited_claim_check"]["passed"] is True
    assert draft["opt_out_sentence"] in draft["body"]
    assert len(draft["personalization_evidence_map"]) == 1
    assert all(step["fresh_approval_required"] for step in draft["follow_up_sequence"])
    assert draft["external_action_executed"] is False


def test_csv_upsert_preserves_zero_values(tmp_path) -> None:
    path = tmp_path / "register.csv"
    path.write_text("id,count\n", encoding="utf-8")
    upsert_csv(path, "id", {"id": "A", "count": 0})
    assert path.read_text(encoding="utf-8").splitlines()[1] == "A,0"
