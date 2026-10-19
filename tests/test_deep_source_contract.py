from scripts.source_adapters.base import (
    DeepExtractedFields,
    DeepSourceAdapter,
    DeepSourceOpportunity,
    SourceDocument,
    SourceOpportunity,
)
from scripts.source_adapters.mock_adapter import MockSourceAdapter


def test_deep_contract_dataclasses_serialize() -> None:
    shallow = SourceOpportunity(
        source_name="Test",
        source_type="fixture",
        workflow_type="GOV",
        source_url="https://example.test",
        external_reference="T-1",
        opportunity_title="Fixture tender",
    )
    document = SourceDocument(
        document_id="doc1",
        document_type="pdf",
        document_name="nit.pdf",
        source_url="https://example.test/nit.pdf",
        local_path="outputs/evidence/GOV/T-1/downloads/nit.pdf",
        sha256="abc",
        downloaded_at="2026-06-30T00:00:00+00:00",
    )
    extracted = DeepExtractedFields(title="Fixture tender", confidence_score=80)
    deep = DeepSourceOpportunity(shallow=shallow, extracted=extracted, documents=[document])
    assert deep.to_dict()["documents"][0]["document_name"] == "nit.pdf"


def test_mock_adapter_still_scans_and_deep_reads() -> None:
    adapter: DeepSourceAdapter = MockSourceAdapter()
    opportunities = adapter.scan()
    assert opportunities
    result = adapter.deep_read(opportunities[0])
    assert result.shallow.external_reference == opportunities[0].external_reference
    assert result.extraction_status == "MOCK_DEEP_READ"
