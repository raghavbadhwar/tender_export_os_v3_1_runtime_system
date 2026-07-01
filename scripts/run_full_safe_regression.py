#!/usr/bin/env python3
"""Run the public-template safe regression suite."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.pipeline_error import blocked_error


SAFE_COMMANDS = [
    ["scripts/check_no_private_runtime_data.py", "--public-template"],
    ["scripts/system_health_check.py", "--public-template"],
    ["scripts/validate_event_type_registry.py"],
    ["scripts/validate_register_schemas.py", "--public-template"],
    ["scripts/validate_chatgpt_return.py", "--input", "tests/fixtures/chatgpt_returns/good_return.md"],
    ["scripts/test_source_adapters.py", "--safe", "--limit", "5"],
    ["scripts/setup_drive_folders.py", "--dry-run"],
]


def run_command(args: list[str]) -> dict:
    cmd = [sys.executable, *args]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120)
    return {
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
        "ok": result.returncode == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full safe regression")
    parser.add_argument("--include-pytest", action="store_true", help="Also run python -m pytest")
    parser.add_argument("--output", default="outputs/regression/full_safe_regression_report.json")
    args = parser.parse_args()
    commands = list(SAFE_COMMANDS)
    if args.include_pytest:
        commands.append(["-m", "pytest"])

    results = [run_command(command) for command in commands]
    failures = [result for result in results if not result["ok"]]
    report = {
        "status": "PASS" if not failures else "FAIL",
        "results": results,
        "failures": failures,
        "safety_note": "Safe regression performs no external sends, submissions, payments, uploads, DSC use, or final compliance claims.",
    }
    if failures:
        report["pipeline_error"] = blocked_error("safe_regression", f"{len(failures)} command(s) failed")
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Safe regression {report['status']}: {output}")
    for result in results:
        print(f"{'PASS' if result['ok'] else 'FAIL'} {result['command']}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
