#!/usr/bin/env python3
"""Plan bounded Tender OS Kanban swarms with verifier-before-synthesis ordering."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Callable

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = PROJECT_ROOT / "config" / "kanban_swarms.yaml"
BOARD = "tender-export-os"
OUTPUT_SCHEMA = "config/schemas/swarm_worker_output.schema.json"
CommandRunner = Callable[[list[str]], Any]


def load_swarm_spec(path: Path = DEFAULT_SPEC) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Swarm specification must be a mapping")
    if data.get("board") != BOARD or data.get("external_effects_allowed") is not False:
        raise ValueError("Swarm specification must target Tender OS without external effects")
    if int(data.get("max_concurrency", 0)) != 2:
        raise ValueError("Initial swarm concurrency must remain capped at two")
    swarms = data.get("swarms") or []
    ids = [str(row.get("id", "")) for row in swarms]
    if len(ids) != len(set(ids)) or not all(ids):
        raise ValueError("Swarm IDs must be unique and non-empty")
    for swarm in swarms:
        if int(swarm.get("max_concurrency", 0)) > 2:
            raise ValueError(f"Swarm {swarm.get('id')} exceeds pilot concurrency cap")
        if swarm.get("external_effects_allowed") is not False:
            raise ValueError(f"Swarm {swarm.get('id')} permits external effects")
        workers = swarm.get("workers") or []
        if len(workers) < 2:
            raise ValueError(f"Swarm {swarm.get('id')} needs independent workers")
        worker_ids = [str(worker.get("id", "")) for worker in workers]
        if len(worker_ids) != len(set(worker_ids)) or not all(worker_ids):
            raise ValueError(f"Swarm {swarm.get('id')} worker IDs must be unique")
        for worker in workers:
            if not worker.get("profile") or not worker.get("evidence_keys") or not worker.get("allowed_toolsets"):
                raise ValueError(f"Swarm {swarm.get('id')} has an incomplete worker contract")
    return data


def _swarm(config: dict[str, Any], swarm_id: str) -> dict[str, Any]:
    for swarm in config.get("swarms", []):
        if str(swarm.get("id")) == swarm_id:
            return swarm
    raise ValueError(f"Unknown swarm template: {swarm_id}")


def _safe_case(case_id: str) -> str:
    value = str(case_id).strip()
    if not value or "/" in value or "\\" in value or ".." in value:
        raise ValueError("case_id must be a non-empty bounded identifier")
    return value


def _evidence_path(path_value: str) -> Path:
    path = Path(path_value).expanduser().resolve()
    root = PROJECT_ROOT.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Evidence path escapes workspace: {path}") from exc
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Evidence path is missing or empty: {path}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path) -> str:
    return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))


def build_swarm(
    case_id: str,
    swarm_id: str,
    evidence: dict[str, str],
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or load_swarm_spec()
    case_id = _safe_case(case_id)
    swarm = _swarm(config, swarm_id)
    if len(evidence) < int(swarm["minimum_evidence"]):
        raise ValueError(f"Swarm {swarm_id} requires minimum evidence of {swarm['minimum_evidence']} artifacts")

    resolved: dict[str, Path] = {key: _evidence_path(path) for key, path in evidence.items()}
    missing_keys = sorted({key for worker in swarm["workers"] for key in worker["evidence_keys"]} - set(resolved))
    if missing_keys:
        raise ValueError(f"Missing scoped evidence keys: {', '.join(missing_keys)}")

    output_schema = str(config.get("output_schema") or OUTPUT_SCHEMA)
    tasks: list[dict[str, Any]] = []
    worker_local_ids: list[str] = []
    output_paths: list[str] = []
    for worker in swarm["workers"]:
        worker_id = str(worker["id"])
        local_id = f"{case_id}:{swarm_id}:{worker_id}"
        worker_local_ids.append(local_id)
        worker_outputs = f"outputs/swarms/{case_id}/{swarm_id}/{worker_id}.json"
        output_paths.append(worker_outputs)
        input_artifacts = []
        for key in worker["evidence_keys"]:
            path = resolved[key]
            input_artifacts.append(
                {
                    "key": key,
                    "path": _relative(path),
                    "sha256": _sha256(path),
                }
            )
        tasks.append(
            {
                "local_id": local_id,
                "kind": "worker",
                "worker_id": worker_id,
                "title": f"{swarm['title']}: {worker['role']} [{case_id}]",
                "profile": str(worker["profile"]),
                "parents": [],
                "parallel_group": 1,
                "allowed_toolsets": list(worker["allowed_toolsets"]),
                "input_artifacts": input_artifacts,
                "output_path": worker_outputs,
                "output_schema": output_schema,
                "required_output_fields": ["status", "case_id", "swarm_id", "worker_id", "summary", "evidence", "findings", "unknowns", "stop_reason", "approval_required", "external_actions_executed"],
                "approval_required": False,
                "external_actions_allowed": False,
                "idempotency_key": f"teos:swarm:{case_id}:{swarm_id}:{worker_id}:v{config['version']}",
            }
        )

    verifier_id = f"{case_id}:{swarm_id}:verifier"
    verifier_output = f"outputs/swarms/{case_id}/{swarm_id}/verifier.json"
    tasks.append(
        {
            "local_id": verifier_id,
            "kind": "verifier",
            "worker_id": "verifier",
            "title": f"{swarm['title']}: verify independent outputs [{case_id}]",
            "profile": str(swarm["verifier_profile"]),
            "parents": worker_local_ids,
            "parallel_group": 2,
            "allowed_toolsets": ["file", "skills", "todo"],
            "input_artifacts": [{"path": path} for path in output_paths],
            "output_path": verifier_output,
            "output_schema": output_schema,
            "required_output_fields": ["status", "case_id", "swarm_id", "worker_id", "summary", "evidence", "findings", "unknowns", "stop_reason", "approval_required", "external_actions_executed"],
            "approval_required": False,
            "external_actions_allowed": False,
            "idempotency_key": f"teos:swarm:{case_id}:{swarm_id}:verifier:v{config['version']}",
        }
    )

    synthesis_id = f"{case_id}:{swarm_id}:synthesizer"
    tasks.append(
        {
            "local_id": synthesis_id,
            "kind": "synthesizer",
            "worker_id": "synthesizer",
            "title": f"{swarm['title']}: synthesize verified findings [{case_id}]",
            "profile": str(swarm["synthesizer_profile"]),
            "parents": [verifier_id],
            "parallel_group": 3,
            "allowed_toolsets": ["file", "skills", "todo"],
            "input_artifacts": [{"path": path} for path in output_paths] + [{"path": verifier_output}],
            "output_path": f"outputs/swarms/{case_id}/{swarm_id}/synthesis.json",
            "output_schema": output_schema,
            "required_output_fields": ["status", "case_id", "swarm_id", "worker_id", "summary", "evidence", "findings", "unknowns", "stop_reason", "approval_required", "external_actions_executed"],
            "preserve_disagreements": bool(swarm["preserve_disagreements"]),
            "approval_required": False,
            "external_actions_allowed": False,
            "idempotency_key": f"teos:swarm:{case_id}:{swarm_id}:synthesizer:v{config['version']}",
        }
    )
    return {
        "version": int(config["version"]),
        "board": BOARD,
        "case_id": case_id,
        "swarm_id": swarm_id,
        "title": swarm["title"],
        "max_concurrency": int(swarm["max_concurrency"]),
        "external_effects_allowed": False,
        "measurement_status": "PLANNING_ONLY",
        "tasks": tasks,
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }


def benchmark_plan(graph: dict[str, Any]) -> dict[str, Any]:
    workers = sum(1 for task in graph.get("tasks", []) if task.get("kind") == "worker")
    total_tasks = len(graph.get("tasks", []))
    concurrency = max(1, int(graph.get("max_concurrency", 1)))
    return {
        "measurement_status": "PLANNING_ONLY",
        "worker_count": workers,
        "max_concurrency": concurrency,
        "estimated_parallel_rounds": math.ceil(workers / concurrency),
        "single_profile_rounds": total_tasks,
        "verifier_before_synthesis": any(task.get("kind") == "verifier" for task in graph.get("tasks", [])),
        "external_actions_executed": False,
        "note": "No model, token, latency, correctness, or owner-correction metric is claimed until a controlled pilot run records it.",
    }


def _run(command: list[str]) -> Any:
    completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(completed.stderr or completed.stdout)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Kanban returned non-JSON output: {completed.stdout[:500]}") from exc


def execute_swarm(graph: dict[str, Any], command_runner: CommandRunner = _run) -> dict[str, str]:
    created: dict[str, str] = {}
    for task in graph["tasks"]:
        command = [
            "hermes", "kanban", "--board", BOARD, "create", task["title"],
            "--body", json.dumps(task, sort_keys=True),
            "--assignee", task["profile"],
            "--workspace", f"dir:{PROJECT_ROOT}",
            "--tenant", f"swarm:{graph['case_id']}:{graph['swarm_id']}",
            "--idempotency-key", task["idempotency_key"],
            "--max-runtime", "900", "--max-retries", "1", "--created-by", "create_teos_swarm", "--json",
        ]
        data = command_runner(command)
        task_id = str(data.get("id") or data.get("task_id") or (data.get("task") or {}).get("id") or "") if isinstance(data, dict) else ""
        if not task_id:
            raise RuntimeError(f"Could not determine task ID for {task['local_id']}")
        created[task["local_id"]] = task_id
    for task in graph["tasks"]:
        for parent in task.get("parents", []):
            command_runner(["hermes", "kanban", "--board", BOARD, "link", created[parent], created[task["local_id"]], "--json"])
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--swarm", required=True)
    parser.add_argument("--evidence", action="append", default=[], metavar="KEY=PATH")
    parser.add_argument("--output", default="")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    evidence: dict[str, str] = {}
    for item in args.evidence:
        key, separator, path = item.partition("=")
        if not separator or not key or not path:
            raise SystemExit("--evidence must use KEY=PATH")
        evidence[key] = path
    graph = build_swarm(args.case_id, args.swarm, evidence)
    result: dict[str, Any] = {"status": "PASS", "graph": graph, "external_actions_executed": False}
    if args.benchmark:
        result["benchmark"] = benchmark_plan(graph)
    if args.execute:
        result["hermes_task_ids"] = execute_swarm(graph)
    if args.output:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        result["output"] = str(output)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
