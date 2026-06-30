#!/usr/bin/env python3
"""Check Hermes and Codex runtime readiness without assuming CLI syntax."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "runtime_readiness_report.json"


COMMANDS = {
    "hermes_path": ["hermes", "--help"],
    "hermes_doctor": ["hermes", "doctor"],
    "hermes_tools_help": ["hermes", "tools", "--help"],
    "hermes_skills_help": ["hermes", "skills", "--help"],
    "hermes_mcp_help": ["hermes", "mcp", "--help"],
    "hermes_kanban_help": ["hermes", "kanban", "--help"],
    "hermes_cron_help": ["hermes", "cron", "--help"],
    "codex_version": ["codex", "--version"],
    "codex_help": ["codex", "--help"],
    "codex_doctor": ["codex", "doctor"],
    "codex_plugin_inventory": ["codex", "plugin", "list", "--available", "--json"],
    "codex_app_server_help": ["codex", "app-server", "--help"],
}


KEYWORDS = {
    "hermes_path": ["cron", "kanban", "skills", "memory", "tools", "mcp", "gateway", "sessions"],
    "codex_help": ["app-server", "plugin", "doctor", "mcp", "exec"],
    "codex_app_server_help": ["app-server"],
}


def run_command(command: list[str], timeout: int, truncate_stdout: bool = True) -> dict:
    executable = shutil.which(command[0])
    if not executable:
        return {
            "available": False,
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": f"{command[0]} not found on PATH",
            "timed_out": False,
        }

    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        stdout = completed.stdout[-12000:] if truncate_stdout else completed.stdout
        return {
            "available": True,
            "path": executable,
            "command": command,
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": completed.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "available": True,
            "path": executable,
            "command": command,
            "returncode": None,
            "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def summarize_plugin_inventory(raw_stdout: str) -> dict:
    try:
        payload = json.loads(raw_stdout)
    except json.JSONDecodeError:
        return {"valid_json": False, "installed_count": None, "available_count": None}

    installed = payload.get("installed", [])
    available = payload.get("available", [])
    enabled = [p for p in installed if p.get("enabled") is True]
    return {
        "valid_json": True,
        "installed_count": len(installed),
        "enabled_count": len(enabled),
        "available_count": len(available),
        "enabled_plugins_sample": [p.get("pluginId") for p in enabled[:20]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Hermes/Codex runtime readiness")
    parser.add_argument("--timeout", type=int, default=12, help="Per-command timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    args = parser.parse_args()

    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    checks = {}
    for name, command in COMMANDS.items():
        checks[name] = run_command(
            command,
            args.timeout,
            truncate_stdout=(name != "codex_plugin_inventory"),
        )
        if name == "codex_plugin_inventory" and checks[name].get("stdout"):
            checks[name]["summary"] = summarize_plugin_inventory(checks[name]["stdout"])
            checks[name]["stdout"] = "<suppressed: plugin inventory summarized>"

        text = f"{checks[name].get('stdout', '')}\n{checks[name].get('stderr', '')}".lower()
        if name in KEYWORDS:
            checks[name]["keyword_presence"] = {
                keyword: keyword.lower() in text for keyword in KEYWORDS[name]
            }

    ready = {
        "hermes_available": bool(checks["hermes_path"].get("available")),
        "codex_available": bool(checks["codex_help"].get("available")),
        "codex_app_server_command_present": checks["codex_help"].get("available")
        and "app-server" in checks["codex_help"].get("stdout", ""),
        "codex_plugin_inventory_json": checks["codex_plugin_inventory"].get("summary", {}).get("valid_json") is True,
        "hermes_kanban_command_present": "kanban" in checks["hermes_path"].get("stdout", ""),
        "hermes_cron_command_present": "cron" in checks["hermes_path"].get("stdout", ""),
    }
    ready["preferred_runtime_ready"] = all(
        [
            ready["hermes_available"],
            ready["codex_available"],
            ready["codex_app_server_command_present"],
            ready["hermes_kanban_command_present"],
            ready["hermes_cron_command_present"],
        ]
    )

    report = {
        "generated_at": started,
        "project_root": str(PROJECT_ROOT),
        "ready": ready,
        "checks": checks,
        "next_action": "Use /codex-runtime codex_app_server if preferred_runtime_ready is true; otherwise inspect the failed checks.",
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Report: {OUTPUT_PATH}")
        for key, value in ready.items():
            print(f"{key}: {value}")
    return 0 if ready["preferred_runtime_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
