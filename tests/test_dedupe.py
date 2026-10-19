import csv

from scripts.source_adapters.base import SourceOpportunity
from scripts.source_runtime.dedupe import DedupeEngine


def test_dedupe_matches_existing_source_url(tmp_path) -> None:
    register = tmp_path / "master_cases.csv"
    headers = ["case_id", "workflow_type", "source_url", "opportunity_title", "buyer_name", "deadline_date", "source_name", "product_or_service"]
    with register.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerow({"case_id": "GOV-20260630-001", "workflow_type": "GOV", "source_url": "https://example.test/tender/1", "opportunity_title": "Tender", "buyer_name": "Buyer", "deadline_date": "2026-07-10"})
    engine = DedupeEngine(register)
    opportunity = SourceOpportunity("Test", "fixture", "GOV", "https://example.test/tender/1", "NEW", "Tender")
    assert engine.find_duplicate(opportunity) == "GOV-20260630-001"
