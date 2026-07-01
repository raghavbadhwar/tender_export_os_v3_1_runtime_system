from scripts.low_competition_order_radar import DEFAULT_KEYWORDS, load_yaml_config
from scripts.retender_corrigenda_watch import detect_retender_corrigenda_records


KEYWORDS = load_yaml_config(DEFAULT_KEYWORDS)


def test_retender_corrigenda_watch_detects_master_case_signals() -> None:
    rows = [
        {
            "case_id": "GOV-RET-001",
            "source_url": "https://example.com/retender",
            "buyer_name": "District Office",
            "opportunity_title": "Retender for AMC of RO water purifier",
            "deadline_date": "2026-07-30",
            "corrigenda_summary": "date extension and revised BOQ",
        }
    ]

    matches = detect_retender_corrigenda_records(rows, [], KEYWORDS)

    assert len(matches) == 1
    assert matches[0]["change_type"] == "RETENDER"
    assert "Re-deep-read public documents" in matches[0]["recommended_action"]


def test_retender_corrigenda_watch_detects_source_fixture_date_extension() -> None:
    source_records = [
        {
            "external_reference": "SRC-EXT-001",
            "title": "Corrigendum: technical bid extended due to single bid received",
            "source_url": "https://example.com/corrigendum",
            "buyer": "Municipal Office",
            "deadline": "2026-08-02",
        }
    ]

    matches = detect_retender_corrigenda_records([], source_records, KEYWORDS)

    assert len(matches) == 1
    assert matches[0]["change_type"] in {"DATE_EXTENSION", "LOW_BIDDER_RECALL", "CORRIGENDUM"}
    assert "single bid received" in " ".join(matches[0]["matched_keywords"]).lower()
