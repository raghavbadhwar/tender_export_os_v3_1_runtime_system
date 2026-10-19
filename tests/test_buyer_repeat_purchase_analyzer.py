from scripts.buyer_repeat_purchase_analyzer import analyze_repeat_buyers
from scripts.low_competition_order_radar import DEFAULT_CATEGORIES, load_yaml_config


CATEGORIES = load_yaml_config(DEFAULT_CATEGORIES)


def test_repeat_buyer_is_scored_by_category_history() -> None:
    cases = [
        {
            "case_id": "GOV-BUY-001",
            "buyer_name": "District Training Institute",
            "buyer_type": "Government",
            "opportunity_title": "Office stationery and toner cartridge",
            "product_or_service": "office stationery toner",
            "estimated_value_inr": "100000",
        },
        {
            "case_id": "GOV-BUY-002",
            "buyer_name": "District Training Institute",
            "buyer_type": "Government",
            "opportunity_title": "Printing and conference kit material",
            "product_or_service": "printing conference kit",
            "estimated_value_inr": "150000",
        },
        {
            "case_id": "GOV-BUY-003",
            "buyer_name": "District Training Institute",
            "buyer_type": "Government",
            "opportunity_title": "Office stationery rate contract",
            "product_or_service": "office stationery",
            "estimated_value_inr": "120000",
        },
    ]

    rows = analyze_repeat_buyers(cases, [], [], CATEGORIES)

    assert rows[0]["buyer_name"] == "District Training Institute"
    assert rows[0]["past_tender_count"] == 3
    assert rows[0]["similar_category_awards"] >= 2
    assert rows[0]["buyer_repeat_score"] >= 80
    assert "stationery" in " ".join(rows[0]["next_watch_keywords"]).lower()


def test_source_records_count_toward_repeat_buyer_watch() -> None:
    source_records = [
        {
            "external_reference": "SRC-1",
            "title": "RO water purifier filter replacement",
            "buyer": "City Hospital",
        },
        {
            "external_reference": "SRC-2",
            "title": "AMC of RO water cooler",
            "buyer": "City Hospital",
        },
    ]

    rows = analyze_repeat_buyers([], [], source_records, CATEGORIES)

    assert rows[0]["buyer_name"] == "City Hospital"
    assert rows[0]["past_tender_count"] == 2
    assert "RO AMC" in rows[0]["next_watch_keywords"]
