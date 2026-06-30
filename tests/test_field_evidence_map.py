from pathlib import Path

from scripts.source_adapters.base import SourceOpportunity
from scripts.source_runtime.document_parser import parse_document
from scripts.source_runtime.tender_field_extractor import extract_fields

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_critical_fields_include_evidence_references() -> None:
    result = parse_document(PROJECT_ROOT / "tests" / "fixtures" / "html" / "tender_detail.html")
    opportunity = SourceOpportunity(
        source_name="Fixture",
        source_type="fixture",
        workflow_type="GOV",
        source_url="https://example.test/tender",
        external_reference="FIX-1",
        opportunity_title="Supply of Water Purifiers",
    )
    fields = extract_fields(opportunity, [result.to_dict()], "Fixture")
    assert fields.emd_amount_inr
    assert fields.field_evidence["emd_amount_inr"]["evidence_file"].endswith("tender_detail.html")
    assert fields.field_evidence["boq_items"]["extraction_method"] == "table_classifier"
