#!/usr/bin/env python3
"""Measure Tender OS MCP cold discovery and warm agent availability.

Cold trials use ``hermes mcp test`` which starts a fresh stdio server. Warm
trials start a normal one-shot Hermes agent and require it to call the bounded
``capability_status`` tool, returning a strict side-effect-free JSON canary.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "outputs" / "upgrade_baseline" / "mcp_discovery_reliability.json"
)
Runner = Callable[..., subprocess.CompletedProcess[str]]
TOOLS_RE = re.compile(r"Tools discovered:\s*(\d+)", re.I)

WARM_CANARY_PROMPT = """This is a side-effect-free Tender OS MCP availability canary.
Call the Tender OS `capability_status` MCP tool exactly once. Do not call any
other tool and do not perform or claim any external action. After the tool
returns, output ONLY this JSON object with JSON booleans and no markdown:
{"mcp_tools_visible": true, "status": "success", "external_actions": false}
If the tool is unavailable or fails, output the same object with
`mcp_tools_visible` false and `status` set to `failed`.
"""


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def parse_cold_result(
    completed: subprocess.CompletedProcess[str],
    *,
    expected_tools: int,
    duration_seconds: float,
) -> dict[str, Any]:
    output = f"{completed.stdout}\n{completed.stderr}"
    match = TOOLS_RE.search(output)
    tools = int(match.group(1)) if match else 0
    connected = "connected" in output.lower() and completed.returncode == 0
    return {
        "ok": connected and tools == expected_tools,
        "returncode": completed.returncode,
        "connected": connected,
        "tools_discovered": tools,
        "expected_tools": expected_tools,
        "duration_seconds": round(duration_seconds, 3),
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def extract_json_object(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    if start < 0:
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def parse_warm_result(
    completed: subprocess.CompletedProcess[str], *, duration_seconds: float
) -> dict[str, Any]:
    payload = extract_json_object(completed.stdout.strip())
    ok = bool(
        completed.returncode == 0
        and payload
        and payload.get("mcp_tools_visible") is True
        and payload.get("status") == "success"
        and payload.get("external_actions") is False
    )
    return {
        "ok": ok,
        "returncode": completed.returncode,
        "duration_seconds": round(duration_seconds, 3),
        "payload": payload,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def run_process(
    runner: Runner,
    command: list[str],
    *,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return runner(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def failed_trial(kind: str, exc: Exception, duration: float) -> dict[str, Any]:
    return {
        "ok": False,
        "kind": kind,
        "returncode": None,
        "duration_seconds": round(duration, 3),
        "error": f"{type(exc).__name__}: {exc}",
    }


def run_trials(
    *,
    profile: str,
    server: str,
    cold_trials: int,
    warm_trials: int,
    expected_tools: int,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    cold: list[dict[str, Any]] = []
    warm: list[dict[str, Any]] = []

    for index in range(1, cold_trials + 1):
        started = time.monotonic()
        try:
            completed = run_process(
                runner,
                ["hermes", "-p", profile, "mcp", "test", server],
                timeout=60,
            )
            result = parse_cold_result(
                completed,
                expected_tools=expected_tools,
                duration_seconds=time.monotonic() - started,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            result = failed_trial("cold", exc, time.monotonic() - started)
        result["trial"] = index
        cold.append(result)

    with tempfile.TemporaryDirectory(prefix="teos-mcp-canary-") as tmp:
        temp_root = Path(tmp)
        for index in range(1, warm_trials + 1):
            started = time.monotonic()
            usage_path = temp_root / f"usage-{index}.json"
            try:
                completed = run_process(
                    runner,
                    [
                        "hermes",
                        "-p",
                        profile,
                        "-z",
                        WARM_CANARY_PROMPT,
                        "--usage-file",
                        str(usage_path),
                    ],
                    timeout=180,
                )
                result = parse_warm_result(
                    completed, duration_seconds=time.monotonic() - started
                )
                if usage_path.is_file():
                    try:
                        usage = json.loads(usage_path.read_text(encoding="utf-8"))
                        result["usage"] = {
                            key: usage.get(key)
                            for key in ("model", "provider", "api_calls", "input_tokens", "output_tokens", "estimated_cost")
                            if key in usage
                        }
                    except (OSError, json.JSONDecodeError):
                        result["usage"] = {"error": "invalid usage file"}
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                result = failed_trial("warm", exc, time.monotonic() - started)
            result["trial"] = index
            warm.append(result)

    cold_passed = sum(bool(row.get("ok")) for row in cold)
    warm_passed = sum(bool(row.get("ok")) for row in warm)
    status = (
        "PASS"
        if cold_passed == cold_trials and warm_passed == warm_trials
        else "FAIL"
    )
    durations = [float(row.get("duration_seconds", 0)) for row in [*cold, *warm]]
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "status": status,
        "profile": profile,
        "server": server,
        "configured_discovery_timeout_seconds": 20,
        "expected_tools": expected_tools,
        "cold_trials": cold,
        "warm_trials": warm,
        "cold_passed": cold_passed,
        "warm_passed": warm_passed,
        "total_trials": cold_trials + warm_trials,
        "total_passed": cold_passed + warm_passed,
        "max_duration_seconds": max(durations, default=0),
        "mean_duration_seconds": round(sum(durations) / len(durations), 3) if durations else 0,
        "external_actions_executed": False,
        "safety_note": (
            "Cold trials perform MCP discovery. Warm trials call only the bounded read-only "
            "capability_status tool and request a strict no-external-action canary response."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="tender-export-os")
    parser.add_argument("--server", default="tender_os")
    parser.add_argument("--cold-trials", type=int, default=3)
    parser.add_argument("--warm-trials", type=int, default=10)
    parser.add_argument("--expected-tools", type=int, default=9)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    if args.cold_trials < 1 or args.warm_trials < 1 or args.expected_tools < 1:
        parser.error("trial counts and expected-tools must be positive")

    report = run_trials(
        profile=args.profile,
        server=args.server,
        cold_trials=args.cold_trials,
        warm_trials=args.warm_trials,
        expected_tools=args.expected_tools,
    )
    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(output, 0o600)
    print(
        json.dumps(
            {
                "status": report["status"],
                "cold": f"{report['cold_passed']}/{args.cold_trials}",
                "warm": f"{report['warm_passed']}/{args.warm_trials}",
                "max_duration_seconds": report["max_duration_seconds"],
                "output": str(output),
                "external_actions_executed": False,
            },
            indent=2,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
