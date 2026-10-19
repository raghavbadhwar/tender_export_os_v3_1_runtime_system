#!/usr/bin/env python3
"""Run and record the reproducible Tender OS upgrade Phase 0 gate."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "upgrade_baseline" / "validation.json"

PHASE0_COMMANDS: list[list[str]] = [
    ["scripts/validate_agent_loops.py"],
    ["scripts/validate_loop_schedule.py"],
    ["scripts/validate_register_schemas.py"],
    ["scripts/validate_event_type_registry.py"],
    ["scripts/check_projection_integrity.py", "--fail-on-drift"],
    ["scripts/evaluate_hermes_behavioral_contracts.py", "--validate-only"],
    ["scripts/tender_os_policy.py", "--self-test"],
    [
        "-m",
        "pytest",
        "-q",
        "tests/test_capture_upgrade_baseline.py",
        "tests/test_mcp_discovery_reliability.py",
        "tests/test_run_upgrade_phase0_validation.py",
    ],
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_commands(commands: Iterable[list[str]]) -> list[dict[str, Any]]:
    """Run every validator, preserving full stdout/stderr and never fail fast."""
    records: list[dict[str, Any]] = []
    for args in commands:
        command = [sys.executable, *args]
        timeout = 1200 if args[:2] == ["-m", "pytest"] else 300
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            completed = subprocess.CompletedProcess(
                command,
                124,
                stdout,
                f"{stderr}\nTimed out after {timeout}s".lstrip(),
            )
        records.append(
            {
                "command": command,
                "completed": completed,
                "duration_seconds": round(time.monotonic() - started, 3),
            }
        )
    return records


def build_report(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for record in records:
        completed: subprocess.CompletedProcess[str] = record["completed"]
        command = list(record["command"])
        results.append(
            {
                "command": command,
                "command_text": " ".join(str(part) for part in command),
                "cwd": str(PROJECT_ROOT),
                "returncode": completed.returncode,
                "ok": completed.returncode == 0,
                "duration_seconds": record["duration_seconds"],
                "stdout": completed.stdout or "",
                "stderr": completed.stderr or "",
            }
        )

    passed = sum(bool(result["ok"]) for result in results)
    failed = len(results) - passed
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "status": "PASS" if failed == 0 else "FAIL",
        "passed": passed,
        "failed": failed,
        "results": results,
        "safety_note": (
            "Phase 0 validation is local and read-only apart from this private receipt; "
            "it performs no sends, submissions, uploads, payments, DSC use, or commitments."
        ),
    }


def write_report(output: Path, report: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(output, 0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = PROJECT_ROOT / output

    report = build_report(run_commands(PHASE0_COMMANDS))
    write_report(output, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "passed": report["passed"],
                "failed": report["failed"],
                "output": str(output),
            },
            indent=2,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
