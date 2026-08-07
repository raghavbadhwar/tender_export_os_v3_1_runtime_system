from __future__ import annotations

import json
from pathlib import Path

from scripts.gov_deep_read_contract import render_markdown, validate_report, write_deep_read


FACT_KEYS = {
    "buyer_name",
    "bid_number",
    "tender_title",
    "publication_date",
    "deadline_date",
    "eligibility",
    "turnover",
    "experience",
    "oem",
    "emd",
    "pbg",
    "required_documents",
    "delivery",
    "payment",
    "penalties",
    "evaluation_method",
    "reverse_auction",
    "inspection",
    "warranty",
}


def citation(page: int = 1) -> dict[str, str | int]:
    return {
        "source_path": "outputs/evidence/private/GOV-1/tender.pdf",
        "source_url": "https://eprocure.gov.in/tender/GOV-1",
        "page": page,
        "section": "fixture",
    }


def fact(value: str) -> dict:
    return {"status": "EXTRACTED", "value": value, "reason": "", "citations": [citation()]}


def report() -> dict:
    return {
        "schema_version": "gov_deep_read.v1",
        "case_id": "GOV-20990101-001",
        "workflow_type": "GOV",
        "extraction_status": "COMPLETE",
        "generated_at": "2099-01-02T10:00:00+00:00",
        "source_documents": [
            {
                "source_path": "outputs/evidence/private/GOV-1/tender.pdf",
                "source_url": "https://eprocure.gov.in/tender/GOV-1",
                "sha256": "a" * 64,
                "document_type": "NIT",
                "page_count": 12,
            }
        ],
        "facts": {key: fact(f"Observed {key}") for key in FACT_KEYS},
        "corrigenda": [
            {
                "status": "NONE_FOUND",
                "summary": "No corrigendum identified in the packet.",
                "citations": [citation(2)],
            }
        ],
        "boq_lines": [
            {
                "line_id": "1",
                "description": "Supply of water filters",
                "quantity": "10",
                "unit": "each",
                "specification": "As cited",
                "citations": [citation(3)],
            }
        ],
        "ambiguous_clauses": [
            {
                "topic": "eligibility",
                "status": "AMBIGUOUS",
                "summary": "Clarification is required before relying on this requirement.",
                "citations": [citation(4)],
            }
        ],
        "recommended_case_status": "SUPPLIER_SEARCH",
        "external_actions_executed": False,
    }


def test_gov_deep_read_contract_requires_all_risky_sections_and_page_citations() -> None:
    value = report()

    assert validate_report(value) == []
    markdown = render_markdown(value)
    assert "Government Tender Deep Read" in markdown
    assert "Supply of water filters" in markdown

    invalid = report()
    invalid["facts"]["emd"] = {"status": "EXTRACTED", "value": "5000", "reason": "", "citations": []}
    invalid["facts"]["payment"] = {"status": "UNKNOWN", "value": "", "reason": "", "citations": []}
    errors = validate_report(invalid)

    assert any("facts.emd" in error and "citation" in error for error in errors)
    assert any("facts.payment" in error and "reason" in error for error in errors)


def test_gov_deep_read_write_creates_versioned_json_markdown_and_event(tmp_path: Path) -> None:
    value = report()
    output_dir = tmp_path / "case"
    events_path = tmp_path / "events.jsonl"

    result = write_deep_read(value, output_dir=output_dir, events_path=events_path, actor="pytest")

    assert result["json_path"].is_file()
    assert result["markdown_path"].is_file()
    event = json.loads(events_path.read_text(encoding="utf-8").strip())
    assert event["event_type"] == "case.deep_read_recorded"
    assert event["payload"]["schema_version"] == "gov_deep_read.v1"
