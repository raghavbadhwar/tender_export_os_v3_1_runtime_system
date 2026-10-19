from scripts.score_opportunity import evaluate_trader_specific_kills


def test_missing_evidence_watchlists_not_rejects() -> None:
    decision = evaluate_trader_specific_kills({"case_id": "GOV-1"})
    assert decision["status"] == "WATCHLIST"
    assert "incomplete_evidence" in decision["flags"]


def test_manufacturer_only_rejects() -> None:
    decision = evaluate_trader_specific_kills({"manufacturer_only_tender": "TRUE"})
    assert decision["status"] == "REJECTED"
    assert "manufacturer_only_tender" in decision["flags"]


def test_capital_exposure_watchlists() -> None:
    decision = evaluate_trader_specific_kills({"emd_amount_inr": "600000", "max_capital_exposure_inr": "500000"})
    assert decision["status"] == "WATCHLIST"
    assert "emd_fee_pbg_exceeds_capital_limit" in decision["flags"]
