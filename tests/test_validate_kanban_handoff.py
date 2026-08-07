from __future__ import annotations

import json
from pathlib import Path

from scripts.create_case_task_graph import build_graph
from scripts.validate_kanban_handoff import (
    can_auto_promote,
    validate_completion,
    validate_parent_results,
    validate_task_input,
)


def graph_task(stage: str = "deep_read") -> dict:
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
    return next(task for task in graph["tasks"] if task["key"] == stage)


def test_validate_task_input_parses_all_typed_handoff_fields() -> None:
    task = graph_task()

    result = validate_task_input(task, known_case_ids={"GOV-20990101-001"}, check_input_files=False)

    assert result["ok"] is True
    assert result["handoff"]["stage"] == "deep_read"
    assert result["errors"] == []


def test_validate_task_input_rejects_missing_typed_field() -> None:
    task = graph_task()
    handoff = dict(task["handoff"])
    del handoff["next_profile"]
    task["body"] = "TEOS_TYPED_HANDOFF_V1\n" + json.dumps(handoff, sort_keys=True)

    result = validate_task_input(task, known_case_ids={"GOV-20990101-001"}, check_input_files=False)

    assert result["ok"] is False
    assert any("next_profile" in error for error in result["errors"])


def test_validate_completion_requires_artifact_citations_run_log_and_stage_gate(tmp_path: Path) -> None:
    task = graph_task("deep_read")
    artifact = tmp_path / "deep_read.md"
    artifact.write_text("GOV-20990101-001 cited deep read\n", encoding="utf-8")
    run_log = tmp_path / "run.json"
    run_log.write_text(json.dumps({"run_id": "RUN-X", "case_id": "GOV-20990101-001"}), encoding="utf-8")
    task["expected_outputs"] = [str(artifact)]
    result = {
        "status": "PASS",
        "case_id": "GOV-20990101-001",
        "stage": "deep_read",
        "citations": ["fixture.pdf:1"],
        "artifacts": [str(artifact)],
        "run_log_evidence": [str(run_log)],
        "document_readable": True,
        "ambiguous_clauses": [],
    }

    valid = validate_completion(task, result, project_root=tmp_path)
    invalid = validate_completion(task, result | {"citations": []}, project_root=tmp_path)

    assert valid["ok"] is True
    assert invalid["ok"] is False
    assert any("citation" in error for error in invalid["errors"])


def test_validate_parent_results_requires_done_evidence_and_visible_artifacts(tmp_path: Path) -> None:
    artifact = tmp_path / "parent.json"
    artifact.write_text("{}", encoding="utf-8")
    parent_results = {
        "GOV-20990101-001:intake": {
            "status": "done",
            "result": {
                "status": "PASS",
                "citations": ["source.example"],
                "artifacts": [str(artifact)],
            },
        }
    }

    valid = validate_parent_results(
        ["GOV-20990101-001:intake"], parent_results, project_root=tmp_path
    )
    invalid = validate_parent_results(
        ["GOV-20990101-001:intake"],
        {"GOV-20990101-001:intake": {"status": "done", "result": {"status": "PASS", "citations": [], "artifacts": []}}},
        project_root=tmp_path,
    )

    assert valid["ok"] is True
    assert invalid["ok"] is False


def test_needs_input_blocks_never_auto_promote() -> None:
    approval = graph_task("approval")

    assert approval["block_kind"] == "needs_input"
    assert can_auto_promote(approval, parents_complete=True) is False
    for reason in (
        "owner_approval",
        "missing_documents",
        "unavailable_credentials",
        "ambiguous_compliance",
        "portal_human_challenge",
    ):
        blocked = approval | {"block_kind": "needs_input", "block_reason": reason}
        assert can_auto_promote(blocked, parents_complete=True) is False
