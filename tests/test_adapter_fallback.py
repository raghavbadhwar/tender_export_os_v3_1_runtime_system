"""Proposed test cases to validate adapter fallback pathways when selectors fail."""

import pytest
from pathlib import Path
from scripts.source_adapters.gem_adapter import GeMAdapter
from scripts.source_adapters.cppp_adapter import CPPPAdapter


def test_gem_adapter_fallback_page_text() -> None:
    html = """
    <!doctype html>
    <html><body>
    <div>
      Some unstructured page text where DOM selectors like .bid-card or table rows are completely missing.
      But it contains the critical details in text:
      Tender Reference Number: GEM/2099/B/100001
      Buyer Organisation: Example District Office
      Tender End Date: 31-01-2099
      Estimated Value: INR 250000
    </div>
    </body></html>
    """
    adapter = GeMAdapter(keyword="", limit=5)
    # Force fallback by ensuring selector_config is empty/non-matching
    adapter.selector_config = {}
    items = adapter._extract_listing_opportunities(html, "https://bidplus.gem.gov.in/all-bids")
    
    assert len(items) >= 1
    assert items[0].external_reference == "GEM/2099/B/100001"
    assert items[0].buyer_name == "Example District Office"
    assert items[0].deadline_date == "31-01-2099"


def test_cppp_adapter_fallback_page_text() -> None:
    html = """
    <!doctype html>
    <html><body>
    <div>
      CPPP portal page text where table rows or css class elements fail to parse.
      Tender ID: CPP/2099/ABC/001
      Organisation: Example Ministry
      Submission Deadline: 2099-02-15
      Tender Value: INR 500000
    </div>
    </body></html>
    """
    adapter = CPPPAdapter(keyword="", limit=5)
    adapter.selector_config = {}
    items = adapter.extract_listing_cards(html, "https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata")
    
    assert len(items) >= 1
    assert items[0].external_reference == "CPP/2099/ABC/001"
    assert items[0].buyer_name == "Example Ministry"
    assert items[0].deadline_date == "2099-02-15"
