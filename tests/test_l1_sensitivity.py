from scripts.gov_tender_pricing_model import l1_sensitivity_table


def test_l1_sensitivity_has_required_scenarios() -> None:
    rows = l1_sensitivity_table(100000, 85000)
    assert len(rows) == 5
    assert rows[0]["scenario"] == "base bid price"
    assert rows[-1]["scenario"] == "competitor -20%"
    assert "decision_warning" in rows[-1]
    assert "cash_risk" in rows[-1]
