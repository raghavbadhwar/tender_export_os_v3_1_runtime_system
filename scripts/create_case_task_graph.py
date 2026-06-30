#!/usr/bin/env python3
"""Create a per-case Hermes Kanban task graph for Tender Export OS v4.1."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any

from event_ledger import append_event

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "kanban_task_graphs"
BOARD = "tender-export-os"

TASKS: dict[str, list[dict[str, Any]]] = {
    "GOV": [
        {"key": "intake", "title": "Intake source evidence", "assignee": "gov-tender-radar"},
        {"key": "fast_kill", "title": "Fast-kill eligibility and deadline check", "assignee": "gov-tender-radar", "parents": ["intake"]},
        {"key": "deep_read", "title": "Deep-read tender, BOQ, eligibility, EMD, clauses", "assignee": "gov-tender-radar", "parents": ["fast_kill"]},
        {"key": "supplier", "title": "Supplier 5-3-2 proof", "assignee": "supplier-sourcing", "parents": ["deep_read"]},
        {"key": "pricing", "title": "GOV pricing waterfall draft", "assignee": "pricing-compliance", "parents": ["supplier"]},
        {"key": "compliance", "title": "Compliance matrix and document checklist", "assignee": "pricing-compliance", "parents": ["deep_read"]},
        {"key": "artifacts", "title": "Bid pack and case dossier draft", "assignee": "codex-artifact-factory", "parents": ["pricing", "compliance"]},
        {"key": "approval", "title": "Owner approval card", "assignee": "hermes-chief-operator", "parents": ["artifacts"], "initial_status": "blocked"},
        {"key": "execution", "title": "Post-approval submission tracking", "assignee": "sales-followup", "parents": ["approval"]},
        {"key": "learning", "title": "Win/loss and source/supplier learning", "assignee": "learning-review", "parents": ["execution"]},
    ],
    "EXPORT": [
        {"key": "intake", "title": "Intake RFQ evidence", "assignee": "export-rfq-radar"},
        {"key": "buyer", "title": "Buyer verification draft", "assignee": "export-rfq-radar", "parents": ["intake"]},
        {"key": "deep_read", "title": "Extract product spec, quantity, destination, incoterms, payment", "assignee": "export-rfq-radar", "parents": ["buyer"]},
        {"key": "supplier", "title": "Supplier 5-3-2 proof", "assignee": "supplier-sourcing", "parents": ["deep_read"]},
        {"key": "compliance", "title": "Export compliance risk draft", "assignee": "pricing-compliance", "parents": ["deep_read"]},
        {"key": "pricing", "title": "EXW/FOB/CIF pricing waterfall draft", "assignee": "pricing-compliance", "parents": ["supplier", "compliance"]},
        {"key": "artifacts", "title": "Export quote pack and case dossier draft", "assignee": "codex-artifact-factory", "parents": ["pricing"]},
        {"key": "approval", "title": "Owner approval card", "assignee": "hermes-chief-operator", "parents": ["artifacts"], "initial_status": "blocked"},
        {"key": "followup", "title": "Post-approval buyer reply tracking", "assignee": "sales-followup", "parents": ["approval"]},
        {"key": "learning", "title": "Win/loss and buyer/supplier learning", "assignee": "learning-review", "parents": ["followup"]},
    ],
}


def load_cases() -> list[dict[str, str]]:
    with (DATA_DIR / "master_cases.csv").open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def find_case(case_id: str) -> dict[str, str]:
    for case in load_cases():
        if case.get("case_id") == case_id:
            return case
    raise SystemExit(f"Unknown case_id: {case_id}")


def task_body(case: dict[str, str], task: dict[str, Any]) -> str:
    case_id = case.get("case_id", "")
    return "\n".join([
        f"case_id: {case_id}",
        f"workflow_type: {case.get('workflow_type', '')}",
        f"status: {case.get('status', '')}",
        f"opportunity: {case.get('opportunity_title', '')}",
        f"buyer: {case.get('buyer_name', '')}",
        f"deadline: {case.get('deadline_date', '')}",
        "",
        f"Task: {task['title']}",
        "",
        "Rules:",
        "- Use case_id in every output and comment.",
        "- Cite sources used.",
        "- Internal drafts/artifacts are always allowed; supplier RFQ/follow-up and portal login/signup are standing-authorized with receipts.",
        "- Stop at remaining approval gates; do not contact buyers, submit, upload, pay, use DSC, confirm HSN/ITC-HS, claim origin, place POs, or commit final price/delivery/payment terms.",
        "- Record durable state changes through the event ledger or documented projection scripts.",
    ])


def build_graph(case: dict[str, str]) -> dict[str, Any]:
    workflow = case.get("workflow_type", "").upper()
    template = TASKS.get(workflow)
    if not template:
        raise SystemExit(f"Unsupported workflow_type for {case.get('case_id')}: {workflow}")
    case_id = case.get("case_id", "")
    tasks = []
    for order, task in enumerate(template, start=1):
        task_id = f"{case_id}:{task['key']}"
        tasks.append({
            "local_id": task_id,
            "key": task["key"],
            "title": f"{case_id} — {task['title']}",
            "body": task_body(case, task),
            "assignee": task["assignee"],
            "parents": [f"{case_id}:{parent}" for parent in task.get("parents", [])],
            "initial_status": task.get("initial_status", ""),
            "idempotency_key": f"tender-os:{case_id}:{task['key']}",
            "order": order,
        })
    return {
        "case_id": case_id,
        "workflow_type": workflow,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "board": BOARD,
        "mode": "plan_or_execute",
        "tasks": tasks,
    }


def run_hermes(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=PROJECT_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"stdout": completed.stdout.strip()}


def execute_graph(graph: dict[str, Any]) -> dict[str, str]:
    created: dict[str, str] = {}
    for task in graph["tasks"]:
        cmd = [
            "hermes", "kanban", "--board", BOARD, "create", task["title"],
            "--body", task["body"],
            "--assignee", task["assignee"],
            "--workspace", f"dir:{PROJECT_ROOT}",
            "--tenant", graph["case_id"],
            "--idempotency-key", task["idempotency_key"],
            "--created-by", "create_case_task_graph",
            "--json",
        ]
        if task.get("initial_status"):
            cmd.extend(["--initial-status", task["initial_status"]])
        data = run_hermes(cmd)
        hermes_id = data.get("id") or data.get("task_id") or data.get("task", {}).get("id") or data.get("stdout", "").split()[0]
        if not hermes_id:
            raise RuntimeError(f"Could not determine task id from {data}")
        created[task["local_id"]] = hermes_id
    for task in graph["tasks"]:
        child = created[task["local_id"]]
        for parent_local in task.get("parents", []):
            parent = created[parent_local]
            run_hermes(["hermes", "kanban", "--board", BOARD, "link", parent, child])
    return created


def write_graph(graph: dict[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{graph['case_id']}_task_graph.json"
    path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a GOV/EXPORT Kanban task graph for one case")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--execute", action="store_true", help="Actually create/link Hermes Kanban tasks")
    parser.add_argument("--record-event", action="store_true")
    args = parser.parse_args()
    case = find_case(args.case_id)
    graph = build_graph(case)
    created: dict[str, str] = {}
    if args.execute:
        created = execute_graph(graph)
        graph["executed_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        graph["hermes_task_ids"] = created
    path = write_graph(graph)
    print(f"Wrote {rel(path)}")
    if created:
        print(f"Created/linked {len(created)} Hermes Kanban tasks")
    if args.record_event:
        append_event(
            "kanban.task_graph_created",
            "create_case_task_graph",
            case_id=args.case_id,
            object_type="kanban_task_graph",
            object_id=rel(path),
            payload={"graph_path": rel(path), "executed": bool(args.execute), "task_count": len(graph["tasks"]), "hermes_task_ids": created},
            citations=[rel(path), "config/kanban_board.yaml", "data/master_cases.csv"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
