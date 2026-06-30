from pathlib import Path

from scripts.source_adapters.ungm_adapter import UNGMAdapter

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_ungm_selector_fixture_extracts_listing() -> None:
    html = (PROJECT_ROOT / "tests" / "fixtures" / "html" / "ungm_listing.html").read_text(encoding="utf-8")
    adapter = UNGMAdapter(keyword="hygiene", limit=5)
    items = adapter.extract_listing_cards(html, "https://www.ungm.org/Public/Notice")
    assert len(items) == 1
    assert items[0].workflow_type == "EXPORT"
    assert items[0].external_reference == "UNGM-2099-001"
    assert items[0].buyer_name == "Example UN Agency"
