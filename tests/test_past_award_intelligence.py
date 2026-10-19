from scripts.past_award_intelligence import analyze_past_awards


def test_past_award_intelligence_scores_repeat_buyer() -> None:
    rows = [
        {"buyer_name": "Example Buyer", "product_or_service": "Water filters", "winner": "Supplier A", "award_value_inr": "100000"},
        {"buyer_name": "Example Buyer", "product_or_service": "Water filters AMC", "winner": "Supplier A", "award_value_inr": "120000"},
        {"buyer_name": "Other Buyer", "product_or_service": "Water filters", "winner": "Supplier B", "award_value_inr": "90000"},
    ]
    result = analyze_past_awards(rows, "Example Buyer", "Water")
    assert result["past_tender_count"] == 2
    assert result["similar_category_awards"] == 2
    assert result["known_past_winners"] == ["Supplier A"]
    assert result["incumbent_risk"] == "high"
