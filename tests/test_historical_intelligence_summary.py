from scripts.build_historical_intelligence_summary import build_summary


def test_historical_summary_uses_example_fallback_for_empty_live_tables() -> None:
    summary = build_summary(use_examples_if_empty=True)

    assert summary["table_count"] == 5
    assert summary["ready_for_ml"] is True
    assert summary["tables"]["historical_tender_notices"]["source_used"].endswith(".example.csv")
    assert summary["evidence_level_counts"]["PUBLIC_LISTING_ONLY"] >= 1
