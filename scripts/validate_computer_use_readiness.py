#!/usr/bin/env python3
"""Validate Computer Use readiness without starting a portal-assist session."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "computer_use_portal_assist.yaml"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "computer_use_readiness"
Runner = Callable[..., subprocess.CompletedProcess[str]]


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def run_command(command: list[str], *, runner: Runner = subprocess.run, timeout: int = 45) -> dict[str, Any]:
    try:
        completed = runner(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": exc.stdout if isinstance(exc.stdout, str) else "",
            "stderr": exc.stderr if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def summarize_output(text: str) -> dict[str, Any]:
    lowered = text.lower()
    return {
        "has_fail_marker": "❌" in text or " failed" in lowered or "error" in lowered,
        "has_warning_marker": "⚠" in text or "warning" in lowered,
        "accessibility_granted": "accessibility is granted" in lowered,
        "screen_recording_granted": "screen recording is granted" in lowered,
        "display_shareable_count_zero": "0 display(s) shareable" in lowered,
        "computer_use_available": "computer_use" in lowered,
    }


def build_readiness(*, config: dict[str, Any], runner: Runner = subprocess.run) -> dict[str, Any]:
    commands = {
        "hermes_doctor": run_command(["hermes", "doctor"], runner=runner, timeout=60),
        "computer_use_status": run_command(["hermes", "computer-use", "status"], runner=runner, timeout=30),
        "computer_use_doctor": run_command(["hermes", "computer-use", "doctor"], runner=runner, timeout=45),
    }
    summaries = {
        key: summarize_output(f"{value.get('stdout', '')}\n{value.get('stderr', '')}")
        for key, value in commands.items()
    }
    blockers: list[str] = []
    if commands["hermes_doctor"]["returncode"] != 0:
        blockers.append("hermes doctor failed")
    if commands["computer_use_status"]["returncode"] != 0:
        blockers.append("computer-use status failed")
    if commands["computer_use_doctor"]["returncode"] != 0:
        blockers.append("computer-use doctor failed")
    if summaries["computer_use_doctor"]["display_shareable_count_zero"]:
        blockers.append("computer-use doctor reports 0 display(s) shareable")
    if config.get("portal_assist_enabled") is not False:
        blockers.append("portal_assist_enabled must remain false until owner-approved case-scoped canary")
    remediation_steps: list[str] = []
    if "computer-use doctor reports 0 display(s) shareable" in blockers:
        remediation_steps.extend(
            [
                "Open the local desktop session with a visible display attached or shared.",
                "Confirm macOS Screen Recording and Accessibility permissions for the active Hermes/Codex runtime.",
                "Rerun: hermes computer-use doctor",
                "Rerun: python3 scripts/validate_computer_use_readiness.py --json",
                "Only after status is READY_WITH_WARNINGS, run a read-only case-scoped canary before any portal-assist session.",
            ]
        )

    return {
        "schema_version": "computer_use_readiness.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        # Hermes doctor can report unrelated optional integration warnings.  They
        # must not turn a healthy, locally verified Computer Use runtime into an
        # ambiguous readiness result.  This state means only that the next safe
        # action is the separately owner-approved, read-only canary; it never
        # enables portal assist.
        "status": "READY_FOR_READ_ONLY_CANARY" if not blockers else "BLOCKED",
        "portal_assist_enabled": False,
        "read_only_canary_required_before_portal_assist": True,
        "manual_observable_case_scope_required": True,
        "commands": commands,
        "summaries": summaries,
        "blockers": blockers,
        "remediation_steps": remediation_steps,
        "forbidden_actions": config.get("forbidden_actions", []),
        "external_actions_executed": False,
        "safety_note": "Readiness validation only. No browser, portal, login, form, upload, payment, DSC, or submission action was attempted.",
    }


def write_report(report: dict[str, Any], output_dir: Path = OUTPUT_DIR) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"computer_use_readiness_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"json": str(path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_readiness(config=load_config(Path(args.config).expanduser()))
    paths = write_report(report)
    payload = {
        "status": report["status"],
        "portal_assist_enabled": False,
        "blockers": report["blockers"],
        "json": paths["json"],
    }
    print(json.dumps(payload, indent=2) if args.json else f"Computer Use readiness {report['status']}: {paths['json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
