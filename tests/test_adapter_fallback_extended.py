import pytest
from scripts.source_adapters.gem_adapter import GeMAdapter
from scripts.source_adapters.cppp_adapter import CPPPAdapter

def test_gem_adapter_empty_text() -> None:
    # Test completely empty HTML structure
    html = "<html><body></body></html>"
    adapter = GeMAdapter(keyword="stationery", limit=5)
    adapter.selector_config = {}
    items = adapter._extract_listing_opportunities(html, "https://bidplus.gem.gov.in/all-bids")
    # Empty HTML -> html_to_text returns empty string or whitespace only.
    # If no text is found, it should return an empty list.
    assert len(items) == 0

def test_gem_adapter_unstructured_fallback() -> None:
    # Test text that doesn't contain a valid bid pattern but is not empty
    html = "<html><body>Some random text without bid numbers. Only mentions stationery.</body></html>"
    adapter = GeMAdapter(keyword="stationery", limit=5)
    adapter.selector_config = {}
    items = adapter._extract_listing_opportunities(html, "https://bidplus.gem.gov.in/all-bids")
    # Should fall back to the GEM-LISTING-UNSTRUCTURED record
    assert len(items) == 1
    assert items[0].external_reference == "GEM-LISTING-UNSTRUCTURED"
    assert items[0].opportunity_title == "stationery"

def test_gem_adapter_mismatched_missing_fields() -> None:
    # Test text with bid pattern but missing date, buyer, value.
    html = """
    <html><body>
    GEM/2026/B/999999
    Just a random chunk with a bid reference.
    </body></html>
    """
    adapter = GeMAdapter(keyword="", limit=5)
    adapter.selector_config = {}
    items = adapter._extract_listing_opportunities(html, "https://bidplus.gem.gov.in/all-bids")
    assert len(items) == 1
    assert items[0].external_reference == "GEM/2026/B/999999"
    assert items[0].buyer_name == ""
    assert items[0].deadline_date == ""
    # Resolved: parsed tender ID is now skipped as estimated value
    assert items[0].estimated_value_inr == ""

def test_gem_adapter_first_chunk_keyword_bypass() -> None:
    # Test if the keyword check is NOT bypassed on the first chunk
    html = """
    <html><body>
    GEM/2026/B/000001
    First chunk has a bid but does not contain the keyword.
    
    GEM/2026/B/000002
    Second chunk has a bid and contains the keyword: stationery.
    
    GEM/2026/B/000003
    Third chunk has a bid and does not contain keyword.
    </body></html>
    """
    # Keyword set to "stationery"
    adapter = GeMAdapter(keyword="stationery", limit=5)
    adapter.selector_config = {}
    items = adapter._extract_listing_opportunities(html, "https://bidplus.gem.gov.in/all-bids")
    
    extracted_refs = [item.external_reference for item in items]
    
    # First chunk should now fail the keyword check and be skipped.
    assert "GEM/2026/B/000001" not in extracted_refs
    assert "GEM/2026/B/000002" in extracted_refs
    assert "GEM/2026/B/000003" not in extracted_refs


def test_gem_adapter_extracts_live_bidplus_cards_without_ra_or_static_links() -> None:
    html = """
    <div id="bidCard">
      <div class="card">
        <div class="block_header">
          <p class="bid_no"><span>Bid No.:</span><a class="bid_no_hover" href="showbidDocument/9197112">GEM/2026/B/7421049</a></p>
          <p class="bid_no"><span>RA NO:</span><a class="bid_no_hover" href="/showradocumentPdf/9588175">GEM/2026/R/695819</a></p>
        </div>
        <div class="card-body"><div class="row">
          <div class="col-md-4"><div class="row"><strong>Items:</strong><a data-content="Public Wi-Fi Solution implementation at Goa International Airport">Public Wi-Fi Solution...</a></div></div>
          <div class="col-md-5"><div class="row"><strong>Department Name And Address:</strong></div><div class="row">Ministry of Civil Aviation<br/>Airports Authority of India</div></div>
          <div class="col-md-3"><div class="row"><strong>End Date:</strong><span class="end_date">13-07-2026 1:21 PM</span></div></div>
        </div></div>
      </div>
    </div>
    """
    adapter = GeMAdapter(keyword="", limit=5)
    items = adapter._extract_listing_opportunities(html, "https://bidplus.gem.gov.in/all-bids")

    assert len(items) == 1
    assert items[0].external_reference == "GEM/2026/B/7421049"
    assert items[0].opportunity_title == "Public Wi-Fi Solution implementation at Goa International Airport"
    assert items[0].source_url == "https://bidplus.gem.gov.in/showbidDocument/9197112"
    assert "Airports Authority of India" in items[0].buyer_name
    assert items[0].deadline_date == "13-07-2026 1:21 PM"

