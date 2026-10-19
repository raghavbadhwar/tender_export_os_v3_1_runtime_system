from pathlib import Path

from scripts.source_runtime.document_parser import parse_document
from scripts.source_runtime.evidence_store import EvidenceStore
from scripts.source_runtime.tender_field_extractor import extract_fields
from scripts.source_adapters.base import SourceOpportunity

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_parser_extracts_html_text_tables_and_fields(tmp_path) -> None:
    store = EvidenceStore("GOV", "FIXTURE", "Fixture", "https://example.test", "RUN-1", root=tmp_path)
    path = PROJECT_ROOT / "tests" / "fixtures" / "html" / "tender_detail.html"
    result = parse_document(path, store)
    assert result.parse_status == "PARSED"
    assert result.tables
    opportunity = SourceOpportunity(
        source_name="Fixture",
        source_type="fixture",
        workflow_type="GOV",
        source_url="https://example.test",
        external_reference="FIX-1",
        opportunity_title="Supply of Water Purifiers",
    )
    fields = extract_fields(opportunity, [result.to_dict()], "Fixture")
    assert fields.emd_amount_inr
    assert fields.boq_items
    assert fields.confidence_score >= 50


def test_parser_extracts_csv_tables(tmp_path) -> None:
    store = EvidenceStore("GOV", "CSV", "Fixture", "https://example.test", "RUN-1", root=tmp_path)
    path = PROJECT_ROOT / "tests" / "fixtures" / "documents" / "sample_boq.csv"
    result = parse_document(path, store)
    assert result.parse_status == "PARSED"
    assert "RO water purifier" in result.text
    assert result.extracted_json_path
