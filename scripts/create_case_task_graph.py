#!/usr/bin/env python3
"""Build and optionally create a validated per-case Hermes Kanban DAG."""

from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event


DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "kanban_task_graphs"
DEFAULT_GRAPH_SPEC = PROJECT_ROOT / "config" / "case_task_graph.yaml"
CommandRunner = Callable[[list[str]], Any]

REQUIRED_STAGE_FIELDS = {
    "key",
    "title",
    "assignee",
    "parents",
    "required_inputs",
    "expected_outputs",
    "approval_boundary",
    "approval_required",
    "retry_limit",
    "max_runtime_seconds",
    "completion_validator",
    "required_output_schema",
    "stop_conditions",
    "next_profile",
    "idempotency_key_template",
}

GOV_REQUIRED_STAGE_PARENTS = {
    "intake": [],
    "fast_kill": ["intake"],
    "fast_kill_critic": ["fast_kill"],
    "deep_read": ["fast_kill_critic"],
    "supplier": ["deep_read"],
    "historical_intelligence": ["deep_read"],
    "pricing": ["supplier", "historical_intelligence"],
    "compliance": ["deep_read"],
    "artifacts": ["pricing", "compliance"],
    "approval": ["artifacts"],
    "execution": ["approval"],
    "evaluation_award": ["execution"],
    "delivery_payment": ["evaluation_award"],
    "learning": ["delivery_payment"],
}

EXPORT_REQUIRED_STAGE_PARENTS = {
    "research_thesis": [],
    "target_staging": ["research_thesis"],
    "buyer_verification": ["target_staging"],
    "contact_path_proof": ["buyer_verification"],
    "outreach_approval": ["contact_path_proof"],
    "first_contact": ["outreach_approval"],
    "reply_triage": ["first_contact"],
    "rfq_verification": ["reply_triage"],
    "supplier": ["rfq_verification"],
    "compliance": ["rfq_verification"],
    "pricing": ["supplier", "compliance"],
    "quote_pack": ["pricing"],
    "quote_approval": ["quote_pack"],
    "quote_delivery": ["quote_approval"],
    "negotiation_drafts": ["quote_delivery"],
    "order_capture": ["negotiation_drafts"],
    "shipment_invoice_payment": ["order_capture"],
    "repeat_buyer_learning": ["shipment_invoice_payment"],
}


def load_graph_spec(path: Path = DEFAULT_GRAPH_SPEC) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Case task graph must be a YAML mapping: {path}")
    spec = copy.deepcopy(data)
    template = str(spec.get("idempotency_key_template") or "")
    for workflow in (spec.get("workflows") or {}).values():
        for stage in workflow.get("stages") or []:
            stage.setdefault("idempotency_key_template", template)
            stage.setdefault("external_effect", False)
            stage.setdefault("initial_status", "")
            stage.setdefault("block_kind", "")
            stage.setdefault("block_reason", "")
    validate_graph_spec(spec)
    return spec


def _assert_acyclic(stages: list[dict[str, Any]], workflow: str) -> None:
    parents = {stage["key"]: list(stage.get("parents") or []) for stage in stages}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(key: str) -> None:
        if key in visiting:
            raise ValueError(f"{workflow} graph contains a cycle at {key}")
        if key in visited:
            return
        visiting.add(key)
        for parent in parents[key]:
            visit(parent)
        visiting.remove(key)
        visited.add(key)

    for key in parents:
        visit(key)


def _validate_gov_operating_flow(stages: list[dict[str, Any]]) -> None:
    """Preserve the governed GOV progression rather than only checking a DAG."""
    by_key = {str(stage["key"]): stage for stage in stages}
    missing = sorted(set(GOV_REQUIRED_STAGE_PARENTS) - set(by_key))
    if missing:
        raise ValueError(f"GOV graph missing required stages: {', '.join(missing)}")
    for key, parents in GOV_REQUIRED_STAGE_PARENTS.items():
        if list(by_key[key].get("parents") or []) != parents:
            raise ValueError(f"GOV.{key} must depend on {parents}")
    if by_key["execution"].get("external_effect"):
        raise ValueError("GOV.execution tracks owner-operated submission and may not expose an external effect")
    if by_key["approval"].get("initial_status") != "blocked":
        raise ValueError("GOV.approval must wait as a typed owner block")


