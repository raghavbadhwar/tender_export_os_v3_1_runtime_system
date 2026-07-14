from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from scripts.tender_os_mcp_tools import TenderOSTools
from scripts.tender_os_policy import TenderPolicyEngine
from scripts.update_master_case import VALID_STATUS_TRANSITIONS


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def isolated_tools(tmp_path: Path) -> TenderOSTools:
    data = tmp_path / "data"
    data.mkdir()
    shutil.copy(PROJECT_ROOT / "data" / "master_cases.csv", data / "master_cases.csv")
    (tmp_path / "receipts").mkdir()
    policy = TenderPolicyEngine(
        config_path=PROJECT_ROOT / "config" / "tender_tool_policy.yaml",
        rego_path=PROJECT_ROOT / "policies" / "tender_os_authorization.rego",
        approvals_path=PROJECT_ROOT / "data" / "approvals_receipts.csv",
        receipt_root=tmp_path / "receipts" / "policy_decisions",
        events_file=tmp_path / "data" / "events.jsonl",
        project_root=tmp_path,
    )
    return TenderOSTools(policy=policy, record_decisions=True, project_root=tmp_path)


def first_case(tmp_path: Path) -> dict[str, str]:
    with (tmp_path / "data" / "master_cases.csv").open(newline="", encoding="utf-8") as handle:
        return next(csv.DictReader(handle))


def test_stage_case_transition_is_receipted_and_idempotent(tmp_path: Path) -> None:
    tools = isolated_tools(tmp_path)
    case = first_case(tmp_path)
    target_status = VALID_STATUS_TRANSITIONS[case["status"]][0]
    result = tools.stage_case_transition(
        case_id=case["case_id"],
        from_status=case["status"],
        to_status=target_status,
        evidence_ids=["receipt://fast-kill-001"],
        citations=["outputs/fast_kill_001.json"],
        actor_profile="teos-orchestrator",
        idempotency_key="transition:test:001",
        reason="deterministic fast-kill receipt is present",
    )

    assert result.status == "success"
    assert result.external_side_effects is False
    assert result.approval_required is False
    assert result.policy_receipt_path
    assert result.data["event_type"] == "case.status_changed"
    assert (tmp_path / result.data["receipt_path"]).is_file()
    assert result.data["event_id"]

    replay = tools.stage_case_transition(
        case_id=case["case_id"],
        from_status=case["status"],
        to_status=target_status,
        evidence_ids=["receipt://fast-kill-001"],
        citations=["outputs/fast_kill_001.json"],
        actor_profile="teos-orchestrator",
        idempotency_key="transition:test:001",
        reason="deterministic fast-kill receipt is present",
    )
    assert replay.status == "success"
    assert replay.data["event_id"] == result.data["event_id"]
    assert replay.data["receipt_path"] == result.data["receipt_path"]


def test_internal_write_rejects_invalid_transition_and_missing_case_scope(tmp_path: Path) -> None:
    tools = isolated_tools(tmp_path)
    case = first_case(tmp_path)
    invalid = tools.stage_case_transition(
        case_id=case["case_id"],
        from_status=case["status"],
        to_status="APPROVED",
        evidence_ids=["receipt://bad"],
        citations=["outputs/bad.json"],
        actor_profile="teos-orchestrator",
        idempotency_key="transition:test:bad",
        reason="invalid transition must be rejected",
    )
    assert invalid.status == "failed"
    assert any("transition" in message.lower() for message in invalid.missing_information)

    missing_case = tools.stage_case_transition(
        case_id="",
        from_status=case["status"],
        to_status="FAST_KILL",
        evidence_ids=["receipt://missing-case"],
        citations=["outputs/missing.json"],
        actor_profile="teos-orchestrator",
        idempotency_key="transition:test:missing-case",
        reason="case scope is mandatory",
    )
    assert missing_case.status == "failed"
    assert any("case_id" in message for message in missing_case.missing_information)


