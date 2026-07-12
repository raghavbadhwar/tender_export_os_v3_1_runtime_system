"""Proposed test cases to validate India Business Portal adapter listing extraction."""

from pathlib import Path
from scripts.source_adapters.india_business_portal_adapter import IndiaBusinessPortalAdapter


def test_india_business_portal_extracts_listing() -> None:
    html_path = Path(__file__).resolve().parent / "proposed_india_business_portal_listing.html"
    html = html_path.read_text(encoding="utf-8")
    
    adapter = IndiaBusinessPortalAdapter(keyword="organic tea", limit=5)
    # Inject the selector config since the actual YAML is staged in explorer_1
    adapter.selector_config = {
        "listing_card": [".rfq-card"],
        "fields": {
            "tender_id": [".rfq-id"],
            "title": [".rfq-title"],
            "buyer": [".buyer"],
            "deadline": [".deadline"],
            "value": [".value"],
            "detail_link": ["a.detail-link"],
            "document_link": ["a.document-link"]
        }
    }
    
    items = adapter._extract_listing_opportunities(html, "https://www.indiabusinessportal.gov.in")
    assert len(items) == 1
    assert items[0].workflow_type == "EXPORT"
    assert items[0].external_reference == "IBP-2026-001"
    assert items[0].buyer_name == "Dubai Import Corp"
    assert items[0].deadline_date == "2026-12-31"