def _validate_export_operating_flow(stages: list[dict[str, Any]]) -> None:
    """Keep discovery, contact, RFQ, quote, and cash tracking as distinct governed stages."""
    by_key = {str(stage["key"]): stage for stage in stages}
    missing = sorted(set(EXPORT_REQUIRED_STAGE_PARENTS) - set(by_key))
    if missing:
        raise ValueError(f"EXPORT graph missing required stages: {', '.join(missing)}")
    for key, parents in EXPORT_REQUIRED_STAGE_PARENTS.items():
        if list(by_key[key].get("parents") or []) != parents:
            raise ValueError(f"EXPORT.{key} must depend on {parents}")
    for key in ("outreach_approval", "quote_approval"):
        if by_key[key].get("initial_status") != "blocked":
            raise ValueError(f"EXPORT.{key} must wait as a typed owner block")
    for key in ("first_contact", "quote_delivery"):
        if by_key[key].get("external_effect"):
            raise ValueError(f"EXPORT.{key} may create an owner-operated connector handoff but not execute externally")


def validate_graph_spec(spec: dict[str, Any], known_profiles: set[str] | None = None) -> None:
    workflows = spec.get("workflows")
    if not isinstance(workflows, dict) or set(workflows) != {"GOV", "EXPORT"}:
        raise ValueError("case task graph must define GOV and EXPORT workflows")
    for workflow_name, workflow in workflows.items():
        stages = workflow.get("stages") if isinstance(workflow, dict) else None
        if not isinstance(stages, list) or not stages:
            raise ValueError(f"{workflow_name} has no stages")
        keys = [str(stage.get("key") or "") for stage in stages]
        if len(set(keys)) != len(keys) or any(not key for key in keys):
            raise ValueError(f"{workflow_name} stage keys must be unique and non-empty")
        key_set = set(keys)
        for stage in stages:
            missing = sorted(REQUIRED_STAGE_FIELDS - set(stage))
            if missing:
                raise ValueError(f"{workflow_name}.{stage.get('key')} missing fields: {', '.join(missing)}")
            unknown_parents = sorted(set(stage.get("parents") or []) - key_set)
            if unknown_parents:
                raise ValueError(
                    f"{workflow_name}.{stage['key']} has unknown parent(s): {', '.join(unknown_parents)}"
                )
            if known_profiles is not None and stage["assignee"] not in known_profiles:
                raise ValueError(f"{workflow_name}.{stage['key']} has unknown assignee {stage['assignee']}")
            if not str(stage.get("idempotency_key_template") or ""):
                raise ValueError(f"{workflow_name}.{stage['key']} has no idempotency template")
            if stage.get("initial_status") == "blocked" and stage.get("block_kind") != "needs_input":
                raise ValueError(f"{workflow_name}.{stage['key']} blocked task must use needs_input")
            if stage.get("external_effect") and int(stage.get("retry_limit") or 0) != 0:
                raise ValueError(f"{workflow_name}.{stage['key']} external-effect tracking may not auto-retry")
        if workflow_name == "GOV":
            _validate_gov_operating_flow(stages)
        if workflow_name == "EXPORT":
            _validate_export_operating_flow(stages)
        _assert_acyclic(stages, workflow_name)


GRAPH_SPEC = load_graph_spec()
BOARD = str(GRAPH_SPEC["board"])
TASKS: dict[str, list[dict[str, Any]]] = {
    name: workflow["stages"] for name, workflow in GRAPH_SPEC["workflows"].items()
}


def load_cases() -> list[dict[str, str]]:
    with (DATA_DIR / "master_cases.csv").open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def find_case(case_id: str) -> dict[str, str]:
    for case in load_cases():
        if case.get("case_id") == case_id:
            return case
    raise SystemExit(f"Unknown case_id: {case_id}")


def _format_paths(values: list[str], *, case_id: str, stage: str) -> list[str]:
    return [str(value).format(case_id=case_id, stage=stage) for value in values]


def _parse_source_event_ids(case: dict[str, Any]) -> list[str]:
    raw = case.get("source_event_ids") or []
    if isinstance(raw, list):
        return [str(value) for value in raw if value]
    text = str(raw).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(value) for value in parsed if value]
    except json.JSONDecodeError:
        pass
    return [value.strip() for value in text.split(",") if value.strip()]


