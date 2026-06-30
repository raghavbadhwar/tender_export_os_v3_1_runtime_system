#!/usr/bin/env python3
"""Create a plan to reconcile local case state with Hermes Kanban."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path

from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
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


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def desired_task(case: dict) -> dict:
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


def next_action(case: dict) -> str:
    status = case.get("status", "")
    if status == "SUPPLIER_SEARCH":
        return "Complete supplier proof; do not price until two quote proofs exist."
    if status == "APPROVAL_REQUIRED":
        return "Owner must approve, reject, or ask changes from the approval card."
    if status == "PRICING_READY":
        return "Create artifacts and approval card before external action."
    if status == "FOLLOW_UP":
        return "Track buyer/supplier response and validity windows."
    if status in {"REJECTED", "WON", "LOST", "ARCHIVED"}:
        return "Archive or keep for weekly learning review."
    return "Route to next valid workflow stage."


def load_snapshot(path: Path | None) -> dict[str, dict]:
    if not path:
        return {}
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = data.get("tasks", data if isinstance(data, list) else [])
    return {task.get("case_id"): task for task in tasks if task.get("case_id")}


def build_plan(cases: list[dict], current_tasks: dict[str, dict]) -> dict:
    desired = {case.get("case_id"): desired_task(case) for case in cases if case.get("case_id")}
    actions = []
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

    return {
        "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "mode": "plan_only",
        "safety_note": "This plan does not write to Hermes Kanban. Review before executing with any future connector.",
        "actions": actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan Hermes Kanban reconciliation")
    parser.add_argument("--snapshot", help="Optional current Hermes Kanban JSON snapshot")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Plan output path")
    parser.add_argument("--record-event", action="store_true", help="Append kanban.reconciliation_planned event")
    args = parser.parse_args()

    snapshot = Path(args.snapshot) if args.snapshot else None
    if snapshot and not snapshot.is_absolute():
        snapshot = PROJECT_ROOT / snapshot
    current_tasks = load_snapshot(snapshot)
    cases = load_csv(PROJECT_ROOT / "data" / "master_cases.csv")
    plan = build_plan(cases, current_tasks)

    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"Wrote reconciliation plan with {len(plan['actions'])} actions to {output}")
    print("Plan-only mode: no Hermes Kanban writes performed.")

    if args.record_event:
        append_event(
            "kanban.reconciliation_planned",
            "reconcile_hermes_kanban",
            object_type="kanban_reconciliation",
            object_id=str(output.relative_to(PROJECT_ROOT)),
            payload={"actions": len(plan["actions"]), "output": str(output.relative_to(PROJECT_ROOT))},
            citations=[str(output.relative_to(PROJECT_ROOT)), "data/master_cases.csv"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
