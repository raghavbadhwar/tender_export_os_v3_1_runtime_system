#!/usr/bin/env python3
"""Plan and apply deduplicated source-adapter degradation escalations."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOARD = "tender-export-os"
DEGRADED_STATUSES = {"ERROR", "BLOCKED", "EMPTY", "UNPROVEN", "FAIL", "FAILING"}
ADAPTER_SOURCES = {
    "cppp": ("CPPP — Central Public Procurement Portal", "GOV", "gov-tender-intelligence"),
    "gem": ("GeM — Government e-Marketplace", "GOV", "gov-tender-intelligence"),
    "ungm": ("UN Global Marketplace (UNGM)", "EXPORT", "export-buyer-intelligence"),
}


def _safe_int(value: Any) -> int:
    try:
        return int(float(str(value or 0)))
    except ValueError:
        return 0


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:64] or "source"


def build_degradation_actions(
    source_health: list[dict[str, Any]],
    canary_results: list[dict[str, Any]],
    *,
    threshold: int,
    receipt_path: str,
    increment_failure: bool = True,
) -> list[dict[str, Any]]:
    if threshold <= 0:
        raise ValueError("degradation threshold must be positive")
    health_by_name = {str(row.get("source_name") or ""): row for row in source_health}
    actions_by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for result in canary_results:
        adapter = str(result.get("adapter") or "").lower()
        default_name, default_workflow, default_profile = ADAPTER_SOURCES.get(
            adapter,
            (str(result.get("source_name") or adapter or "UNKNOWN_SOURCE"), "GOV", "tender-export-os"),
        )
        source_name = str(result.get("source_name") or default_name)
        health = health_by_name.get(source_name, {})
        status = str(result.get("status") or "").upper()
        if status not in DEGRADED_STATUSES:
            continue
        intentional_access_stop = (
            str(health.get("paywalled") or "").upper() == "TRUE"
            or str(health.get("login_required") or "").upper() == "TRUE"
            or str(health.get("health_status") or "").upper() in {"PAYWALLED", "LOGIN_REQUIRED", "NEEDS LOGIN"}
        )
        if intentional_access_stop:
            continue
        streak = _safe_int(health.get("consecutive_failures")) + (1 if increment_failure else 0)
        if streak < threshold:
            continue
        workflow = str(health.get("workflow") or default_workflow).upper()
        assignee = default_profile if default_profile != "tender-export-os" else (
            "export-buyer-intelligence" if workflow == "EXPORT" else "gov-tender-intelligence"
        )
        source_slug = _slug(source_name)
        idempotency_suffix = f"{source_slug}:streak-{streak}"
        handoff = {
            "case_id": f"SOURCE-{source_slug.upper()}",
            "workflow_type": workflow if workflow in {"GOV", "EXPORT"} else "GOV",
            "stage": "source_adapter_repair",
            "source_event_ids": [],
            "input_artifacts": [receipt_path],
            "required_output_schema": "config/schemas/mcp_tool_result.schema.json",
            "approval_required": False,
            "deadline": "",
            "stop_conditions": ["unavailable_credentials", "portal_human_challenge"],
            "next_profile": assignee,
        }
        body = "\n".join(
            [
                "TEOS_TYPED_HANDOFF_V1",
                json.dumps(handoff, sort_keys=True),
                "",
                f"Source: {source_name}",
                f"Adapter: {adapter}",
                f"Consecutive failure streak: {streak} (threshold {threshold})",
                f"Evidence receipt: {receipt_path}",
                "Diagnose or propose a source-adapter repair. Do not log in, bypass CAPTCHA/paywall, contact anyone, or execute an external action.",
                "external_effect: false",
            ]
        )
        action = {
            "source_name": source_name,
            "adapter": adapter,
            "workflow": workflow,
            "status": status,
            "consecutive_failures": streak,
            "threshold": threshold,
            "receipt_path": receipt_path,
            "artifact_path": str(result.get("artifact_path") or ""),
            "event_idempotency_key": f"teos:source-adapter-degraded:{idempotency_suffix}",
            "task": {
                "title": f"Repair degraded source adapter — {source_name} — streak {streak}",
                "body": body,
                "assignee": assignee,
                "idempotency_key": f"teos:source-repair:{idempotency_suffix}",
            },
        }
        actions_by_key[(source_name, streak)] = action
    return [actions_by_key[key] for key in sorted(actions_by_key)]


def apply_degradation_actions(
    actions: list[dict[str, Any]],
    *,
    event_appender: Callable[..., dict[str, Any]] | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[dict[str, str]]:
    if event_appender is None:
        # Cron invokes `scripts/run_live_source_canary.py` as a direct file,
        # where Python exposes the scripts directory rather than the project
        # root.  Support both direct execution and package imports.
        try:
            from scripts.event_ledger import append_event as event_appender
        except ModuleNotFoundError:  # pragma: no cover - direct cron execution
            from event_ledger import append_event as event_appender
    applied: list[dict[str, str]] = []
    for action in actions:
        citations = [action["receipt_path"]]
        if action.get("artifact_path"):
            citations.append(action["artifact_path"])
        event = event_appender(
            "source.adapter_degraded",
            "source_degradation",
            object_type="source_adapter",
            object_id=action["source_name"],
            source="source_health_runtime",
            payload={
                "source_name": action["source_name"],
                "adapter": action["adapter"],
                "status": action["status"],
                "consecutive_failures": action["consecutive_failures"],
                "threshold": action["threshold"],
                "receipt_path": action["receipt_path"],
            },
            citations=citations,
            idempotency_key=action["event_idempotency_key"],
        )
        task = action["task"]
        command = [
            "hermes", "kanban", "--board", BOARD, "create", task["title"],
            "--body", task["body"], "--assignee", task["assignee"],
            "--workspace", f"dir:{PROJECT_ROOT}", "--tenant", "source-repair",
            "--idempotency-key", task["idempotency_key"], "--max-runtime", "900",
            "--max-retries", "1", "--created-by", "source_degradation", "--json",
        ]
        completed = runner(command, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120, check=False)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "source repair card creation failed")
        value = json.loads(completed.stdout)
        task_id = str(value.get("id") or value.get("task_id") or (value.get("task") or {}).get("id") or "")
        if not task_id:
            raise RuntimeError("source repair card creation returned no task id")
        applied.append({"source_name": action["source_name"], "event_id": str(event["event_id"]), "task_id": task_id})
    return applied
