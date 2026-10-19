from __future__ import annotations

from pathlib import Path

import yaml

from scripts.create_case_task_graph import TASKS, build_graph
from scripts.kanban_blocked_task_drain import classify_task


LEGACY_ALIASES = {
    "hermes-chief-operator",
    "gov-tender-radar",
    "export-rfq-radar",
    "supplier-sourcing",
    "pricing-compliance",
    "sales-followup",
    "learning-review",
    "source-health",
    "codex-artifact-factory",
    "chatgpt-boardroom-handoff",
}


def load_yaml(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def test_kanban_board_uses_only_real_registry_profiles() -> None:
    board = load_yaml("config/kanban_board.yaml")
    registry = load_yaml("config/hermes_specialist_profiles.yaml")
    profile_ids = {row["id"] for row in board["profiles"]}

    assert profile_ids == set(registry["profiles"])
    assert not (profile_ids & LEGACY_ALIASES)
    assert board["routing"]["decomposition_profile"] == "teos-orchestrator"
    assert board["routing"]["owner_approval_profile"] == "tender-export-os"
    assert board["routing"]["compatibility_aliases_allowed_as_assignees"] is False


def test_case_graph_has_real_assignees_and_separate_pricing_compliance() -> None:
    board_profiles = {row["id"] for row in load_yaml("config/kanban_board.yaml")["profiles"]}
    assignees = {task["assignee"] for tasks in TASKS.values() for task in tasks}

    assert assignees <= board_profiles
    assert not (assignees & LEGACY_ALIASES)
    for workflow, tasks in TASKS.items():
        by_key = {task["key"]: task for task in tasks}
        assert by_key["pricing"]["assignee"] == "pricing-risk"
        assert by_key["compliance"]["assignee"] == "compliance-due-diligence"
        approval_keys = ["approval"] if workflow == "GOV" else ["outreach_approval", "quote_approval"]
        for key in approval_keys:
            assert by_key[key]["approval_required"] is True
            assert by_key[key]["initial_status"] == "blocked"
            assert by_key[key]["block_kind"] == "needs_input"
            assert by_key[key]["block_reason"] == "owner_approval"
        learning_key = "learning" if workflow == "GOV" else "repeat_buyer_learning"
        assert by_key[learning_key]["assignee"] == "learning-evaluation"


def test_case_graph_uses_versioned_teos_idempotency_keys() -> None:
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

    assert all(task["idempotency_key"] == f"teos:GOV-20990101-001:{task['key']}:v1" for task in graph["tasks"])


def test_blocked_task_routing_splits_pricing_and_compliance() -> None:
    pricing = classify_task({"title": "Pricing margin assumptions"})
    compliance = classify_task({"title": "HSN and origin compliance"})
    supplier = classify_task({"title": "Supplier quote proof"})
    approval = classify_task({"title": "Owner approval required"})

    assert pricing[1] == "pricing-risk"
    assert compliance[1] == "compliance-due-diligence"
    assert supplier[1] == "supplier-commercial"
    assert approval[1] == "tender-export-os"
