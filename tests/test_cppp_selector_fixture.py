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


def test_cppp_live_table_shape_does_not_shift_dates_into_identity_fields() -> None:
    html = """
    <table><tbody><tr>
      <td>1.</td><td>11-Jul-2026 06:55 PM</td><td>25-Jul-2026 05:00 PM</td>
      <td>27-Jul-2026 11:30 AM</td>
      <td><a href="/cppp/tendersfullview/example">MN08129</a>/MSRRDA/E-TENDER/PMGSY-III/NIT-6/2026_CESQC_148640_49</td>
      <td>National Rural Roads Development Agency (NRRDA)</td><td>--</td>
    </tr></tbody></table>
    """
    adapter = CPPPAdapter(limit=1)

    items = adapter.extract_listing_cards(html, "https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata")

    assert items[0].external_reference == "MN08129"
    assert "MSRRDA/E-TENDER" in items[0].opportunity_title
    assert items[0].buyer_name == "National Rural Roads Development Agency (NRRDA)"
    assert items[0].deadline_date == "25-Jul-2026 05:00 PM"
    assert items[0].source_url.endswith("/cppp/tendersfullview/example")
    assert items[0].estimated_value_inr == ""
