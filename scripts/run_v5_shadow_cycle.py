#!/usr/bin/env python3
"""Run the V5 demand-forecast shadow pipeline sequentially and fail fast."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "demand_forecasting"
Runner = Callable[..., subprocess.CompletedProcess[str]]


def python_for(project_root: Path) -> str:
    repository_python = project_root / ".venv" / "bin" / "python"
    return str(repository_python) if repository_python.is_file() else sys.executable


def cycle_commands(project_root: Path = PROJECT_ROOT) -> list[list[str]]:
    python = python_for(project_root)
    return [
        [python, "scripts/build_buyer_purchase_history.py", "--write"],
        [python, "scripts/build_category_demand_history.py", "--write"],
        [python, "scripts/generate_v5_demand_forecast_low_competition.py", "--write-candidates"],
        [python, "scripts/backtest_v5_demand_forecasts.py", "--write"],
        [python, "scripts/evaluate_forecast_calibration.py", "--write", "--json"],
    ]


def run_cycle(
    *,
    project_root: Path = PROJECT_ROOT,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    for command in cycle_commands(project_root):
        completed = runner(
            command,
            cwd=project_root,
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
        result = {
            "command": command,
            "exit_code": completed.returncode,
            "status": "PASS" if completed.returncode == 0 else "FAIL",
            "stdout_tail": (completed.stdout or "")[-2000:],
            "stderr_tail": (completed.stderr or "")[-2000:],
        }
        steps.append(result)
        if completed.returncode != 0:
            break

    failed = next((step for step in steps if step["status"] == "FAIL"), None)
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "FAIL" if failed else "PASS",
        "exit_code": int(failed["exit_code"]) if failed else 0,
        "steps": steps,
        "external_business_actions": False,
        "approval_boundary": "Internal shadow projections only; forecasts remain advisory until evidence and owner gates pass.",
    }


def main() -> int:
    report = run_cycle()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUTPUT_DIR / f"v5_shadow_cycle_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"V5 shadow cycle {report['status']}: {path}")
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