def test_cppp_adapter_empty_text() -> None:
    html = "<html><body></body></html>"
    adapter = CPPPAdapter(keyword="stationery", limit=5)
    adapter.selector_config = {}
    items = adapter.extract_listing_cards(html, "https://eprocure.gov.in/cppp")
    assert len(items) == 0

def test_cppp_adapter_unstructured_fallback() -> None:
    # CPPPAdapter now appends a CPP-LISTING-UNSTRUCTURED record
    html = "<html><body>Some random text without bid numbers. Only mentions stationery.</body></html>"
    adapter = CPPPAdapter(keyword="stationery", limit=5)
    adapter.selector_config = {}
    items = adapter.extract_listing_cards(html, "https://eprocure.gov.in/cppp")
    assert len(items) == 1
    assert items[0].external_reference == "CPP-LISTING-UNSTRUCTURED"
    assert items[0].opportunity_title == "stationery"

def test_cppp_adapter_mismatched_missing_fields() -> None:
    html = """
    <html><body>
    CPP/2026/ABC/123
    Just a random chunk with a bid reference.
    </body></html>
    """
    adapter = CPPPAdapter(keyword="", limit=5)
    adapter.selector_config = {}
    items = adapter.extract_listing_cards(html, "https://eprocure.gov.in/cppp")
    assert len(items) == 1
    assert items[0].external_reference == "CPP/2026/ABC/123"
    assert items[0].buyer_name == ""
    assert items[0].deadline_date == ""
    assert items[0].estimated_value_inr == ""

def test_cppp_adapter_mismatched_missing_fields_large_digits() -> None:
    # Test CPPPAdapter matching the tender ID as estimated value when it contains 5+ digits
    html = """
    <html><body>
    CPP/2026/ABC/999999
    Just a random chunk with a bid reference.
    </body></html>
    """
    adapter = CPPPAdapter(keyword="", limit=5)
    adapter.selector_config = {}
    items = adapter.extract_listing_cards(html, "https://eprocure.gov.in/cppp")
    assert len(items) == 1
    assert items[0].external_reference == "CPP/2026/ABC/999999"
    assert items[0].buyer_name == ""
    assert items[0].deadline_date == ""
    # Resolved: parsed tender ID is now skipped as estimated value
    assert items[0].estimated_value_inr == ""

def test_cppp_adapter_first_chunk_keyword_bypass() -> None:
    html = """
    <html><body>
    CPP/2026/ABC/001
    First chunk has a bid but does not contain the keyword.
    
    CPP/2026/ABC/002
    Second chunk has a bid and contains the keyword: stationery.
    
    CPP/2026/ABC/003
    Third chunk has a bid and does not contain keyword.
    </body></html>
    """
    adapter = CPPPAdapter(keyword="stationery", limit=5)
    adapter.selector_config = {}
    items = adapter.extract_listing_cards(html, "https://eprocure.gov.in/cppp")
    
    extracted_refs = [item.external_reference for item in items]
    
    # First chunk should now fail the keyword check and be skipped.
    assert "CPP/2026/ABC/001" not in extracted_refs
    assert "CPP/2026/ABC/002" in extracted_refs
    assert "CPP/2026/ABC/003" not in extracted_refs
