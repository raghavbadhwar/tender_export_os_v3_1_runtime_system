from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.create_case_task_graph import (
    DEFAULT_GRAPH_SPEC,
    build_graph,
    execute_graph,
    load_graph_spec,
    validate_graph_spec,
)


REQUIRED_STAGE_FIELDS = {
    "key",
    "assignee",
    "parents",
    "required_inputs",
    "expected_outputs",
    "approval_boundary",
    "retry_limit",
    "max_runtime_seconds",
    "completion_validator",
    "idempotency_key_template",
}

REQUIRED_HANDOFF_FIELDS = {
    "case_id",
    "workflow_type",
    "stage",
    "source_event_ids",
    "input_artifacts",
    "required_output_schema",
    "approval_required",
    "deadline",
    "stop_conditions",
    "next_profile",
}


def test_case_task_graph_config_has_complete_gov_and_export_dags() -> None:
    spec = load_graph_spec(DEFAULT_GRAPH_SPEC)

    assert set(spec["workflows"]) == {"GOV", "EXPORT"}
    for workflow in spec["workflows"].values():
        stages = workflow["stages"]
        assert len(stages) >= 10
        assert all(REQUIRED_STAGE_FIELDS <= set(stage) for stage in stages)
        keys = {stage["key"] for stage in stages}
        assert all(set(stage["parents"]) <= keys for stage in stages)


def test_build_graph_embeds_typed_handoff_and_needs_input_approval_block() -> None:
    graph = build_graph(
        {
            "case_id": "GOV-20990101-001",
            "workflow_type": "GOV",
            "status": "NEW",
            "opportunity_title": "Fixture",
            "buyer_name": "Fixture buyer",
            "deadline_date": "2099-01-31",
        }
    )
    by_key = {task["key"]: task for task in graph["tasks"]}

    for task in graph["tasks"]:
        handoff = task["handoff"]
        assert REQUIRED_HANDOFF_FIELDS <= set(handoff)
        assert json.dumps(handoff, sort_keys=True) in task["body"]
        assert task["idempotency_key"] == f"teos:GOV-20990101-001:{task['key']}:v1"

    assert by_key["approval"]["initial_status"] == "blocked"
    assert by_key["approval"]["block_kind"] == "needs_input"
    assert by_key["approval"]["handoff"]["approval_required"] is True
    assert by_key["execution"]["external_effect"] is False
    assert by_key["execution"]["max_retries"] == 0


def test_gov_graph_keeps_deterministic_review_parallel_proof_and_post_submission_milestones_distinct() -> None:
    graph = build_graph(
        {
            "case_id": "GOV-20990101-003",
            "workflow_type": "GOV",
            "status": "NEW",
            "opportunity_title": "Fixture",
            "buyer_name": "Fixture buyer",
            "deadline_date": "2099-01-31",
        }
    )
    by_key = {task["key"]: task for task in graph["tasks"]}

    assert set(by_key) >= {
        "intake",
        "fast_kill",
        "fast_kill_critic",
        "deep_read",
        "supplier",
        "historical_intelligence",
        "pricing",
        "compliance",
        "artifacts",
        "approval",
        "execution",
        "evaluation_award",
        "delivery_payment",
        "learning",
    }
    assert by_key["fast_kill_critic"]["parents"] == ["GOV-20990101-003:fast_kill"]
    assert by_key["deep_read"]["parents"] == ["GOV-20990101-003:fast_kill_critic"]
    assert by_key["historical_intelligence"]["parents"] == ["GOV-20990101-003:deep_read"]
    assert by_key["pricing"]["parents"] == [
        "GOV-20990101-003:supplier",
        "GOV-20990101-003:historical_intelligence",
    ]
    assert by_key["compliance"]["parents"] == ["GOV-20990101-003:deep_read"]
    assert set(by_key["artifacts"]["parents"]) == {
        "GOV-20990101-003:pricing",
        "GOV-20990101-003:compliance",
    }
    assert by_key["artifacts"]["completion_validator"] == "bid_pack_verification"
    assert by_key["artifacts"]["handoff"]["input_artifacts"] == [
        "outputs/case_reports/GOV-20990101-003/supplier_532_GOV-20990101-003.json",
        "outputs/case_reports/GOV-20990101-003/pricing_GOV-20990101-003.json",
        "outputs/case_reports/GOV-20990101-003/pricing_GOV-20990101-003.md",
        "outputs/case_reports/GOV-20990101-003/compliance_draft_GOV-20990101-003.json",
        "outputs/case_reports/GOV-20990101-003/compliance_draft_GOV-20990101-003.md",
    ]
    assert "outputs/bid_packs/GOV-20990101-003/verification_receipt.json" in by_key["artifacts"]["body"]
    assert "receipts/plugin_runs/GOV-20990101-003_bid_pack.json" in by_key["approval"]["body"]
    assert by_key["evaluation_award"]["parents"] == ["GOV-20990101-003:execution"]
    assert by_key["delivery_payment"]["parents"] == ["GOV-20990101-003:evaluation_award"]
    assert by_key["learning"]["parents"] == ["GOV-20990101-003:delivery_payment"]


