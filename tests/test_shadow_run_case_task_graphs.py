from __future__ import annotations

import csv
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from scripts.create_case_task_graph import build_graph
from scripts.shadow_run_case_task_graphs import (
    evaluate_shadow_graph,
    run_shadow_suite,
    select_shadow_cases,
)


NOW = dt.datetime(2026, 7, 12, 12, 0, tzinfo=dt.timezone.utc)
PROFILES = {
    "tender-export-os",
    "gov-tender-intelligence",
    "export-buyer-intelligence",
    "supplier-commercial",
    "pricing-risk",
    "compliance-due-diligence",
    "relationship-ops",
    "learning-evaluation",
}


def case(case_id: str, workflow: str, status: str = "WATCHLIST") -> dict[str, str]:
    return {
        "case_id": case_id,
        "workflow_type": workflow,
        "status": status,
        "opportunity_title": f"Opportunity {case_id}",
        "buyer_name": "Buyer",
        "deadline_date": "2026-08-01" if workflow == "GOV" else "",
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_shadow_case_selection_is_deterministic_and_ignores_terminal_cases() -> None:
    cases = [
        case("GOV-004", "GOV"),
        case("GOV-002", "GOV", "REJECTED"),
        case("GOV-003", "GOV"),
        case("GOV-001", "GOV"),
        case("GOV-005", "GOV"),
        case("EXP-003", "EXPORT"),
        case("EXP-001", "EXPORT"),
        case("EXP-004", "EXPORT", "ARCHIVED"),
        case("EXP-002", "EXPORT"),
    ]

    selected = select_shadow_cases(cases, per_workflow=3)

    assert [row["case_id"] for row in selected] == [
        "GOV-001",
        "GOV-003",
        "GOV-004",
        "EXP-001",
        "EXP-002",
        "EXP-003",
    ]


def test_shadow_graph_uses_ready_or_typed_truthful_blockers(tmp_path: Path) -> None:
    selected_case = case("GOV-001", "GOV")
    graph = build_graph(selected_case)
    write_csv(tmp_path / "data/master_cases.csv", ["case_id"], [{"case_id": "GOV-001"}])
    write_csv(tmp_path / "data/quote_master.csv", ["case_id"], [])
    write_csv(tmp_path / "data/supplier_master.csv", ["supplier_id"], [])
    (tmp_path / "data/events.jsonl").write_text("", encoding="utf-8")
    write_csv(tmp_path / "data/agent_run_log.csv", ["run_id"], [])

    receipt = evaluate_shadow_graph(
        selected_case,
        graph,
        live_profiles=PROFILES,
        quote_rows=[],
        project_root=tmp_path,
        as_of=NOW,
    )
    by_stage = {row["stage"]: row for row in receipt["stages"]}

    assert receipt["status"] == "PASS"
    assert by_stage["intake"]["state"] == "READY"
    assert by_stage["fast_kill"]["state"] == "BLOCKED"
    assert by_stage["fast_kill"]["block_kind"] == "needs_input"
    assert by_stage["fast_kill"]["block_reason"] == "missing_documents"
    assert by_stage["approval"]["state"] == "BLOCKED"
    assert by_stage["approval"]["block_kind"] == "needs_input"
    assert by_stage["approval"]["block_reason"] == "owner_approval"
    assert by_stage["execution"]["state"] == "BLOCKED"
    assert receipt["all_stages_ready_or_typed_blocked"] is True
    assert receipt["kanban_mutated"] is False
    assert receipt["agents_executed"] is False
    assert receipt["external_actions_executed"] is False


def test_shadow_suite_writes_six_idempotent_graph_receipts(tmp_path: Path) -> None:
    cases = [case(f"GOV-{number:03d}", "GOV") for number in range(1, 5)] + [
        case(f"EXP-{number:03d}", "EXPORT") for number in range(1, 5)
    ]
    output_root = tmp_path / "outputs/kanban_task_graphs/shadow"

    first = run_shadow_suite(
        cases,
        live_profiles=PROFILES,
        project_root=tmp_path,
        output_root=output_root,
        as_of=NOW,
    )
    second = run_shadow_suite(
        list(reversed(cases)),
        live_profiles=PROFILES,
        project_root=tmp_path,
        output_root=output_root,
        as_of=NOW + dt.timedelta(hours=1),
    )

    assert first["status"] == "PASS"
    assert first["selected_case_count"] == 6
    assert first["workflow_counts"] == {"EXPORT": 3, "GOV": 3}
    assert first["suite_idempotency_key"] == second["suite_idempotency_key"]
    assert first["kanban_mutated"] is False
    assert first["agents_executed"] is False
    assert first["external_actions_executed"] is False
    for case_id in first["selected_case_ids"]:
        graph = json.loads((output_root / case_id / "graph.json").read_text(encoding="utf-8"))
        receipt = json.loads((output_root / case_id / "shadow_receipt.json").read_text(encoding="utf-8"))
        assert graph["case_id"] == case_id
        assert receipt["case_id"] == case_id
        assert receipt["all_stages_ready_or_typed_blocked"] is True


def test_shadow_runner_is_directly_executable() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "shadow_run_case_task_graphs.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Shadow-evaluate six complete" in completed.stdout
