from pathlib import Path

from scripts.source_adapters.gem_adapter import GeMAdapter

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_gem_selector_fixture_extracts_listing() -> None:
    html = (PROJECT_ROOT / "tests" / "fixtures" / "html" / "gem_listing.html").read_text(encoding="utf-8")
    adapter = GeMAdapter(keyword="water purifier", limit=5)
    items = adapter._extract_listing_opportunities(html, "https://bidplus.gem.gov.in/all-bids")
    assert len(items) == 1
    assert items[0].external_reference == "GEM/2099/B/100001"
    assert "water purifiers" in items[0].opportunity_title.lower()
    assert items[0].deadline_date == "31-01-2099"
