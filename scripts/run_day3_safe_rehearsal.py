#!/usr/bin/env python3
"""Run Day 3 safe end-to-end hardening rehearsal.

All commands are read-only/dry-run safe. The runner writes a local report and
never sends, uploads, submits, pays, uses DSC, pauses cron, mutates Kanban, or
commits final price/classification/origin/compliance claims.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "day3_rehearsal" / "day3_safe_rehearsal_report.json"

SAFE_REHEARSAL_COMMANDS = [
    ["scripts/check_no_private_runtime_data.py", "--public-template"],
    ["scripts/check_chatgpt_return_loop.py", "--output", "outputs/day3_rehearsal/chatgpt_return_loop_check.json"],
    ["scripts/import_from_drive.py", "--group", "08_ChatGPT_Bridge", "--output", "outputs/day3_rehearsal/drive_import_chatgpt_bridge_dryrun_plan.json"],
    ["scripts/sync_to_drive.py", "--mode", "public-template", "--dry-run", "--output", "outputs/day3_rehearsal/drive_sync_public_template_dryrun.json"],
    ["scripts/sync_to_drive.py", "--mode", "private-runtime", "--dry-run", "--output", "outputs/day3_rehearsal/drive_sync_private_runtime_dryrun.json"],
    ["scripts/stage_deep_research_leads.py", "--input", "tests/fixtures/deep_research_leads/good_leads.json", "--dry-run"],
    ["scripts/kanban_blocked_task_drain.py", "--output", "outputs/day3_rehearsal/blocked_task_drain_plan.json"],
    ["scripts/check_codex_runtime_readiness.py", "--timeout", "8"],
    ["scripts/run_full_safe_regression.py", "--include-pytest"],
]

FORBIDDEN_TOKENS = {
    "--execute",
    "--record-event",
    "--apply",
    "submit",
    "upload-bid",
    "pay",
    "dsc",
    "send-message",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def command_is_safe(command: list[str]) -> bool:
    lowered = [part.lower() for part in command]
    if any(token in lowered for token in FORBIDDEN_TOKENS):
        return False
    text = " ".join(lowered)
    if "sync_to_drive.py" in text and "--dry-run" not in lowered:
        return False
    if "stage_deep_research_leads.py" in text and "--dry-run" not in lowered:
        return False
    return True


def run_command(command: list[str], timeout: int) -> dict[str, Any]:
    if not command_is_safe(command):
        return {
            "command": " ".join(command),
            "returncode": 99,
            "ok": False,
            "stdout_tail": "",
            "stderr_tail": "Command rejected by rehearsal safety guard.",
        }
    completed = subprocess.run(
        [sys.executable, *command],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return {
        "command": " ".join([sys.executable, *command]),
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def run_rehearsal(output: Path, timeout: int = 600) -> dict[str, Any]:
    results = [run_command(command, timeout) for command in SAFE_REHEARSAL_COMMANDS]
    report = {
        "generated_at": now_iso(),
        "mode": "safe_dry_run_rehearsal",
        "external_actions_executed": False,
        "drive_uploaded_or_downloaded": False,
        "kanban_mutated": False,
        "cron_mutated": False,
        "profile_mutated": False,
        "results": results,
        "status": "PASS" if all(item["ok"] for item in results) else "FAIL",
        "safety_note": "Day 3 rehearsal is dry-run/read-only only. No external send/submission/upload/payment/DSC/final claim was executed.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 3 safe end-to-end rehearsal")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    report = run_rehearsal(output, timeout=args.timeout)
    print(f"Day 3 safe rehearsal {report['status']}: {output}")
    for item in report["results"]:
        print(("PASS" if item["ok"] else "FAIL"), item["command"])
    print("No external action, Drive transfer, Kanban mutation, cron mutation, or profile mutation executed.")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
