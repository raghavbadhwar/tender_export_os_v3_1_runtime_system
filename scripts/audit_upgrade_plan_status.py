#!/usr/bin/env python3
"""Audit upgrade-plan task status against current readiness evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = PROJECT_ROOT / "plan" / "upgrade-hermes-tender-export-os-1.md"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "production_readiness"
ALLOWED_SENTINEL_YELLOW_TASKS = {"TASK-103"}

TASK_ROW_RE = re.compile(r"^\|\s*(TASK-\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$")


def load_plan(path: Path = DEFAULT_PLAN) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    frontmatter: dict[str, Any] = {}
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end >= 0:
            payload = yaml.safe_load(text[4:end]) or {}
            if isinstance(payload, dict):
                frontmatter = payload
    return frontmatter, text


def parse_task_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = TASK_ROW_RE.match(line)
        if not match:
            continue
        task_id, description, completed, date = match.groups()
        rows.append(
            {
                "task_id": task_id.strip(),
                "description": description.strip(),
                "completed": completed.strip(),
                "date": date.strip(),
                "line": str(line_no),
            }
        )
    return rows


def latest_json(pattern: str) -> tuple[Path | None, dict[str, Any]]:
    matches = sorted(PROJECT_ROOT.glob(pattern), key=lambda path: path.stat().st_mtime if path.exists() else 0)
    if not matches:
        return None, {}
    path = matches[-1]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return path, {}
    return path, payload if isinstance(payload, dict) else {}


def status_kind(value: str) -> str:
    if "✅" in value:
        return "complete"
    if "🟡" in value:
        return "blocked_or_in_progress"
    if "❌" in value:
        return "failed"
    return "unknown"


def audit_plan(*, plan_path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    frontmatter, text = load_plan(plan_path)
    rows = parse_task_rows(text)
    readiness_path, readiness = latest_json("outputs/production_readiness/final_readiness_*.json")
    gate_path, gate = latest_json("outputs/production_readiness/production_readiness_gate_*.json")
    blocker_ids = {
        str(row.get("task_id"))
        for row in readiness.get("blocking_tasks", [])
        if isinstance(row, dict) and row.get("task_id")
    }
    yellow_ids = {row["task_id"] for row in rows if status_kind(row["completed"]) == "blocked_or_in_progress"}
    failed_ids = sorted(row["task_id"] for row in rows if status_kind(row["completed"]) == "failed")
    unknown_ids = sorted(row["task_id"] for row in rows if status_kind(row["completed"]) == "unknown")
    errors: list[str] = []
    warnings: list[str] = []

    if failed_ids:
        errors.append(f"failed task rows present: {', '.join(failed_ids)}")
    if unknown_ids:
        errors.append(f"unknown task status rows present: {', '.join(unknown_ids)}")
    missing_yellow = sorted(blocker_ids - yellow_ids)
    stale_yellow = sorted(yellow_ids - blocker_ids - ALLOWED_SENTINEL_YELLOW_TASKS)
    if missing_yellow:
        errors.append(f"readiness blockers not marked yellow in plan: {', '.join(missing_yellow)}")
    if stale_yellow:
        warnings.append(f"yellow plan rows not currently in readiness blockers: {', '.join(stale_yellow)}")

    today = dt.date.today().isoformat()
    last_updated = str(frontmatter.get("last_updated") or "")
    latest_task_date = max((row["date"] for row in rows if row["date"]), default="")
    if last_updated and latest_task_date and last_updated < latest_task_date:
        warnings.append(f"frontmatter last_updated {last_updated} is older than latest task date {latest_task_date}")
    if last_updated and last_updated < today and latest_task_date == today:
        warnings.append(f"frontmatter last_updated {last_updated} is older than today {today}")

    readiness_status = readiness.get("status") or "MISSING"
    gate_status = gate.get("status") or "MISSING"
    if not readiness_path:
        errors.append("final readiness receipt missing")
    if not gate_path:
        errors.append("production readiness gate report missing")

    return {
        "schema_version": "upgrade_plan_status_audit.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS" if not errors else "FAIL",
        "plan_path": str(plan_path),
        "frontmatter": {
            "status": frontmatter.get("status"),
            "last_updated": last_updated,
        },
        "task_count": len(rows),
        "complete_task_count": sum(1 for row in rows if status_kind(row["completed"]) == "complete"),
        "yellow_task_ids": sorted(yellow_ids),
        "allowed_sentinel_yellow_task_ids": sorted(ALLOWED_SENTINEL_YELLOW_TASKS & yellow_ids),
        "readiness_blocker_ids": sorted(blocker_ids),
        "failed_task_ids": failed_ids,
        "unknown_task_ids": unknown_ids,
        "readiness_receipt": str(readiness_path) if readiness_path else "",
        "readiness_status": readiness_status,
        "production_readiness_gate": str(gate_path) if gate_path else "",
        "production_readiness_gate_status": gate_status,
        "errors": errors,
        "warnings": warnings,
        "external_actions_executed": False,
        "production_routing_enabled": False,
        "safety_note": "Plan audit only. It reads local plan/readiness artifacts and performs no approvals, routing changes, external actions, or plan mutation.",
    }


def write_report(report: dict[str, Any], output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"upgrade_plan_status_audit_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default=str(DEFAULT_PLAN))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = audit_plan(plan_path=Path(args.plan).expanduser())
    path = write_report(report, Path(args.output_dir).expanduser())
    payload = {
        "status": report["status"],
        "task_count": report["task_count"],
        "yellow_task_ids": report["yellow_task_ids"],
        "readiness_blocker_ids": report["readiness_blocker_ids"],
        "errors": report["errors"],
        "warnings": report["warnings"],
        "report": str(path),
        "external_actions_executed": False,
        "production_routing_enabled": False,
    }
    print(json.dumps(payload, indent=2) if args.json else f"Upgrade plan status audit {report['status']}: {path}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
