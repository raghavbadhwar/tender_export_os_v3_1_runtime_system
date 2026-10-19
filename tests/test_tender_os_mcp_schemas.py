from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.tender_os_mcp_tools import (
    InternalCaseTransitionRequest,
    InternalEvidenceAttachmentRequest,
    InternalLearningProposalRequest,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_internal_write_request_schemas_validate_typed_models() -> None:
    fixtures = [
        (
            "internal_case_transition.schema.json",
            InternalCaseTransitionRequest(
                case_id="GOV-FIXTURE-001",
                from_status="WATCHLIST",
                to_status="DEEP_READ",
                evidence_ids=["receipt://fixture"],
                citations=["outputs/fixture.json"],
                actor_profile="teos-orchestrator",
                idempotency_key="transition:schema:001",
                reason="fixture evidence is present",
            ),
        ),
        (
            "internal_evidence_attachment.schema.json",
            InternalEvidenceAttachmentRequest(
                case_id="GOV-FIXTURE-001",
                evidence_path="outputs/fixture.json",
                evidence_type="review_receipt",
                actor_profile="teos-orchestrator",
                idempotency_key="evidence:schema:001",
                citations=["outputs/fixture.json"],
            ),
        ),
        (
            "internal_learning_proposal.schema.json",
            InternalLearningProposalRequest(
                proposal_id="LP-FIXTURE-001",
                case_ids=["GOV-FIXTURE-001"],
                proposal_type="test",
                summary="Add a regression fixture.",
                evidence=["receipt://fixture"],
                tests=["tests/test_tender_os_mcp_schemas.py"],
                rollback="Remove the proposal before promotion.",
                actor_profile="learning-evaluation",
                idempotency_key="learning:schema:001",
                citations=["outputs/fixture.json"],
            ),
        ),
    ]
    for schema_name, model in fixtures:
        schema = json.loads((PROJECT_ROOT / "config" / "schemas" / schema_name).read_text(encoding="utf-8"))
        errors = sorted(Draft202012Validator(schema).iter_errors(model.model_dump(mode="json")), key=lambda error: error.path)
        assert errors == [], [error.message for error in errors]
