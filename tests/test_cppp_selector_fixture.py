from pathlib import Path

from scripts.source_adapters.cppp_adapter import CPPPAdapter

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_cppp_selector_fixture_extracts_listing() -> None:
    html = (PROJECT_ROOT / "tests" / "fixtures" / "html" / "cppp_listing.html").read_text(encoding="utf-8")
    adapter = CPPPAdapter(keyword="data entry", limit=5)
    items = adapter.extract_listing_cards(html, "https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata")
    assert len(items) == 1
    assert items[0].external_reference == "CPP/2099/ABC/001"
    assert items[0].buyer_name == "Example Ministry"
    assert items[0].estimated_value_inr == "INR 500000"