def build_handoff(case: dict[str, Any], stage: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case.get("case_id") or "")
    stage_key = str(stage["key"])
    return {
        "case_id": case_id,
        "workflow_type": str(case.get("workflow_type") or "").upper(),
        "stage": stage_key,
        "source_event_ids": _parse_source_event_ids(case),
        "input_artifacts": _format_paths(
            list(stage.get("required_inputs") or []), case_id=case_id, stage=stage_key
        ),
        "required_output_schema": str(stage["required_output_schema"]),
        "approval_required": bool(stage.get("approval_required")),
        "deadline": str(case.get("deadline_date") or ""),
        "stop_conditions": list(stage.get("stop_conditions") or []),
        "next_profile": str(stage.get("next_profile") or ""),
    }


def task_body(case: dict[str, Any], stage: dict[str, Any], handoff: dict[str, Any]) -> str:
    expected_outputs = _format_paths(
        list(stage.get("expected_outputs") or []),
        case_id=handoff["case_id"],
        stage=handoff["stage"],
    )
    return "\n".join(
        [
            "TEOS_TYPED_HANDOFF_V1",
            json.dumps(handoff, sort_keys=True),
            "",
            f"opportunity: {case.get('opportunity_title', '')}",
            f"buyer: {case.get('buyer_name', '')}",
            f"case_status: {case.get('status', '')}",
            f"task: {stage['title']}",
            f"expected_outputs: {json.dumps(expected_outputs)}",
            f"completion_validator: {stage['completion_validator']}",
            f"approval_boundary: {stage['approval_boundary']}",
            f"block_kind: {stage.get('block_kind') or 'none'}",
            f"block_reason: {stage.get('block_reason') or 'none'}",
            f"external_effect: {str(bool(stage.get('external_effect'))).lower()}",
            "",
            "Rules:",
            "- Use case_id in every output and completion record.",
            "- Cite every source and local evidence path used.",
            "- Complete only after the named validator passes, expected artifacts exist, and run-log evidence is present.",
            "- Block with kind needs_input for owner approval, missing documents, unavailable credentials, ambiguous compliance, or a portal human challenge.",
            "- Do not contact anyone, submit, upload, pay, use DSC, confirm classification/origin, or commit price/delivery/payment terms.",
        ]
    )


def build_graph(case: dict[str, Any], graph_spec: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = graph_spec or GRAPH_SPEC
    validate_graph_spec(spec)
    workflow = str(case.get("workflow_type") or "").upper()
    workflow_spec = (spec.get("workflows") or {}).get(workflow)
    if not workflow_spec:
        raise ValueError(f"Unsupported workflow_type for {case.get('case_id')}: {workflow}")
    case_id = str(case.get("case_id") or "")
    if not case_id:
        raise ValueError("case_id is required")
    tasks: list[dict[str, Any]] = []
    for order, stage in enumerate(workflow_spec["stages"], start=1):
        key = str(stage["key"])
        handoff = build_handoff(case, stage)
        task_id = f"{case_id}:{key}"
        idempotency_key = str(stage["idempotency_key_template"]).format(
            case_id=case_id, stage=key, workflow_type=workflow
        )
        tasks.append(
            {
                "local_id": task_id,
                "key": key,
                "title": f"{case_id} — {stage['title']}",
                "body": task_body(case, stage, handoff),
                "handoff": handoff,
                "assignee": stage["assignee"],
                "parents": [f"{case_id}:{parent}" for parent in stage.get("parents") or []],
                "initial_status": stage.get("initial_status") or "",
                "block_kind": stage.get("block_kind") or "",
                "block_reason": stage.get("block_reason") or "",
                "idempotency_key": idempotency_key,
                "max_runtime_seconds": int(stage["max_runtime_seconds"]),
                "max_retries": int(stage["retry_limit"]),
                "completion_validator": stage["completion_validator"],
                "expected_outputs": _format_paths(
                    list(stage.get("expected_outputs") or []), case_id=case_id, stage=key
                ),
                "external_effect": bool(stage.get("external_effect")),
                "order": order,
            }
        )
    canonical = json.dumps(tasks, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": 1,
        "case_id": case_id,
        "workflow_type": workflow,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "board": str(spec["board"]),
        "workspace": f"dir:{spec['workspace']}",
        "mode": "plan_or_execute",
        "graph_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "tasks": tasks,
        "external_actions_executed": False,
    }


def run_hermes(args: list[str]) -> Any:
    completed = subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(args)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"stdout": completed.stdout.strip()}


