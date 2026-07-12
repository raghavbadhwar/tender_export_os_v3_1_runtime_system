"""Proposed test cases to validate Kanban state synchronization and drift reconciliation."""

import json
from pathlib import Path
from scripts.reconcile_hermes_kanban import build_plan, desired_task


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
