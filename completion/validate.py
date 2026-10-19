#!/usr/bin/env python3
"""Validate and select bounded completion-plan tasks using only the standard library."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


STATUSES = {"pending", "ready", "blocked", "done"}
PRIORITIES = {"P0", "P1", "P2"}
TASK_FIELDS = {
    "id", "title", "priority", "status", "depends_on", "objective",
    "context_files", "allowed_paths", "max_changed_files", "steps", "checks",
    "acceptance", "stop_conditions", "evidence_receipt", "human_gate", "blocker",
}


def _safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def _within(path: str, roots: list[str]) -> bool:
    return any(path == root.rstrip("/") or path.startswith(root.rstrip("/") + "/") for root in roots)


def validate(plan: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    if plan.get("schema_version") != "completion_plan.v1":
        errors.append("schema_version must be completion_plan.v1")
    policy = plan.get("execution_policy")
    if not isinstance(policy, dict):
        errors.append("execution_policy must be an object")
        policy = {}
    for key in ("external_actions_allowed", "commit_allowed", "push_allowed", "deploy_allowed"):
        if policy.get(key) is not False:
            errors.append(f"execution_policy.{key} must be false")
    if policy.get("one_task_per_run") is not True:
        errors.append("execution_policy.one_task_per_run must be true")
    if policy.get("max_check_attempts") != 2:
        errors.append("execution_policy.max_check_attempts must be 2")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return errors + ["tasks must be a non-empty list"]
    task_map = {task.get("id"): task for task in tasks if isinstance(task, dict)}
    if len(task_map) != len(tasks) or None in task_map:
        errors.append("task ids must be present and unique")
    if len([task for task in tasks if isinstance(task, dict) and task.get("status") == "ready"]) > 1:
        errors.append("at most one task may be ready")
    for task in tasks:
        if not isinstance(task, dict):
            errors.append("every task must be an object")
            continue
        task_id = str(task.get("id", "<missing>"))
        missing = sorted(TASK_FIELDS - set(task))
        if missing:
            errors.append(f"{task_id}: missing fields: {', '.join(missing)}")
        if not re.fullmatch(r"[A-Z]+-[0-9]{2}", task_id):
            errors.append(f"{task_id}: invalid task id")
        if task.get("status") not in STATUSES:
            errors.append(f"{task_id}: invalid status")
        if task.get("priority") not in PRIORITIES:
            errors.append(f"{task_id}: invalid priority")
        dependencies = task.get("depends_on")
        if not isinstance(dependencies, list) or any(dep not in task_map or dep == task_id for dep in dependencies):
            errors.append(f"{task_id}: invalid dependencies")
            dependencies = []
        if task.get("status") == "ready" and any(task_map[dep].get("status") != "done" for dep in dependencies):
            errors.append(f"{task_id}: ready task has incomplete dependencies")
        for field, minimum, maximum in (("context_files", 1, 8), ("allowed_paths", 1, 8)):
            values = task.get(field)
            if not isinstance(values, list) or not minimum <= len(values) <= maximum or not all(_safe_path(v) for v in values):
                errors.append(f"{task_id}: {field} must contain {minimum}-{maximum} safe relative paths")
        max_files = task.get("max_changed_files")
        if not isinstance(max_files, int) or not 1 <= max_files <= 5:
            errors.append(f"{task_id}: max_changed_files must be 1-5")
        for field, minimum, maximum in (("steps", 1, 7), ("checks", 1, 7), ("acceptance", 1, 8), ("stop_conditions", 2, 8)):
            values = task.get(field)
            if not isinstance(values, list) or not minimum <= len(values) <= maximum or not all(isinstance(v, str) and v.strip() for v in values):
                errors.append(f"{task_id}: {field} must contain {minimum}-{maximum} non-empty strings")
        receipt = task.get("evidence_receipt")
        if not _safe_path(receipt) or receipt != f"completion/evidence/{task_id}.json":
            errors.append(f"{task_id}: evidence_receipt must be completion/evidence/{task_id}.json")
        if task.get("status") == "blocked" and not isinstance(task.get("blocker"), str):
            errors.append(f"{task_id}: blocked task requires blocker text")
        if task.get("human_gate") not in {True, False}:
            errors.append(f"{task_id}: human_gate must be boolean")
        if task.get("status") == "done" and isinstance(receipt, str):
            receipt_path = root / receipt
            if not receipt_path.is_file():
                errors.append(f"{task_id}: done task has no evidence receipt")
                continue
            try:
                evidence = json.loads(receipt_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                errors.append(f"{task_id}: evidence receipt is invalid JSON")
                continue
            if evidence.get("schema_version") != "completion_evidence.v1" or evidence.get("task_id") != task_id or evidence.get("result") != "pass":
                errors.append(f"{task_id}: evidence identity/result is invalid")
            if evidence.get("external_actions_executed") is not False:
                errors.append(f"{task_id}: evidence must record no external actions")
            changed = evidence.get("files_changed")
            allowed = task.get("allowed_paths") if isinstance(task.get("allowed_paths"), list) else []
            if not isinstance(changed, list) or len(changed) > max_files or not all(_safe_path(p) and _within(p, allowed) for p in changed):
                errors.append(f"{task_id}: evidence files exceed task scope")
            checks = evidence.get("checks")
            expected = task.get("checks")
            if not isinstance(checks, list) or [item.get("command") for item in checks if isinstance(item, dict)] != expected or any(item.get("exit_code") != 0 for item in checks if isinstance(item, dict)):
                errors.append(f"{task_id}: evidence checks do not match zero-exit task checks")
    return errors


def _self_check() -> int:
    good = {"schema_version": "completion_plan.v1", "project": "self-check", "execution_policy": {"one_task_per_run": True, "max_check_attempts": 2, "external_actions_allowed": False, "commit_allowed": False, "push_allowed": False, "deploy_allowed": False}, "tasks": [{"id": "TEST-01", "title": "check", "priority": "P0", "status": "ready", "depends_on": [], "objective": "validate", "context_files": ["README.md"], "allowed_paths": ["README.md"], "max_changed_files": 1, "steps": ["inspect"], "checks": ["true"], "acceptance": ["passes"], "stop_conditions": ["scope changes", "tool missing"], "evidence_receipt": "completion/evidence/TEST-01.json", "human_gate": False, "blocker": None}]}
    assert validate(good, Path.cwd()) == []
    good["execution_policy"]["external_actions_allowed"] = True
    assert validate(good, Path.cwd())
    print("completion validator self-check: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=Path("completion/plan.json"))
    parser.add_argument("--next", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        return _self_check()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    errors = validate(plan, Path.cwd())
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
        return 1
    ready = next((task for task in plan["tasks"] if task["status"] == "ready"), None)
    print(json.dumps({"status": "PASS", "next_task": ready if args.next else (ready or {}).get("id")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

