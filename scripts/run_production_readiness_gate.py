#!/usr/bin/env python3
"""Run the safe production-readiness gate as one reproducible command."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "production_readiness"

Runner = Callable[..., subprocess.CompletedProcess[str]]

READINESS_COMMANDS: list[list[str]] = [
    ["scripts/validate_live_cron_installation.py", "--json"],
    ["scripts/check_cron_gateway_reliability.py", "--source-canary-window", "--json"],
    ["scripts/run_shadow_profile_probes.py", "--write-log", "--write-evaluations", "--json"],
    ["scripts/generate_shadow_pilot_report.py", "--json"],
    ["scripts/run_profile_behavioral_eval_queue.py", "--json"],
    ["scripts/evaluate_profile_production_routing.py", "--json"],
    ["scripts/revalidate_drive_knowledge_bus_sync.py", "--json"],
    ["scripts/validate_computer_use_readiness.py", "--json"],
    ["scripts/generate_production_pilot_report.py", "--prepare", "--json"],
    ["scripts/validate_register_schemas.py"],
    ["scripts/validate_profile_behavioral_gate.py", "--json"],
    ["scripts/validate_infrastructure_scale_gates.py", "--json"],
    ["scripts/check_runtime_slos.py", "--json"],
    ["scripts/validate_contact_form_lane.py", "--json"],
    ["scripts/validate_contact_form_connector_design.py", "--json"],
    ["scripts/generate_final_readiness_receipt.py", "--json"],
    ["scripts/generate_owner_action_packet.py", "--json"],
    ["scripts/audit_upgrade_plan_status.py", "--json"],
    ["scripts/generate_final_readiness_receipt.py", "--json"],
]

POST_SEAL_COMMANDS: list[list[str]] = [
    ["scripts/validate_live_cron_installation.py", "--json"],
    ["scripts/check_cron_gateway_reliability.py", "--source-canary-window", "--json"],
    ["scripts/generate_final_readiness_receipt.py", "--json"],
    ["scripts/generate_owner_action_packet.py", "--json"],
    ["scripts/audit_upgrade_plan_status.py", "--json"],
    ["scripts/generate_final_readiness_receipt.py", "--json"],
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_command(args: list[str], *, runner: Runner = subprocess.run, timeout: int = 300) -> dict[str, Any]:
    command = [sys.executable, *args]
    started = time.monotonic()
    try:
        completed = runner(
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
        return {
            "command": command,
            "command_text": " ".join(command),
            "returncode": 124,
            "ok": False,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": stdout[-2000:],
            "stderr_tail": (stderr + f"\nTimed out after {timeout}s")[-2000:],
            "json": {},
        }
    stdout = completed.stdout or ""
    parsed: dict[str, Any] = {}
    try:
        maybe = json.loads(stdout)
        if isinstance(maybe, dict):
            parsed = maybe
    except json.JSONDecodeError:
        parsed = {}
    return {
        "command": command,
        "command_text": " ".join(command),
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout_tail": stdout[-2000:],
        "stderr_tail": (completed.stderr or "")[-2000:],
        "json": parsed,
    }


def build_report(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    results = list(records)
    failures = [row for row in results if not row["ok"]]
    final_readiness = next(
        (
            row["json"]
            for row in reversed(results)
            if row["command_text"].find("generate_final_readiness_receipt.py") >= 0 and row.get("json")
        ),
        {},
    )
    owner_packet = next(
        (
            row["json"]
            for row in reversed(results)
            if row["command_text"].find("generate_owner_action_packet.py") >= 0 and row.get("json")
        ),
        {},
    )
    readiness_status = final_readiness.get("status") or "UNKNOWN"
    if failures:
        status = "FAIL"
    elif readiness_status == "BLOCKED":
        status = "BLOCKED"
    elif readiness_status in {"READY", "READY_FOR_OWNER_SIGNOFF"}:
        status = readiness_status
    else:
        status = "PASS"
    return {
        "schema_version": "production_readiness_gate.v1",
        "generated_at": now_iso(),
        "status": status,
        "command_count": len(results),
        "failure_count": len(failures),
        "readiness_status": readiness_status,
        "blocking_task_count": final_readiness.get("blocking_task_count", final_readiness.get("blocking_tasks", 0)),
        "blocking_task_ids": final_readiness.get("blocking_task_ids", []),
        "readiness_receipt": final_readiness.get("receipt"),
        "owner_action_packet": {
            "json": owner_packet.get("json"),
            "markdown": owner_packet.get("markdown"),
            "blocking_task_count": owner_packet.get("blocking_task_count"),
        },
        "results": results,
        "external_actions_executed": False,
        "production_routing_enabled": False,
        "safety_note": "Safe readiness gate only. It writes local receipts/log/evaluation telemetry but performs no sends, submissions, uploads, payments, DSC use, contacts, auth changes, or external commitments.",
    }


def write_report(report: dict[str, Any], output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"production_readiness_gate_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def rewrite_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_seal_results(report: dict[str, Any], seal_records: list[dict[str, Any]]) -> dict[str, Any]:
    seal_failures = [row for row in seal_records if not row["ok"]]
    final_readiness = next(
        (
            row["json"]
            for row in reversed(seal_records)
            if row["command_text"].find("generate_final_readiness_receipt.py") >= 0 and row.get("json")
        ),
        {},
    )
    owner_packet = next(
        (
            row["json"]
            for row in reversed(seal_records)
            if row["command_text"].find("generate_owner_action_packet.py") >= 0 and row.get("json")
        ),
        {},
    )
    report["sealed"] = not seal_failures
    report["seal_results"] = seal_records
    report["seal_failure_count"] = len(seal_failures)
    report["command_count"] = int(report.get("command_count") or 0) + len(seal_records)
    report["failure_count"] = int(report.get("failure_count") or 0) + len(seal_failures)
    if final_readiness:
        readiness_status = final_readiness.get("status") or report.get("readiness_status") or "UNKNOWN"
        report["readiness_status"] = readiness_status
        report["blocking_task_count"] = final_readiness.get("blocking_task_count", final_readiness.get("blocking_tasks", 0))
        report["blocking_task_ids"] = final_readiness.get("blocking_task_ids", [])
        report["readiness_receipt"] = final_readiness.get("receipt")
        if report["failure_count"]:
            report["status"] = "FAIL"
        elif readiness_status == "BLOCKED":
            report["status"] = "BLOCKED"
        elif readiness_status in {"READY", "READY_FOR_OWNER_SIGNOFF"}:
            report["status"] = readiness_status
    if owner_packet:
        report["owner_action_packet"] = {
            "json": owner_packet.get("json"),
            "markdown": owner_packet.get("markdown"),
            "blocking_task_count": owner_packet.get("blocking_task_count"),
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    records = [run_command(command) for command in READINESS_COMMANDS]
    report = build_report(records)
    path = write_report(report, Path(args.output_dir).expanduser())
    seal_records = [run_command(command) for command in POST_SEAL_COMMANDS]
    report["report_path"] = str(path)
    report = apply_seal_results(report, seal_records)
    rewrite_report(path, report)
    payload = {
        "status": report["status"],
        "command_count": report["command_count"],
        "failure_count": report["failure_count"],
        "seal_failure_count": report.get("seal_failure_count", 0),
        "readiness_status": report["readiness_status"],
        "sealed": report.get("sealed"),
        "report": str(path),
        "owner_action_packet": report["owner_action_packet"],
        "external_actions_executed": False,
        "production_routing_enabled": False,
    }
    print(json.dumps(payload, indent=2) if args.json else f"Production readiness gate {report['status']}: {path}")
    return 0 if report["status"] not in {"FAIL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
