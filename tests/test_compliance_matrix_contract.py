from __future__ import annotations

import json
from pathlib import Path

from scripts.compliance_matrix_contract import validate_matrix, write_matrix


def citation() -> dict[str, str | int]:
    return {
        "source_path": "outputs/evidence/private/GOV-1/tender.pdf",
        "source_url": "https://eprocure.gov.in/tender/1",
        "source_kind": "tender_document",
        "source_date": "2099-01-01",
        "primary_source": True,
        "page": 3,
    }


def matrix() -> dict:
    return {
        "schema_version": "compliance_matrix.v1",
        "case_id": "GOV-1",
        "workflow_type": "GOV",
        "generated_at": "2099-01-01T00:00:00+00:00",
        "matrix_status": "DRAFT_READY",
        "clauses": [
            {
                "clause_id": "ELIG-1",
                "requirement_text": "GST registration required",
                "requirement_type": "eligibility",
                "position": "COMPLIES",
                "evidence_citations": [citation()],
                "owner_decision_needed": False,
            },
            {
                "clause_id": "DEL-1",
                "requirement_text": "Delivery within 14 days",
                "requirement_type": "delivery",
                "position": "COMPLIES",
                "evidence_citations": [citation()],
                "owner_decision_needed": False,
            },
        ],
        "unresolved_items": [],
        "external_actions_executed": False,
    }


def test_matrix_requires_explicit_positions_and_citations_for_claims() -> None:
    assert validate_matrix(matrix()) == []

    invalid = matrix()
    invalid["clauses"][0]["position"] = "COMPLIANT"
    invalid["clauses"][0]["evidence_citations"] = []
    errors = validate_matrix(invalid)
    assert any("position must be one of" in error for error in errors)


def test_unknown_or_expert_review_can_never_be_silently_draft_ready() -> None:
    blocked = matrix()
    blocked["clauses"][1] = {
        "clause_id": "CERT-1",
        "requirement_text": "OEM authorization",
        "requirement_type": "certificate",
        "position": "OWNER/EXPERT_REVIEW",
        "reason": "Supplier authorization is not in the evidence bundle",
        "owner_decision_needed": True,
        "evidence_citations": [],
    }
    blocked["matrix_status"] = "BLOCKED"
    blocked["unresolved_items"] = ["OEM authorization"]

    assert validate_matrix(blocked) == []
    blocked["matrix_status"] = "DRAFT_READY"
    assert any("DRAFT_READY matrix may not contain" in error for error in validate_matrix(blocked))


def test_compliance_claim_requires_current_primary_source() -> None:
    stale = matrix()
    stale["generated_at"] = "2101-01-01T00:00:00+00:00"
    errors = validate_matrix(stale)
    assert any("stale by policy" in error for error in errors)

    non_primary = matrix()
    non_primary["clauses"][0]["evidence_citations"][0]["primary_source"] = False
    assert any("primary_source must be true" in error for error in validate_matrix(non_primary))


def test_export_compliance_requires_workflow_specific_source_kind() -> None:
    export = matrix()
    export["case_id"] = "EXP-1"
    export["workflow_type"] = "EXPORT"
    export["clauses"][0]["requirement_type"] = "scomet"
    export["clauses"][0]["evidence_citations"][0]["source_kind"] = "tender_document"

    errors = validate_matrix(export)

    assert any("source_kind tender_document is not allowed for EXPORT/scomet" in error for error in errors)


def test_write_matrix_creates_readable_artifact_and_canonical_event(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    result = write_matrix(matrix(), output_dir=tmp_path / "case", events_path=events, actor="pytest")

    assert result["json_path"].is_file()
    assert result["markdown_path"].is_file()
    event = json.loads(events.read_text(encoding="utf-8").strip())
    assert event["event_type"] == "compliance.matrix_drafted"
    assert event["payload"]["matrix_status"] == "DRAFT_READY"
