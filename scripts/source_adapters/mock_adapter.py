"""Fixture-backed source adapter used for safe tests."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from scripts.source_adapters.base import DeepExtractedFields, DeepSourceOpportunity, SourceOpportunity
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from base import DeepExtractedFields, DeepSourceOpportunity, SourceOpportunity  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "sources" / "mock_opportunities.json"


class MockSourceAdapter:
    name = "mock"

    def __init__(self, fixture: Path = DEFAULT_FIXTURE) -> None:
        self.fixture = fixture

    def scan(self) -> list[SourceOpportunity]:
        rows = json.loads(self.fixture.read_text(encoding="utf-8"))
        return [SourceOpportunity(**row) for row in rows]

    def deep_read(self, opportunity: SourceOpportunity) -> DeepSourceOpportunity:
        extracted = DeepExtractedFields(
            buyer_organisation=opportunity.buyer_name,
            tender_id=opportunity.external_reference,
            bid_number=opportunity.external_reference,
            title=opportunity.opportunity_title,
            workflow_type=opportunity.workflow_type,
            source_portal=opportunity.source_name,
            source_url=opportunity.source_url,
            product_or_service=opportunity.product_or_service,
            tender_value_inr=opportunity.estimated_value_inr,
            bid_end_date=opportunity.deadline_date,
            missing_fields=["deep_evidence_bundle"],
            confidence_score=45,
        )
        return DeepSourceOpportunity(
            shallow=opportunity,
            extracted=extracted,
            extraction_status="MOCK_DEEP_READ",
            blocker_status=opportunity.blocker_status,
            citations=opportunity.citations,
        )
