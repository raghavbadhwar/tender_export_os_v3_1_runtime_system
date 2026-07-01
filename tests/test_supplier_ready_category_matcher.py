from scripts.low_competition_order_radar import DEFAULT_CATEGORIES, load_yaml_config
from scripts.supplier_ready_category_matcher import match_supplier_ready_categories


CATEGORIES = load_yaml_config(DEFAULT_CATEGORIES)


def test_supplier_ready_category_scores_supplier_and_quote_proof_depth() -> None:
    suppliers = [
        {
            "supplier_id": "SUP-1",
            "supplier_name": "Stationery One",
            "products_supplied": "office stationery toner cartridge printing",
            "city": "Delhi",
            "gem_registered": "TRUE",
            "gst_verification_status": "verified",
            "credit_days_offered": "30",
            "quote_proof_count": "1",
            "last_quote_proof_path": "receipts/supplier_quotes/q1.pdf",
            "is_indicative_price_only": "FALSE",
        },
        {
            "supplier_id": "SUP-2",
            "supplier_name": "Print Supply Two",
            "products_supplied": "printing cartridge conference kit stationery",
            "city": "Noida",
            "gem_registered": "TRUE",
            "gst_verification_status": "verified",
            "credit_days_offered": "15",
            "quote_proof_count": "1",
            "last_quote_proof_path": "receipts/supplier_quotes/q2.pdf",
            "is_indicative_price_only": "FALSE",
        },
    ]

    rows = match_supplier_ready_categories(suppliers, [], CATEGORIES, quote_rows=[])
    stationery = next(row for row in rows if row["category"] == "office_stationery_printing")

    assert stationery["number_of_suppliers"] == 2
    assert stationery["gem_registered_supplier_count"] == 2
    assert stationery["quote_proof_count"] == 2
    assert stationery["supplier_readiness_score"] >= 60


def test_marketplace_listing_price_is_not_quote_proof_for_readiness() -> None:
    suppliers = [
        {
            "supplier_id": "SUP-3",
            "supplier_name": "Listing Supplier",
            "products_supplied": "office stationery toner cartridge",
            "gem_registered": "TRUE",
            "gst_verification_status": "verified",
            "quote_proof_count": "0",
            "is_indicative_price_only": "FALSE",
        }
    ]
    quote_rows = [
        {
            "supplier_id": "SUP-3",
            "supplier_name": "Listing Supplier",
            "quote_proof_type": "marketplace_listing",
            "quote_proof_path": "outputs/evidence/listing.html",
            "marketplace_listing_price": "100",
            "supplier_specific_quote": "FALSE",
            "indicative_price_only": "FALSE",
        }
    ]

    rows = match_supplier_ready_categories(suppliers, [], CATEGORIES, quote_rows=quote_rows)
    stationery = next(row for row in rows if row["category"] == "office_stationery_printing")

    assert stationery["quote_proof_count"] == 0
    assert any("fewer than 2 supplier-specific quote proofs" in gap for gap in stationery["missing_supplier_gaps"])
