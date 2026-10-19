#!/usr/bin/env python3
"""Run separated no-Codex and Codex/Hermes readiness checks."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "regression"


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d%H%M%S")


def pytest_python(project_root: Path = PROJECT_ROOT) -> str:
    venv_python = project_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def no_codex_commands(stamp: str, project_root: Path = PROJECT_ROOT) -> list[list[str]]:
    safe_output = project_root / "outputs" / "regression" / f"safe_regression_for_matrix_{stamp}.json"
    return [
        ["python3", "scripts/validate_agent_loops.py"],
        ["python3", "scripts/validate_loop_schedule.py"],
        ["python3", "scripts/validate_register_schemas.py"],
        ["python3", "scripts/validate_event_type_registry.py"],
        ["python3", "scripts/run_full_safe_regression.py", "--output", str(safe_output)],
        [pytest_python(project_root), "-m", "pytest"],
    ]


def codex_commands() -> list[list[str]]:
    return [
        ["python3", "scripts/check_codex_runtime_readiness.py", "--timeout", "12"],
        ["python3", "scripts/system_health_check.py", "--runtime"],
    ]


def command_timeout(command: list[str]) -> int:
    joined = " ".join(command)
    if "-m pytest" in joined:
        return 900
    if "run_full_safe_regression.py" in joined or "system_health_check.py" in joined:
        return 900
    return 180


def run_command(command: list[str], project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=command_timeout(command),
            check=False,
        )
        return {
            "command": " ".join(command),
            "returncode": completed.returncode,
            "ok": completed.returncode == 0,
            "stdout_tail": completed.stdout[-3000:],
            "stderr_tail": completed.stderr[-3000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "command": " ".join(command),
            "returncode": None,
            "ok": False,
            "stdout_tail": stdout[-3000:],
            "stderr_tail": stderr[-3000:],
            "timed_out": True,
        }


Runner = Callable[[list[str]], dict[str, object]]


def run_lane(name: str, commands: list[list[str]], runner: Runner) -> dict[str, object]:
    results = [runner(command) for command in commands]
    failures = [result for result in results if not result.get("ok")]
    return {
        "name": name,
        "status": "PASS" if not failures else "FAIL",
        "results": results,
        "failures": failures,
    }


def codex_need(no_codex_lane: dict[str, object], codex_lane: dict[str, object]) -> dict[str, object]:
    core_passed = no_codex_lane["status"] == "PASS"
    codex_passed = codex_lane["status"] == "PASS"
    if core_passed and codex_passed:
        recommendation = "Core operating logic passes without Codex; use Codex for artifact/runtime-heavy work."
    elif core_passed:
        recommendation = "Core operating logic passes without Codex; Codex artifact/runtime work is currently blocked."
    else:
        recommendation = "Core checks failed; fix core repo/runtime logic before evaluating Codex need."
    return {
        "required_for_core": False if core_passed else None,
        "required_for_artifacts": True if codex_passed else False,
        "core_passed_without_codex": core_passed,
        "codex_runtime_available": codex_passed,
        "recommendation": recommendation,
    }


def build_matrix(
    *,
    stamp: str | None = None,
    runner: Runner | None = None,
    include_codex: bool = True,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    stamp = stamp or timestamp()
    runner = runner or (lambda command: run_command(command, project_root))
    no_codex_lane = run_lane("no_codex_core", no_codex_commands(stamp, project_root), runner)
    codex_lane = (
        run_lane("codex_hermes_runtime", codex_commands(), runner)
        if include_codex
        else {"name": "codex_hermes_runtime", "status": "SKIPPED", "results": [], "failures": []}
    )
    report = {
        "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "project_root": str(project_root),
        "lanes": {
            "no_codex_core": no_codex_lane,
            "codex_hermes_runtime": codex_lane,
        },
        "codex_need": codex_need(no_codex_lane, codex_lane) if include_codex else {
            "required_for_core": False if no_codex_lane["status"] == "PASS" else None,
            "required_for_artifacts": False,
            "core_passed_without_codex": no_codex_lane["status"] == "PASS",
            "codex_runtime_available": False,
            "recommendation": "Codex lane skipped; no-Codex result only.",
        },
        "safety_note": "These checks do not authorize external sends, submissions, payments, DSC use, or final commercial/compliance claims.",
    }
    report["status"] = "PASS" if all(
        lane["status"] in {"PASS", "SKIPPED"} for lane in report["lanes"].values()
    ) else "FAIL"
    return report


def write_matrix(report: dict[str, object], stamp: str, output_dir: Path = OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"operating_firm_test_matrix_{stamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run operating-firm test matrix")
    parser.add_argument("--skip-codex", action="store_true", help="Run only no-Codex core checks")
    args = parser.parse_args()
    stamp = timestamp()
    report = build_matrix(stamp=stamp, include_codex=not args.skip_codex)
    output = write_matrix(report, stamp)
    print(f"Operating firm test matrix {report['status']}: {output}")
    print(f"No-Codex lane: {report['lanes']['no_codex_core']['status']}")
    print(f"Codex lane: {report['lanes']['codex_hermes_runtime']['status']}")
    print(f"Codex required for core: {report['codex_need']['required_for_core']}")
    print(f"Codex required for artifacts: {report['codex_need']['required_for_artifacts']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
