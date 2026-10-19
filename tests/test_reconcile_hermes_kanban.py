"""Proposed test cases to validate Kanban state synchronization and drift reconciliation."""

import json
import subprocess
from pathlib import Path
from scripts.reconcile_hermes_kanban import (
    build_event_case_projection,
    build_live_reconciliation_plan,
    build_plan,
    desired_task,
    fetch_live_tasks,
)


def test_desired_task_generation() -> None:
    case = {
        "case_id": "GOV-20260706-001",
        "opportunity_title": "Supply of medical goods",
        "workflow_type": "GOV",
        "status": "SUPPLIER_SEARCH",
        "deadline_date": "2026-07-20",
        "approval_status": "NONE"
    }
    task = desired_task(case)
    assert task["case_id"] == "GOV-20260706-001"
    assert task["board_status"] == "running"
    assert "Complete supplier proof" in task["next_action"]


def test_build_plan_detects_creation_and_update() -> None:
    cases = [
        {
            "case_id": "GOV-001",
            "opportunity_title": "Tender 1",
            "workflow_type": "GOV",
            "status": "NEW",
            "deadline_date": "2026-07-15",
            "approval_status": "NONE"
        },
        {
            "case_id": "EXP-001",
            "opportunity_title": "RFQ 1",
            "workflow_type": "EXPORT",
            "status": "APPROVED",
            "deadline_date": "2026-07-18",
            "approval_status": "APPROVED"
        }
    ]
    current_tasks = {
        "EXP-001": {
            "case_id": "EXP-001",
            "title": "RFQ 1",
            "workflow_type": "EXPORT",
            "board_status": "todo",  # Drift! Desired is "ready" for APPROVED
            "case_status": "WATCHLIST",
            "deadline": "2026-07-18",
            "owner_approval_needed": False,
            "next_action": ""
        }
    }
    
    plan = build_plan(cases, current_tasks)
    actions = plan["actions"]
    
    assert len(actions) == 2
    by_action = {act["case_id"]: act for act in actions}
    
    assert by_action["GOV-001"]["action"] == "create_task"
    assert by_action["EXP-001"]["action"] == "update_task"
    assert "board_status" in by_action["EXP-001"]["diff"]


def test_fetch_live_tasks_uses_real_board_command() -> None:
    calls = []

    def runner(command, **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, '[{"id":"t_1","status":"done"}]', "")

    tasks = fetch_live_tasks(runner=runner)

    assert tasks == [{"id": "t_1", "status": "done"}]
    assert calls == [["hermes", "kanban", "--board", "tender-export-os", "list", "--json"]]


def test_event_case_projection_applies_snapshot_and_updates() -> None:
    events = [
        {
            "event_type": "case.snapshot_imported",
            "case_id": "GOV-1",
            "payload": {"row": {"case_id": "GOV-1", "workflow_type": "GOV", "status": "NEW"}},
        },
        {
            "event_type": "case.updated",
            "case_id": "GOV-1",
            "payload": {"updates": {"status": "WATCHLIST"}},
        },
    ]

    projection = build_event_case_projection(events)

    assert projection["GOV-1"]["status"] == "WATCHLIST"


def test_live_reconciliation_preserves_completed_history_and_is_idempotent() -> None:
    cases = [
        {
            "case_id": "GOV-1",
            "workflow_type": "GOV",
            "status": "NEW",
            "opportunity_title": "Fixture",
            "buyer_name": "Buyer",
            "deadline_date": "2099-01-01",
        }
    ]
    live_tasks = [
        {
            "id": "t_done",
            "title": "GOV-1 — old title",
            "assignee": "gov-tender-intelligence",
            "status": "done",
            "body": 'TEOS_TYPED_HANDOFF_V1\n{"approval_required": false, "case_id": "GOV-1", "deadline": "2099-01-01", "input_artifacts": [], "next_profile": "gov-tender-intelligence", "required_output_schema": "x", "source_event_ids": [], "stage": "intake", "stop_conditions": [], "workflow_type": "GOV"}',
        }
    ]
    event_projection = {"GOV-1": dict(cases[0])}

    first = build_live_reconciliation_plan(cases, event_projection, live_tasks)
    second = build_live_reconciliation_plan(cases, event_projection, live_tasks)

    assert first["actions"] == second["actions"]
    preserved = [action for action in first["actions"] if action["action"] == "preserve_completed_history"]
    assert preserved and preserved[0]["task_id"] == "t_done"
    assert not any(action["action"] == "update_task" and action.get("task_id") == "t_done" for action in first["actions"])
