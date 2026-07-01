#!/usr/bin/env python3
"""Plan a dry-run drain of stale Hermes Kanban blocked tasks.

This script never mutates Hermes Kanban by default. It reads a JSON snapshot or
calls the Hermes CLI, classifies stale blocked tasks, and writes a review plan.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "kanban_blocked_task_drain" / "blocked_task_drain_plan.json"


def parse_time(value: Any) -> dt.datetime | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value, dt.timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def load_tasks_from_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("tasks", "items", "rows", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    raise ValueError(f"Unsupported Kanban JSON shape in {path}")


def task_text(task: dict[str, Any]) -> str:
    values = [
        task.get("title"),
        task.get("body"),
        task.get("description"),
        task.get("blocked_reason"),
        task.get("status_reason"),
        task.get("last_comment"),
    ]
    return " ".join(str(v or "") for v in values).lower()


def task_id(task: dict[str, Any]) -> str:
    return str(task.get("id") or task.get("task_id") or task.get("uuid") or "")


def classify_task(task: dict[str, Any]) -> tuple[str, str, str]:
    text = task_text(task)
    if any(word in text for word in ["rejected", "obsolete", "duplicate", "closed", "done", "archived"]):
        return "ARCHIVE_OR_CLOSE_REVIEW", "hermes-chief-operator", "Likely obsolete/done-like blocker. Review then archive/close manually if safe."
    if any(word in text for word in ["approval", "owner", "decision", "approve", "ask changes"]):
        return "ESCALATE_OWNER_APPROVAL", "hermes-chief-operator", "Blocked on owner/approval decision. Create or refresh approval card; do not mutate task automatically."
    if any(word in text for word in ["source", "adapter", "portal", "captcha", "paywall", "login", "timeout", "broken"]):
        return "REASSIGN_SOURCE_HEALTH", "source-health", "Blocked on source/access/runtime health. Route diagnosis to source-health."
    if any(word in text for word in ["supplier", "quote", "availability", "5-3-2"]):
        return "REASSIGN_SUPPLIER_SOURCING", "supplier-sourcing", "Blocked on supplier proof or quote availability. Route to supplier-sourcing."
    if any(word in text for word in ["pricing", "compliance", "hsn", "itc", "origin"]):
        return "REASSIGN_PRICING_COMPLIANCE", "pricing-compliance", "Blocked on draft pricing/compliance evidence. Route to pricing-compliance; final claims remain gated."
    return "COMMENT_AND_REVIEW", str(task.get("assignee") or "hermes-chief-operator"), "Stale blocker needs human-readable comment, owner review, or reassignment."


def task_age_hours(task: dict[str, Any], now: dt.datetime) -> float | None:
    timestamp = parse_time(task.get("updated_at") or task.get("blocked_at") or task.get("created_at"))
    if timestamp is None:
        return None
    return (now - timestamp).total_seconds() / 3600


def build_blocked_task_drain_plan(
    tasks: list[dict[str, Any]],
    *,
    now: dt.datetime | None = None,
    stale_hours: int = 24,
) -> dict[str, Any]:
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    actions = []
    blocked = [task for task in tasks if str(task.get("status", "")).lower() == "blocked"]
    for task in blocked:
        age = task_age_hours(task, now)
        stale = age is None or age >= stale_hours
        if not stale:
            continue
        recommended, assignee, reason = classify_task(task)
        actions.append(
            {
                "task_id": task_id(task),
                "title": task.get("title", ""),
                "current_assignee": task.get("assignee", ""),
                "age_hours": None if age is None else round(age, 1),
                "recommended_action": recommended,
                "suggested_assignee": assignee,
                "reason": reason,
                "command_hints_not_executed": command_hints(task, recommended, assignee),
            }
        )
    return {
        "generated_at": now.isoformat(),
        "mode": "dry_run_only",
        "kanban_mutated": False,
        "external_actions_executed": False,
        "stale_hours": stale_hours,
        "summary": {
            "tasks_seen": len(tasks),
            "blocked_count": len(blocked),
            "stale_blocked_count": len(actions),
        },
        "actions": actions,
        "safety_note": "No Hermes Kanban task was edited. Review actions before running any block/unblock/comment/archive command.",
    }


def command_hints(task: dict[str, Any], action: str, assignee: str) -> list[str]:
    tid = task_id(task)
    if not tid:
        return []
    if action.startswith("REASSIGN"):
        return [f"hermes kanban --board tender-export-os reassign {tid} {assignee}"]
    if action == "ESCALATE_OWNER_APPROVAL":
        return [f"hermes kanban --board tender-export-os comment {tid} 'Owner approval still required; refresh approval card.'"]
    if action == "ARCHIVE_OR_CLOSE_REVIEW":
        return [f"hermes kanban --board tender-export-os archive {tid}"]
    return [f"hermes kanban --board tender-export-os comment {tid} 'Stale blocker reviewed; next action needed.'"]


def fetch_kanban_tasks() -> list[dict[str, Any]]:
    result = subprocess.run(
        ["hermes", "kanban", "--board", "tender-export-os", "list", "--json"],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "hermes kanban list failed")
    tmp = PROJECT_ROOT / "outputs" / "kanban_blocked_task_drain" / "latest_kanban_snapshot.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(result.stdout, encoding="utf-8")
    return load_tasks_from_json(tmp)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create dry-run plan for stale blocked Hermes Kanban tasks")
    parser.add_argument("--input", help="Optional Hermes Kanban JSON snapshot")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--stale-hours", type=int, default=24)
    args = parser.parse_args()

    if args.input:
        tasks = load_tasks_from_json(Path(args.input))
    else:
        tasks = fetch_kanban_tasks()
    plan = build_blocked_task_drain_plan(tasks, stale_hours=args.stale_hours)
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Kanban blocked-task drain dry-run plan: {output}")
    print(f"Blocked={plan['summary']['blocked_count']} stale={plan['summary']['stale_blocked_count']}")
    print("No Kanban mutation or external action was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