def test_export_graph_separates_market_hypothesis_contact_rfq_quote_and_cash_milestones() -> None:
    graph = build_graph(
        {
            "case_id": "EXP-20990101-003",
            "workflow_type": "EXPORT",
            "status": "WATCHLIST",
            "opportunity_title": "Fixture",
            "buyer_name": "Fixture buyer",
            "deadline_date": "2099-01-31",
        }
    )
    by_key = {task["key"]: task for task in graph["tasks"]}

    assert set(by_key) >= {
        "research_thesis", "target_staging", "buyer_verification", "contact_path_proof", "outreach_approval",
        "first_contact", "reply_triage", "rfq_verification", "supplier", "compliance", "pricing", "quote_pack",
        "quote_approval", "quote_delivery", "negotiation_drafts", "order_capture", "shipment_invoice_payment",
        "repeat_buyer_learning",
    }
    assert by_key["target_staging"]["parents"] == ["EXP-20990101-003:research_thesis"]
    assert by_key["rfq_verification"]["parents"] == ["EXP-20990101-003:reply_triage"]
    assert set(by_key["pricing"]["parents"]) == {
        "EXP-20990101-003:supplier", "EXP-20990101-003:compliance",
    }
    assert by_key["outreach_approval"]["initial_status"] == "blocked"
    assert by_key["quote_approval"]["initial_status"] == "blocked"
    assert by_key["first_contact"]["external_effect"] is False
    assert by_key["quote_delivery"]["external_effect"] is False


def test_validate_graph_spec_rejects_unknown_parent(tmp_path: Path) -> None:
    spec = load_graph_spec(DEFAULT_GRAPH_SPEC)
    spec["workflows"]["GOV"]["stages"][0]["parents"] = ["missing-stage"]

    with pytest.raises(ValueError, match="unknown parent"):
        validate_graph_spec(spec)


def test_validate_graph_spec_rejects_unknown_completion_validator() -> None:
    spec = load_graph_spec(DEFAULT_GRAPH_SPEC)
    spec["workflows"]["GOV"]["stages"][0]["completion_validator"] = "unvalidated_stage"

    with pytest.raises(ValueError, match="unknown completion validator"):
        validate_graph_spec(spec)


def test_execute_graph_fails_before_board_write_for_unknown_assignee() -> None:
    graph = build_graph(
        {
            "case_id": "EXP-20990101-001",
            "workflow_type": "EXPORT",
            "status": "NEW",
            "opportunity_title": "Fixture",
            "buyer_name": "Fixture buyer",
            "deadline_date": "2099-01-31",
        }
    )
    calls: list[list[str]] = []

    def should_not_run(command: list[str]) -> dict:
        calls.append(command)
        return {}

    with pytest.raises(ValueError, match="unknown live assignee"):
        execute_graph(graph, live_profiles={"tender-export-os"}, command_runner=should_not_run)

    assert calls == []


def test_reexecuting_graph_reuses_every_versioned_idempotency_key() -> None:
    graph = build_graph(
        {
            "case_id": "GOV-20990101-002",
            "workflow_type": "GOV",
            "status": "NEW",
            "opportunity_title": "Idempotency fixture",
            "buyer_name": "Fixture buyer",
            "deadline_date": "2099-01-31",
        }
    )
    live_profiles = {task["assignee"] for task in graph["tasks"]}
    board_tasks: dict[str, str] = {}

    def idempotent_board(command: list[str]) -> dict:
        if "create" in command:
            key = command[command.index("--idempotency-key") + 1]
            board_tasks.setdefault(key, f"t_{len(board_tasks) + 1:02d}")
            return {"id": board_tasks[key]}
        if "link" in command:
            return {"ok": True}
        raise AssertionError(command)

    first = execute_graph(graph, live_profiles=live_profiles, command_runner=idempotent_board)
    second = execute_graph(graph, live_profiles=live_profiles, command_runner=idempotent_board)

    assert first == second
    assert len(board_tasks) == len(graph["tasks"])
    assert len(set(first.values())) == len(graph["tasks"])
