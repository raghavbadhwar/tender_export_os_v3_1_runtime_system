#!/usr/bin/env python3
"""Plan-first reconciliation of event-derived case graphs and live Hermes Kanban."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.create_case_task_graph import build_graph, execute_graph
from scripts.event_ledger import append_event
from scripts.validate_kanban_handoff import parse_handoff


BOARD = "tender-export-os"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "system_health" / "hermes_kanban_reconciliation_plan.json"
ACTIVE_STATUSES = {
    "NEW",
    "WATCHLIST",
    "DEEP_READ",
    "SUPPLIER_SEARCH",
    "PRICING_READY",
    "ARTIFACT_PRODUCTION",
    "APPROVAL_REQUIRED",
    "APPROVED",
    "SENT_OR_SUBMITTED",
    "FOLLOW_UP",
}

STATUS_TO_BOARD = {
    "NEW": "triage",
    "FAST_KILL": "triage",
    "WATCHLIST": "todo",
    "DEEP_READ": "running",
    "SUPPLIER_SEARCH": "running",
    "PRICING_READY": "ready",
    "ARTIFACT_PRODUCTION": "running",
    "APPROVAL_REQUIRED": "blocked",
    "CHANGES_REQUESTED": "blocked",
    "APPROVED": "ready",
    "SENT_OR_SUBMITTED": "running",
    "FOLLOW_UP": "todo",
    "WON": "done",
    "LOST": "done",
    "REJECTED": "archived",
    "ARCHIVED": "archived",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.is_file():
        return events
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
            if isinstance(event, dict):
                events.append(event)
    return events


def desired_task(case: dict[str, str]) -> dict[str, Any]:
    status = case.get("status", "")
    return {
        "case_id": case.get("case_id", ""),
        "title": case.get("opportunity_title", ""),
        "workflow_type": case.get("workflow_type", ""),
        "board_status": STATUS_TO_BOARD.get(status, "triage"),
        "case_status": status,
        "deadline": case.get("deadline_date", ""),
        "owner_approval_needed": case.get("approval_status") == "PENDING" or status == "APPROVAL_REQUIRED",
        "next_action": next_action(case),
    }


def next_action(case: dict[str, str]) -> str:
    status = case.get("status", "")
    if status == "SUPPLIER_SEARCH":
        return "Complete supplier proof; do not price until two strict quote proofs exist."
    if status == "APPROVAL_REQUIRED":
        return "Owner must approve, reject, or ask changes from the approval card."
    if status == "PRICING_READY":
        return "Create artifacts and approval card before external action."
    if status == "FOLLOW_UP":
        return "Track buyer/supplier response and validity windows."
    if status in {"REJECTED", "WON", "LOST", "ARCHIVED"}:
        return "Archive or keep for learning review."
    return "Route to the next valid workflow stage."


def load_snapshot(path: Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = data if isinstance(data, list) else data.get("tasks", [])
    return {task.get("case_id"): task for task in tasks if task.get("case_id")}


def build_plan(cases: list[dict[str, str]], current_tasks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Backward-compatible one-card-per-case planner used by older callers."""
    desired = {case.get("case_id"): desired_task(case) for case in cases if case.get("case_id")}
    actions: list[dict[str, Any]] = []
    for case_id, task in desired.items():
        current = current_tasks.get(case_id)
        if not current:
            actions.append({"action": "create_task", "case_id": case_id, "desired": task})
            continue
        diff = {
            key: {"current": current.get(key), "desired": value}
            for key, value in task.items()
            if current.get(key) != value
        }
        if diff:
            actions.append({"action": "update_task", "case_id": case_id, "diff": diff, "desired": task})
    for case_id in sorted(set(current_tasks) - set(desired)):
        actions.append({"action": "archive_orphan_task", "case_id": case_id, "current": current_tasks[case_id]})
    return {"generated_at": now_iso(), "mode": "plan_only", "actions": actions}


