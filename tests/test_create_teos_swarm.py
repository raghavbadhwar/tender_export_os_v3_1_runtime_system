from __future__ import annotations

from pathlib import Path

import pytest

from scripts.create_teos_swarm import benchmark_plan, build_swarm, execute_swarm, load_swarm_spec


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def evidence_fixture(tmp_path: Path) -> dict[str, str]:
    paths = {}
    for key in ("requirements", "eligibility", "deadline", "corrigenda"):
        path = tmp_path / f"{key}.json"
        path.write_text(f'{{"evidence_type":"{key}","verified":true}}', encoding="utf-8")
        paths[key] = str(path)
    return paths


def test_swarm_spec_declares_five_bounded_templates() -> None:
    spec = load_swarm_spec()

    assert {row["id"] for row in spec["swarms"]} == {
        "gov_deep_read",
        "supplier_proof",
        "pricing_red_team",
        "export_buyer_intelligence",
        "compliance_draft",
    }
    assert all(row["max_concurrency"] == 2 for row in spec["swarms"])
    assert all(row["external_effects_allowed"] is False for row in spec["swarms"])


def test_build_swarm_enforces_evidence_threshold_and_scopes_worker_inputs(tmp_path: Path, monkeypatch) -> None:
    import scripts.create_teos_swarm as swarm_module

    monkeypatch.setattr(swarm_module, "PROJECT_ROOT", tmp_path)
    evidence = evidence_fixture(tmp_path)
    graph = build_swarm("GOV-FIXTURE-001", "gov_deep_read", evidence)

    workers = [task for task in graph["tasks"] if task["kind"] == "worker"]
    verifier = next(task for task in graph["tasks"] if task["kind"] == "verifier")
    synthesizer = next(task for task in graph["tasks"] if task["kind"] == "synthesizer")

    assert len(workers) == 3
    assert all(task["external_actions_allowed"] is False for task in graph["tasks"])
    assert workers[0]["input_artifacts"][0]["key"] == "requirements"
    assert workers[0]["input_artifacts"][0]["path"] == "requirements.json"
    assert len(workers[0]["input_artifacts"][0]["sha256"]) == 64
    assert [item["key"] for item in workers[1]["input_artifacts"]] == ["eligibility"]
    assert [item["key"] for item in workers[2]["input_artifacts"]] == ["deadline", "corrigenda"]
    assert verifier["parents"] == [task["local_id"] for task in workers]
    assert synthesizer["parents"] == [verifier["local_id"]]
    assert synthesizer["preserve_disagreements"] is True
    assert all(task["output_schema"] == "config/schemas/swarm_worker_output.schema.json" for task in graph["tasks"])


def test_build_swarm_rejects_missing_or_outside_workspace_evidence(tmp_path: Path, monkeypatch) -> None:
    import scripts.create_teos_swarm as swarm_module

    monkeypatch.setattr(swarm_module, "PROJECT_ROOT", tmp_path)
    evidence = evidence_fixture(tmp_path)
    evidence.pop("deadline")

    with pytest.raises(ValueError, match="minimum evidence"):
        build_swarm("GOV-FIXTURE-002", "gov_deep_read", evidence)

    outside = tmp_path.parent / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    evidence["deadline"] = str(outside)
    with pytest.raises(ValueError, match="workspace"):
        build_swarm("GOV-FIXTURE-003", "gov_deep_read", evidence)


def test_execute_swarm_uses_idempotent_internal_kanban_commands(tmp_path: Path, monkeypatch) -> None:
    import scripts.create_teos_swarm as swarm_module

    monkeypatch.setattr(swarm_module, "PROJECT_ROOT", tmp_path)
    graph = build_swarm("GOV-FIXTURE-004", "gov_deep_read", evidence_fixture(tmp_path))
    commands: list[list[str]] = []

    def runner(command: list[str]) -> dict:
        commands.append(command)
        if "create" in command:
            return {"id": f"TASK-{len(commands)}"}
        return {}

    created = execute_swarm(graph, runner)

    assert len(created) == 5
    create_commands = [command for command in commands if "create" in command]
    assert all("--idempotency-key" in command for command in create_commands)
    assert all("--tenant" in command for command in create_commands)
    assert all("--created-by" in command for command in create_commands)
    assert all("--external" not in command for command in create_commands)


def test_swarm_benchmark_is_explicitly_planning_only() -> None:
    result = benchmark_plan(
        {
            "max_concurrency": 2,
            "tasks": [
                {"kind": "worker"},
                {"kind": "worker"},
                {"kind": "worker"},
                {"kind": "verifier"},
                {"kind": "synthesizer"},
            ],
        }
    )

    assert result["measurement_status"] == "PLANNING_ONLY"
    assert result["estimated_parallel_rounds"] == 2
    assert result["single_profile_rounds"] == 5
    assert "tokens" not in result
    assert result["external_actions_executed"] is False
