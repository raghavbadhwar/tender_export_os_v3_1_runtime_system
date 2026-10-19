from scripts.gov_tender_pricing_model import calculate_gov_pricing


def test_gov_pricing_includes_working_capital_and_emd_cost() -> None:
    result = calculate_gov_pricing(
        100000,
        emd_amount=50000,
        emd_lock_days=60,
        supplier_payment_day=0,
        buyer_payment_day=45,
    )
    assert result.working_capital_gap_days == 45
    assert result.cash_gap_inr > 0
    assert result.emd_opportunity_cost_inr > 0
    assert result.final_bid_price_inr > result.direct_costs_inr
