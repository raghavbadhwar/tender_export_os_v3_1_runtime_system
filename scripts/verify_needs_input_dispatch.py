#!/usr/bin/env python3
"""Prove a live needs_input card cannot auto-promote during dispatch."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOARD = "tender-export-os"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "kanban_task_graphs" / "needs_input_dispatch_receipt.json"
SAFE_BACKGROUND_STATUSES = {"done", "blocked", "archived"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def build_canary_body() -> str:
    handoff = {
        "case_id": "NEEDS_INPUT_CANARY",
        "workflow_type": "GOV",
        "stage": "approval",
        "source_event_ids": [],
        "input_artifacts": [],
        "required_output_schema": "config/schemas/mcp_tool_result.schema.json",
        "approval_required": True,
        "deadline": "",
        "stop_conditions": ["owner_approval"],
        "next_profile": "tender-export-os",
    }
    return "\n".join(
        [
            "TEOS_TYPED_HANDOFF_V1",
            json.dumps(handoff, sort_keys=True),
            "",
            "Internal Phase 2 canary. This card requires owner input and must remain blocked.",
            "block_kind: needs_input",
            "block_reason: owner_approval",
            "external_effect: false",
            "Do not run an agent and do not perform any external action.",
        ]
    )


def _task_record(show: dict[str, Any]) -> dict[str, Any]:
    task = show.get("task")
    return task if isinstance(task, dict) else show


def validate_needs_input_canary(
    before: dict[str, Any],
    after: dict[str, Any],
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    before_task = _task_record(before)
    after_task = _task_record(after)
    errors: list[str] = []
    status_before = str(before_task.get("status") or "").lower()
    status_after = str(after_task.get("status") or "").lower()
    if status_before != "blocked":
        errors.append(f"status before dispatcher is {status_before!r}, not blocked")
    if status_after != "blocked":
        errors.append(f"status after dispatcher is {status_after!r}, not blocked")
    events = before.get("events") if isinstance(before.get("events"), list) else []
    needs_input_event = any(
        event.get("kind") == "blocked"
        and isinstance(event.get("payload"), dict)
        and event["payload"].get("kind") == "needs_input"
        for event in events
        if isinstance(event, dict)
    )
    if not needs_input_event:
        errors.append("blocked event with kind needs_input is missing")
    if runs:
        errors.append("canary has worker runs")
    if before_task.get("started_at") is not None or after_task.get("started_at") is not None:
        errors.append("canary started a worker")
    if str(before_task.get("created_by") or "") != "verify_needs_input_dispatch":
        errors.append("canary creator identity is unexpected")
    return {
        "ok": not errors,
        "errors": errors,
        "task_id": str(before_task.get("id") or after_task.get("id") or ""),
        "status_before": status_before,
        "status_after": status_after,
        "needs_input_event_present": needs_input_event,
        "run_count": len(runs),
        "started_before": before_task.get("started_at"),
        "started_after": after_task.get("started_at"),
    }


def _run(command: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _json(command: list[str], *, timeout: int = 180) -> Any:
    completed = _run(command, timeout=timeout)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Hermes command failed")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Hermes command did not return JSON: {' '.join(command)}") from exc


def _task_id(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    nested = value.get("task") if isinstance(value.get("task"), dict) else {}
    return str(value.get("id") or value.get("task_id") or nested.get("id") or "")


def verify_live_needs_input() -> dict[str, Any]:
    tasks_before = _json(["hermes", "kanban", "--board", BOARD, "list", "--json"])
    unsafe = [
        {"id": row.get("id"), "status": row.get("status"), "title": row.get("title")}
        for row in tasks_before
        if isinstance(row, dict) and str(row.get("status") or "").lower() not in SAFE_BACKGROUND_STATUSES
    ]
    if unsafe:
        raise RuntimeError(f"Refusing dispatcher proof while unrelated runnable tasks exist: {unsafe}")

    created = _json(
        [
            "hermes",
            "kanban",
            "--board",
            BOARD,
            "create",
            "Phase 2 canary — needs_input must not auto-promote",
            "--body",
            build_canary_body(),
            "--assignee",
            "tender-export-os",
            "--workspace",
            f"dir:{PROJECT_ROOT}",
            "--tenant",
            "phase2-canary",
            "--idempotency-key",
            "teos:needs-input-canary:v1",
            "--max-runtime",
            "120",
            "--max-retries",
            "1",
            "--created-by",
            "verify_needs_input_dispatch",
            "--initial-status",
            "blocked",
            "--json",
        ]
    )
    task_id = _task_id(created)
    if not task_id:
        raise RuntimeError("Could not determine needs_input canary task id")

    before = _json(["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"])
    dispatch = _json(
        ["hermes", "kanban", "--board", BOARD, "dispatch", "--max", "1", "--json"],
        timeout=240,
    )
    after = _json(["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"])
    runs_value = _json(["hermes", "kanban", "--board", BOARD, "runs", task_id, "--json"])
    runs = runs_value if isinstance(runs_value, list) else []
    validation = validate_needs_input_canary(before, after, runs)

    archive = _run(["hermes", "kanban", "--board", BOARD, "archive", task_id])
    if archive.returncode != 0:
        validation["errors"].append(archive.stderr.strip() or "failed to archive canary")
        validation["ok"] = False
    archived = _json(["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"])
    archived_status = str(_task_record(archived).get("status") or "").lower()
    if archived_status != "archived":
        validation["errors"].append(f"canary cleanup status is {archived_status!r}, not archived")
        validation["ok"] = False

    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "status": "PASS" if validation["ok"] else "FAIL",
        "board": BOARD,
        "task_id": task_id,
        "dispatch_result": dispatch,
        "validation": validation,
        "cleanup_status": archived_status,
        "kanban_mutated": True,
        "mutation_scope": "created and archived one internal needs_input canary only",
        "agents_executed": False,
        "external_actions_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    report = verify_live_needs_input()
    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(output, 0o600)
    print(json.dumps({"status": report["status"], "task_id": report["task_id"], "cleanup": report["cleanup_status"], "output": str(output)}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
