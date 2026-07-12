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


def test_ungm_live_div_table_shape_extracts_notice_fields() -> None:
    html = """
    <div id="tblNotices"><div class="tableBody">
      <div class="tableRow dataRow notice-table" data-noticeid="306541">
        <div class="tableCell resultTitle"><span class="ungm-title">Supply of leather safety boots</span><a href="/Public/Notice/306541">Open</a></div>
        <div class="tableCell deadline">12-Jul-2026 00:00 (GMT -12.00)</div>
        <div class="tableCell resultAgency">UNRWA</div>
        <div class="tableCell resultInfo1" data-description="Reference">3126000540</div>
      </div>
    </div></div>
    """
    adapter = UNGMAdapter(limit=1)

    items = adapter.extract_listing_cards(html, "https://www.ungm.org/Public/Notice")

    assert items[0].external_reference == "3126000540"
    assert items[0].opportunity_title == "Supply of leather safety boots"
    assert items[0].buyer_name == "UNRWA"
    assert items[0].source_url == "https://www.ungm.org/Public/Notice/306541"
