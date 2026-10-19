from __future__ import annotations

import json
from pathlib import Path

from scripts.compliance_critic import review_matrix, validate_review, write_review


def citation(kind: str = "tender_document") -> dict:
    return {
        "source_path": "outputs/evidence/private/case/source.pdf",
        "source_kind": kind,
        "source_date": "2099-01-01",
        "primary_source": True,
        "page": 1,
    }


def matrix(**updates) -> dict:
    value = {
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
            }
        ],
        "unresolved_items": [],
        "external_actions_executed": False,
    }
    value.update(updates)
    return value


def test_compliance_critic_passes_low_risk_valid_matrix_without_final_authority() -> None:
    review = review_matrix(matrix())

    assert validate_review(review) == []
    assert review["status"] == "PASS_NO_CRITIC_REQUIRED"
    assert review["critic_required"] is False
    assert review["can_write_final_state"] is False
    assert review["external_actions_executed"] is False


def test_compliance_critic_requires_review_for_high_risk_export_source() -> None:
    review = review_matrix(
        matrix(
            case_id="EXP-1",
            workflow_type="EXPORT",
            clauses=[
                {
                    "clause_id": "HSN-1",
                    "requirement_text": "Candidate ITC-HS classification must remain draft",
                    "requirement_type": "hsn_itchs",
                    "position": "COMPLIES",
                    "evidence_citations": [citation("dgft")],
                    "owner_decision_needed": False,
                }
            ],
        )
    )

    assert review["status"] == "REVIEW_REQUIRED"
    assert review["critic_required"] is True
    assert review["high_risk_clauses"] == ["HSN-1"]


def test_compliance_critic_blocks_scomet_or_stale_source_signal() -> None:
    review = review_matrix(
        matrix(
            case_id="EXP-2",
            workflow_type="EXPORT",
            clauses=[
                {
                    "clause_id": "SCOMET-1",
                    "requirement_text": "SCOMET suspected",
                    "requirement_type": "scomet",
                    "position": "OWNER/EXPERT_REVIEW",
                    "reason": "Potential SCOMET match.",
                    "evidence_citations": [citation("scomet_list")],
                    "owner_decision_needed": True,
                }
            ],
            matrix_status="BLOCKED",
            unresolved_items=["SCOMET specialist review required"],
        )
    )

    assert review["status"] == "BLOCKED"
    assert review["scomet_signal"] is True
    assert any("SCOMET" in gap for gap in review["gaps"])


def test_write_compliance_critic_creates_internal_event(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    review = review_matrix(matrix())

    result = write_review(review, output_dir=tmp_path / "case", events_path=events)

    assert Path(result["json_path"]).is_file()
    event = json.loads(events.read_text(encoding="utf-8").strip())
    assert event["event_type"] == "compliance.critic_reviewed"
    assert event["payload"]["critic_required"] is False