def get_live_profiles(command_runner: CommandRunner = run_hermes) -> set[str]:
    data = command_runner(["hermes", "kanban", "--board", BOARD, "assignees", "--json"])
    if not isinstance(data, list):
        raise RuntimeError("Hermes assignees command returned an unexpected shape")
    return {
        str(row.get("name"))
        for row in data
        if isinstance(row, dict) and row.get("on_disk") is True and row.get("name")
    }


def execute_graph(
    graph: dict[str, Any],
    *,
    live_profiles: set[str] | None = None,
    command_runner: CommandRunner = run_hermes,
) -> dict[str, str]:
    profiles = live_profiles if live_profiles is not None else get_live_profiles(command_runner)
    unknown = sorted({task["assignee"] for task in graph["tasks"]} - profiles)
    if unknown:
        raise ValueError(f"unknown live assignee(s): {', '.join(unknown)}")
    local_ids = {task["local_id"] for task in graph["tasks"]}
    unknown_parents = sorted(
        {parent for task in graph["tasks"] for parent in task.get("parents") or []} - local_ids
    )
    if unknown_parents:
        raise ValueError(f"unknown graph parent(s): {', '.join(unknown_parents)}")

    created: dict[str, str] = {}
    for task in graph["tasks"]:
        command = [
            "hermes",
            "kanban",
            "--board",
            graph["board"],
            "create",
            task["title"],
            "--body",
            task["body"],
            "--assignee",
            task["assignee"],
            "--workspace",
            graph["workspace"],
            "--tenant",
            graph["case_id"],
            "--idempotency-key",
            task["idempotency_key"],
            "--max-runtime",
            str(task["max_runtime_seconds"]),
            "--max-retries",
            str(max(1, int(task["max_retries"]) + 1)),
            "--created-by",
            "create_case_task_graph",
            "--json",
        ]
        if task.get("initial_status"):
            command.extend(["--initial-status", task["initial_status"]])
        data = command_runner(command)
        task_id = ""
        if isinstance(data, dict):
            task_id = str(
                data.get("id")
                or data.get("task_id")
                or (data.get("task") or {}).get("id")
                or ""
            )
        if not task_id:
            raise RuntimeError(f"Could not determine task id from {data}")
        created[task["local_id"]] = task_id

    for task in graph["tasks"]:
        child = created[task["local_id"]]
        for parent_local in task.get("parents") or []:
            command_runner(
                [
                    "hermes",
                    "kanban",
                    "--board",
                    graph["board"],
                    "link",
                    created[parent_local],
                    child,
                    "--json",
                ]
            )
    return created


def write_graph(graph: dict[str, Any], output_dir: Path = OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{graph['case_id']}_task_graph.json"
    path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--graph-spec", default=str(DEFAULT_GRAPH_SPEC))
    parser.add_argument("--execute", action="store_true", help="Create and link idempotent Hermes Kanban tasks")
    parser.add_argument("--record-event", action="store_true")
    args = parser.parse_args()

    spec = load_graph_spec(Path(args.graph_spec))
    case = find_case(args.case_id)
    graph = build_graph(case, spec)
    created: dict[str, str] = {}
    if args.execute:
        created = execute_graph(graph)
        graph["executed_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        graph["hermes_task_ids"] = created
    path = write_graph(graph)
    print(f"Wrote {rel(path)}")
    if created:
        print(f"Created/linked {len(created)} idempotent Hermes Kanban tasks")
    if args.record_event:
        append_event(
            "kanban.task_graph_created",
            "create_case_task_graph",
            case_id=args.case_id,
            object_type="kanban_task_graph",
            object_id=rel(path),
            payload={
                "graph_path": rel(path),
                "executed": bool(args.execute),
                "task_count": len(graph["tasks"]),
                "hermes_task_ids": created,
                "graph_sha256": graph["graph_sha256"],
            },
            citations=[rel(path), rel(Path(args.graph_spec)), "data/master_cases.csv"],
            idempotency_key=f"teos:{args.case_id}:task-graph:v1",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