def test_attach_case_evidence_records_hash_and_receipt(tmp_path: Path) -> None:
    tools = isolated_tools(tmp_path)
    case = first_case(tmp_path)
    evidence = tmp_path / "evidence.json"
    evidence.write_text('{"source":"fixture"}\n', encoding="utf-8")

    result = tools.attach_case_evidence(
        case_id=case["case_id"],
        evidence_path=str(evidence),
        evidence_type="review_receipt",
        actor_profile="teos-orchestrator",
        idempotency_key="evidence:test:001",
        citations=["evidence.json"],
    )

    assert result.status == "success"
    assert result.data["sha256"]
    assert result.data["event_type"] == "evidence.bundle_created"
    receipt = json.loads((tmp_path / result.data["receipt_path"]).read_text(encoding="utf-8"))
    assert receipt["external_actions_executed"] is False
    assert receipt["case_id"] == case["case_id"]


def test_remaining_internal_write_operations_are_typed_receipted_and_internal(tmp_path: Path) -> None:
    tools = isolated_tools(tmp_path)
    case = first_case(tmp_path)
    case_id = case["case_id"]
    proof = tmp_path / "quote-proof.txt"
    proof.write_text("supplier quote proof fixture\n", encoding="utf-8")
    card = tmp_path / "approval-card.json"
    card.write_text('{"case_id":"fixture"}\n', encoding="utf-8")
    outcome = tmp_path / "outcome.json"
    outcome.write_text('{"verification_status":"VERIFIED"}\n', encoding="utf-8")
    receipt = tmp_path / "projection-receipt.json"
    receipt.write_text('{"projection":"fixture","status":"PASS"}\n', encoding="utf-8")

    results = [
        tools.stage_supplier_candidate(
            case_id=case_id,
            supplier_id="SUP-FIXTURE-001",
            supplier_name="Fixture Supplier",
            source_type="official_registry",
            evidence_path=str(proof),
            actor_profile="supplier-commercial",
            idempotency_key="supplier:test:001",
            citations=["quote-proof.txt"],
        ),
        tools.record_quote_proof_review(
            case_id=case_id,
            supplier_id="SUP-FIXTURE-001",
            quote_id="QUOTE-FIXTURE-001",
            proof_status="VALID",
            quote_proof_path=str(proof),
            reason="fixture proof has a retained path",
            actor_profile="supplier-commercial",
            idempotency_key="quote:test:001",
            citations=["quote-proof.txt"],
        ),
        tools.create_internal_approval_card(
            case_id=case_id,
            proposed_action="send_supplier_quote_request",
            scope_hash="a" * 64,
            card_path=str(card),
            evidence_ids=["receipt://fixture-approval"],
            actor_profile="teos-orchestrator",
            idempotency_key="approval:test:001",
            citations=["approval-card.json"],
        ),
        tools.record_case_outcome(
            case_id=case_id,
            outcome_id="OUTCOME-FIXTURE-001",
            outcome_status="WON",
            evidence_path=str(outcome),
            actor_profile="learning-evaluation",
            idempotency_key="outcome:test:001",
            citations=["outcome.json"],
        ),
        tools.stage_learning_proposal(
            proposal_id="LP-FIXTURE-001",
            case_ids=[case_id],
            proposal_type="test",
            summary="Add a regression fixture for quote-proof review.",
            evidence=["receipt://fixture-learning"],
            tests=["tests/test_tender_os_mcp_internal_writes.py"],
            rollback="Remove the staged proposal before promotion.",
            actor_profile="learning-evaluation",
            idempotency_key="learning:test:001",
            citations=["outcome.json"],
        ),
        tools.reconcile_projection_from_receipt(
            case_id=case_id,
            receipt_path=str(receipt),
            receipt_sha256="",
            projection_name="master_case_projection",
            actor_profile="teos-orchestrator",
            idempotency_key="projection:test:001",
            citations=["projection-receipt.json"],
        ),
    ]

    assert [result.status for result in results] == ["success"] * len(results)
    assert all(result.external_side_effects is False for result in results)
    assert all(result.policy_receipt_path for result in results)
    assert {result.data["event_type"] for result in results} == {
        "supplier.match_candidates_created",
        "supplier.quote_proof_validated",
        "approval.card_created",
        "case.outcome_recorded",
        "learning.proposal_staged",
        "kanban.reconciliation_applied",
    }