def fetch_live_tasks(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[dict[str, Any]]:
    command = ["hermes", "kanban", "--board", BOARD, "list", "--json"]
    completed = runner(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Hermes Kanban list failed")
    data = json.loads(completed.stdout)
    if not isinstance(data, list):
        raise RuntimeError("Hermes Kanban list returned an unexpected JSON shape")
    return [task for task in data if isinstance(task, dict)]


def build_event_case_projection(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    projection: dict[str, dict[str, Any]] = {}
    for event in events:
        case_id = str(event.get("case_id") or "")
        if not case_id:
            continue
        event_type = str(event.get("event_type") or "")
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if event_type in {"case.snapshot_imported", "case.created"}:
            row = payload.get("row") if isinstance(payload.get("row"), dict) else payload.get("case")
            if isinstance(row, dict):
                projection[case_id] = dict(row)
        if event_type == "case.updated":
            updates = payload.get("updates") if isinstance(payload.get("updates"), dict) else {}
            projection.setdefault(case_id, {"case_id": case_id}).update(updates)
            if payload.get("status"):
                projection[case_id]["status"] = payload["status"]
    return projection


def _managed_live_tasks(live_tasks: list[dict[str, Any]]) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], list[dict[str, Any]]]:
    managed: dict[tuple[str, str], list[dict[str, Any]]] = {}
    unmanaged: list[dict[str, Any]] = []
    for task in live_tasks:
        handoff = parse_handoff(str(task.get("body") or ""))
        if not handoff:
            unmanaged.append(task)
            continue
        key = (str(handoff.get("case_id") or ""), str(handoff.get("stage") or ""))
        managed.setdefault(key, []).append(task)
    return managed, unmanaged


def _task_diff(current: dict[str, Any], desired: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected = {
        "title": desired["title"],
        "assignee": desired["assignee"],
        "body": desired["body"],
        "workspace_path": str(PROJECT_ROOT),
    }
    return {
        key: {"current": current.get(key), "desired": value}
        for key, value in expected.items()
        if current.get(key) != value
    }


def build_live_reconciliation_plan(
    cases: list[dict[str, Any]],
    event_projection: dict[str, dict[str, Any]],
    live_tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    desired: dict[tuple[str, str], dict[str, Any]] = {}
    case_by_id = {str(case.get("case_id") or ""): case for case in cases if case.get("case_id")}
    for case in cases:
        if not case.get("case_id") or str(case.get("workflow_type") or "").upper() not in {"GOV", "EXPORT"}:
            continue
        graph = build_graph(case)
        for task in graph["tasks"]:
            desired[(graph["case_id"], task["key"])] = task

    managed, unmanaged = _managed_live_tasks(live_tasks)
    actions: list[dict[str, Any]] = []
    for case_id in sorted(case_by_id):
        event_case = event_projection.get(case_id)
        if event_case is None:
            actions.append({"action": "projection_missing_case", "case_id": case_id})
            continue
        for field in ("workflow_type", "status"):
            master_value = str(case_by_id[case_id].get(field) or "")
            event_value = str(event_case.get(field) or "")
            if event_value and master_value != event_value:
                actions.append(
                    {
                        "action": "projection_drift",
                        "case_id": case_id,
                        "field": field,
                        "master": master_value,
                        "event_projection": event_value,
                    }
                )

    for key in sorted(desired):
        desired_task_spec = desired[key]
        current_group = sorted(
            managed.get(key, []), key=lambda task: (int(task.get("created_at") or 0), str(task.get("id") or ""))
        )
        if not current_group:
            actions.append(
                {
                    "action": "create_task",
                    "case_id": key[0],
                    "stage": key[1],
                    "idempotency_key": desired_task_spec["idempotency_key"],
                    "desired": desired_task_spec,
                }
            )
            continue
        current = current_group[0]
        if len(current_group) > 1:
            actions.append(
                {
                    "action": "duplicate_task_review",
                    "case_id": key[0],
                    "stage": key[1],
                    "keep_task_id": current.get("id"),
                    "duplicate_task_ids": [task.get("id") for task in current_group[1:]],
                }
            )
        diff = _task_diff(current, desired_task_spec)
        if not diff:
            continue
        if str(current.get("status") or "").lower() in {"done", "archived"}:
            actions.append(
                {
                    "action": "preserve_completed_history",
                    "case_id": key[0],
                    "stage": key[1],
                    "task_id": current.get("id"),
                    "diff": diff,
                }
            )
        else:
            actions.append(
                {
                    "action": "update_task",
                    "case_id": key[0],
                    "stage": key[1],
                    "task_id": current.get("id"),
                    "diff": diff,
                    "desired": desired_task_spec,
                }
            )

    desired_keys = set(desired)
    for key, group in sorted(managed.items()):
        if key not in desired_keys:
            for task in group:
                actions.append(
                    {
                        "action": "block_orphan_task",
                        "case_id": key[0],
                        "stage": key[1],
                        "task_id": task.get("id"),
                    }
                )

    actions.extend(
        {
            "action": "preserve_unmanaged_task",
            "task_id": task.get("id"),
            "status": task.get("status"),
        }
        for task in sorted(unmanaged, key=lambda row: str(row.get("id") or ""))
    )
    canonical = json.dumps(actions, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "mode": "plan_only",
        "board": BOARD,
        "canonical_state": "data/events.jsonl",
        "case_projection": "data/master_cases.csv",
        "actions": actions,
        "plan_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "completed_history_rewritten": False,
        "kanban_mutated": False,
        "external_actions_executed": False,
    }


def safe_relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def apply_confirmed_plan(plan: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Any]:
    case_by_id = {str(case.get("case_id") or ""): case for case in cases}
    case_ids = sorted(
        {
            str(action.get("case_id") or "")
            for action in plan.get("actions") or []
            if action.get("action") == "create_task" and action.get("case_id")
        }
    )
    applied: dict[str, dict[str, str]] = {}
    for case_id in case_ids:
        case = case_by_id.get(case_id)
        if not case:
            raise ValueError(f"Confirmed plan references unknown case {case_id}")
        applied[case_id] = execute_graph(build_graph(case))
    return {
        "mode": "applied",
        "plan_sha256": plan.get("plan_sha256"),
        "case_graphs_applied": applied,
        "completed_history_rewritten": False,
        "external_actions_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", help="Optional Kanban JSON snapshot; live board is default")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--record-event", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--input-plan", help="Previously emitted plan required for --apply")
    parser.add_argument("--confirm-plan-sha256", help="Exact plan hash required for --apply")
    args = parser.parse_args()

    cases = load_csv(PROJECT_ROOT / "data" / "master_cases.csv")
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output

    if args.apply:
        if not args.input_plan or not args.confirm_plan_sha256:
            raise SystemExit("--apply requires --input-plan and --confirm-plan-sha256")
        plan_path = Path(args.input_plan)
        if not plan_path.is_absolute():
            plan_path = PROJECT_ROOT / plan_path
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if plan.get("mode") != "plan_only" or plan.get("plan_sha256") != args.confirm_plan_sha256:
            raise SystemExit("Plan mode/hash mismatch; no Kanban mutation performed")
        report = apply_confirmed_plan(plan, cases)
    else:
        if args.snapshot:
            snapshot = Path(args.snapshot)
            if not snapshot.is_absolute():
                snapshot = PROJECT_ROOT / snapshot
            payload = json.loads(snapshot.read_text(encoding="utf-8"))
            live_tasks = payload if isinstance(payload, list) else payload.get("tasks", [])
        else:
            live_tasks = fetch_live_tasks()
        event_projection = build_event_case_projection(load_events(PROJECT_ROOT / "data" / "events.jsonl"))
        report = build_live_reconciliation_plan(cases, event_projection, live_tasks)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(output, 0o600)
    print(f"Wrote {report['mode']} reconciliation with {len(report.get('actions', []))} actions to {output}")
    if report["mode"] == "plan_only":
        print(f"Plan SHA-256: {report['plan_sha256']}")
        print("Plan-only mode: no Hermes Kanban write was performed.")
    if args.record_event:
        append_event(
            "kanban.reconciliation_applied" if args.apply else "kanban.reconciliation_planned",
            "reconcile_hermes_kanban",
            object_type="kanban_reconciliation",
            object_id=safe_relative_path(output),
            payload={
                "mode": report["mode"],
                "plan_sha256": report.get("plan_sha256"),
                "actions": len(report.get("actions") or []),
            },
            citations=[safe_relative_path(output), "data/events.jsonl", "data/master_cases.csv"],
            idempotency_key=f"teos:kanban-reconciliation:{report.get('plan_sha256') or now_iso()}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
