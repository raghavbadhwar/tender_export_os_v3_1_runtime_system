#!/usr/bin/env python3
"""Create a read-only recovery plan for unhealthy Hermes Kanban tasks.

This module deliberately has no apply mode.  It identifies tasks that may be
reclaimed or must be blocked, but a separate owner-reviewed operation is
required to mutate the board.  In particular, an external-effect task is never
made retryable by this planner.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import signal
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOARD = "tender-export-os"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "system_health" / "kanban_recovery_plan.json"
TERMINAL_STATUSES = {"done", "archived", "cancelled", "canceled"}


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _as_utc(value: Any) -> dt.datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.fromtimestamp(float(value), tz=dt.timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return dt.datetime.fromtimestamp(float(text), tz=dt.timezone.utc)
    except (OverflowError, OSError, ValueError):
        pass
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _parse_handoff(body: str) -> dict[str, Any] | None:
    lines = body.splitlines()
    try:
        index = lines.index("TEOS_TYPED_HANDOFF_V1")
    except ValueError:
        return None
    if index + 1 >= len(lines):
        return None
    try:
        value = json.loads(lines[index + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _is_external_effect(task: dict[str, Any]) -> bool:
    if task.get("external_effect") is True:
        return True
    body = str(task.get("body") or "")
    for line in body.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip().lower() == "external_effect":
            return value.strip().lower() in {"true", "yes", "1"}
    return False


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, signal.SIG_DFL)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _task_identity(task: dict[str, Any]) -> tuple[str, str] | None:
    handoff = _parse_handoff(str(task.get("body") or ""))
    if not handoff:
        return None
    case_id = str(handoff.get("case_id") or "").strip()
    stage = str(handoff.get("stage") or "").strip()
    return (case_id, stage) if case_id and stage else None


def _created_sort_key(task: dict[str, Any]) -> tuple[float, str]:
    created = _as_utc(task.get("created_at"))
    timestamp = created.timestamp() if created else float("inf")
    return timestamp, str(task.get("id") or "")


def _age_seconds(task: dict[str, Any], now: dt.datetime) -> float | None:
    heartbeat = _as_utc(task.get("last_heartbeat_at"))
    started = _as_utc(task.get("started_at"))
    created = _as_utc(task.get("created_at"))
    anchor = heartbeat or started or created
    return max(0.0, (now - anchor).total_seconds()) if anchor else None


def _action(task: dict[str, Any], action: str, reason: str, **extra: Any) -> dict[str, Any]:
    row = {
        "task_id": str(task.get("id") or ""),
        "action": action,
        "reason": reason,
        "current_status": str(task.get("status") or ""),
        "assignee": str(task.get("assignee") or ""),
    }
    row.update(extra)
    return row


def build_recovery_plan(
    tasks: Iterable[dict[str, Any]],
    *,
    known_profiles: set[str],
    known_case_ids: set[str],
    now: dt.datetime | None = None,
    stale_timeout_seconds: int = 14_400,
    failure_limit: int = 2,
    pid_is_alive: Callable[[int], bool] = _pid_is_alive,
) -> dict[str, Any]:
    """Classify unsafe or recoverable tasks without changing board state."""
    if stale_timeout_seconds <= 0:
        raise ValueError("stale_timeout_seconds must be positive")
    if failure_limit <= 0:
        raise ValueError("failure_limit must be positive")

    current_time = (now or _utc_now()).astimezone(dt.timezone.utc)
    task_rows = [dict(task) for task in tasks if isinstance(task, dict)]
    actions: list[dict[str, Any]] = []
    actioned: set[str] = set()

    # Duplicate safety is based only on typed, non-terminal case-stage tasks.
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for task in task_rows:
        identity = _task_identity(task)
        status = str(task.get("status") or "").lower()
        if identity and status not in TERMINAL_STATUSES:
            groups[identity].append(task)
    for (case_id, stage), group in sorted(groups.items()):
        if len(group) < 2:
            continue
        ordered = sorted(group, key=_created_sort_key)
        keeper = ordered[0]
        for duplicate in ordered[1:]:
            task_id = str(duplicate.get("id") or "")
            actions.append(
                _action(
                    duplicate,
                    "BLOCK_DUPLICATE",
                    "A newer active task exists for the same typed case stage.",
                    case_id=case_id,
                    stage=stage,
                    keep_task_id=str(keeper.get("id") or ""),
                    requires_owner_review=True,
                )
            )
            actioned.add(task_id)

    for task in sorted(task_rows, key=lambda row: str(row.get("id") or "")):
        task_id = str(task.get("id") or "")
        if not task_id or task_id in actioned:
            continue
        status = str(task.get("status") or "").lower()
        if status in TERMINAL_STATUSES:
            continue

        identity = _task_identity(task)
        if identity is None:
            actions.append(
                _action(
                    task,
                    "BLOCK_UNTYPED_TASK",
                    "Task has no valid TEOS typed handoff and cannot be recovered automatically.",
                    requires_owner_review=True,
                )
            )
            continue
        case_id, stage = identity
        common = {"case_id": case_id, "stage": stage}

        if case_id not in known_case_ids:
            actions.append(
                _action(
                    task,
                    "BLOCK_ORPHAN",
                    "Typed task references a case that is absent from the canonical case projection.",
                    **common,
                    requires_owner_review=True,
                )
            )
            continue
        if str(task.get("assignee") or "") not in known_profiles:
            actions.append(
                _action(
                    task,
                    "BLOCK_UNKNOWN_ASSIGNEE",
                    "Assignee is not a registered live Hermes profile or approved worker lane.",
                    **common,
                    requires_owner_review=True,
                )
            )
            continue

        failures = int(task.get("consecutive_failures") or task.get("failure_count") or 0)
        if _is_external_effect(task) and failures > 0:
            actions.append(
                _action(
                    task,
                    "BLOCK_EXTERNAL_EFFECT_RETRY",
                    "An external-effect attempt cannot be retried after failure without a new exact-scope owner command.",
                    **common,
                    failure_count=failures,
                    requires_new_owner_command=True,
                    requires_owner_review=True,
                )
            )
            continue
        if failures >= failure_limit:
            actions.append(
                _action(
                    task,
                    "AUTO_BLOCK_FAILURE_LIMIT",
                    "The configured consecutive-failure limit has been reached.",
                    **common,
                    failure_count=failures,
                    failure_limit=failure_limit,
                    requires_owner_review=True,
                )
            )
            continue

        if status != "running":
            continue
        age = _age_seconds(task, current_time)
        pid_value = task.get("worker_pid")
        try:
            pid = int(pid_value) if pid_value not in (None, "") else None
        except (TypeError, ValueError):
            pid = None
        if age is not None and age >= stale_timeout_seconds:
            actions.append(
                _action(
                    task,
                    "RECLAIM_STALE_WORKER",
                    "Worker heartbeat exceeded the configured stale timeout.",
                    **common,
                    worker_pid=pid,
                    heartbeat_age_seconds=int(age),
                    stale_timeout_seconds=stale_timeout_seconds,
                    safe_to_reclaim=True,
                )
            )
            continue
        if pid is None or not pid_is_alive(pid):
            actions.append(
                _action(
                    task,
                    "RECLAIM_DEAD_WORKER",
                    "Worker PID is absent or no longer alive.",
                    **common,
                    worker_pid=pid,
                    heartbeat_age_seconds=int(age) if age is not None else None,
                    safe_to_reclaim=True,
                )
            )

    action_order = {
        "BLOCK_DUPLICATE": 0,
        "BLOCK_UNTYPED_TASK": 1,
        "BLOCK_ORPHAN": 2,
        "BLOCK_UNKNOWN_ASSIGNEE": 3,
        "BLOCK_EXTERNAL_EFFECT_RETRY": 4,
        "AUTO_BLOCK_FAILURE_LIMIT": 5,
        "RECLAIM_STALE_WORKER": 6,
        "RECLAIM_DEAD_WORKER": 7,
    }
    actions.sort(key=lambda row: (action_order.get(row["action"], 99), row["task_id"]))
    canonical = json.dumps(actions, sort_keys=True, separators=(",", ":"))
    counts: dict[str, int] = defaultdict(int)
    for row in actions:
        counts[row["action"]] += 1
    return {
        "schema_version": 1,
        "generated_at": current_time.replace(microsecond=0).isoformat(),
        "mode": "plan_only",
        "board": BOARD,
        "task_count": len(task_rows),
        "actions": actions,
        "summary": {
            "action_count": len(actions),
            "by_action": dict(sorted(counts.items())),
            "safe_reclaims": sum(1 for row in actions if row.get("safe_to_reclaim") is True),
            "owner_review_blocks": sum(1 for row in actions if row.get("requires_owner_review") is True),
        },
        "plan_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "reclaim_invariant": "worker_pid_gone_or_stale_timeout_exceeded",
        "external_effect_retry_requires_new_owner_command": True,
        "kanban_mutated": False,
        "external_actions_executed": False,
    }


def _run_json(command: list[str]) -> Any:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"command failed: {' '.join(command)}")
    return json.loads(completed.stdout)


def fetch_live_tasks() -> list[dict[str, Any]]:
    value = _run_json(["hermes", "kanban", "--board", BOARD, "list", "--json"])
    if not isinstance(value, list):
        raise RuntimeError("Hermes Kanban task list returned an unexpected JSON shape")
    return [row for row in value if isinstance(row, dict)]


def fetch_known_profiles() -> set[str]:
    value = _run_json(["hermes", "kanban", "--board", BOARD, "assignees", "--json"])
    rows = value if isinstance(value, list) else value.get("assignees", []) if isinstance(value, dict) else []
    profiles: set[str] = set()
    for row in rows:
        if isinstance(row, str):
            profiles.add(row)
        elif isinstance(row, dict):
            name = row.get("profile") or row.get("name") or row.get("assignee")
            if name:
                profiles.add(str(name))
    if not profiles:
        raise RuntimeError("Hermes Kanban assignee registry returned no profiles")
    return profiles


def load_known_case_ids(path: Path) -> set[str]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return {str(row.get("case_id") or "") for row in csv.DictReader(handle) if row.get("case_id")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", help="Optional task-list JSON; defaults to live read-only Kanban inspection")
    parser.add_argument("--profiles", help="Optional JSON list of known profiles for offline validation")
    parser.add_argument("--cases", default="data/master_cases.csv")
    parser.add_argument("--stale-timeout-seconds", type=int, default=14_400)
    parser.add_argument("--failure-limit", type=int, default=2)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    if args.snapshot:
        raw = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        tasks = raw if isinstance(raw, list) else raw.get("tasks", [])
    else:
        tasks = fetch_live_tasks()
    if args.profiles:
        raw_profiles = json.loads(Path(args.profiles).read_text(encoding="utf-8"))
        known_profiles = {str(value) for value in raw_profiles}
    else:
        known_profiles = fetch_known_profiles()

    cases_path = Path(args.cases).expanduser()
    if not cases_path.is_absolute():
        cases_path = PROJECT_ROOT / cases_path
    report = build_recovery_plan(
        tasks,
        known_profiles=known_profiles,
        known_case_ids=load_known_case_ids(cases_path),
        stale_timeout_seconds=args.stale_timeout_seconds,
        failure_limit=args.failure_limit,
    )
    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    os.chmod(output, 0o600)
    print(json.dumps({"status": "PASS", "mode": "plan_only", "actions": len(report["actions"]), "output": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
