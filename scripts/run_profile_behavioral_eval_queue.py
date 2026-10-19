#!/usr/bin/env python3
"""Plan or execute bounded one-profile behavioral evaluations for routing readiness."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_hermes_behavioral_contracts import profile_scope_names  # noqa: E402
from scripts.evaluate_profile_production_routing import behavioral_reports_by_profile, load_yaml  # noqa: E402


DEFAULT_SPEC = PROJECT_ROOT / "config" / "hermes_behavioral_eval.yaml"
DEFAULT_ROUTING_CONFIG = PROJECT_ROOT / "config" / "profile_production_routing_gate.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profile_behavioral_eval_queue"
Runner = Callable[..., subprocess.CompletedProcess[str]]


def build_queue(*, spec: dict[str, Any], routing_config: dict[str, Any]) -> dict[str, Any]:
    profiles = profile_scope_names(spec, base_dir=PROJECT_ROOT)
    behavioral_reports = behavioral_reports_by_profile(str(routing_config.get("behavioral_eval_report_glob") or ""))
    rows: list[dict[str, Any]] = []
    for profile in profiles:
        report = behavioral_reports.get(profile) or {}
        passed = report.get("status") == "PASS" and float(report.get("case_pass_rate") or 0) >= 1.0
        rows.append(
            {
                "profile": profile,
                "status": "PASS" if passed else ("NEEDS_EVAL" if not report else "NEEDS_RERUN"),
                "latest_report": report.get("path", ""),
                "latest_report_status": report.get("status", ""),
                "latest_case_pass_rate": report.get("case_pass_rate"),
                "command": f".venv/bin/python scripts/evaluate_hermes_behavioral_contracts.py --profile {profile} --json",
            }
        )
    pending = [row for row in rows if row["status"] != "PASS"]
    return {
        "schema_version": "profile_behavioral_eval_queue.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS" if not pending else "PENDING",
        "profile_count": len(rows),
        "passed_profile_count": len(rows) - len(pending),
        "pending_profile_count": len(pending),
        "next_profile": pending[0]["profile"] if pending else "",
        "profiles": rows,
        "external_actions_executed": False,
        "safety_note": "Queue planning only unless --execute is used. Evaluations use the clarify toolset and do not authorize live work.",
    }


def run_next_profile(queue: dict[str, Any], *, runner: Runner = subprocess.run, timeout: int = 240) -> dict[str, Any]:
    profile = str(queue.get("next_profile") or "").strip()
    if not profile:
        return {"executed": False, "status": "NO_PENDING_PROFILE", "profile": ""}
    command = [
        sys.executable,
        "scripts/evaluate_hermes_behavioral_contracts.py",
        "--profile",
        profile,
        "--json",
    ]
    try:
        completed = runner(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        completed = subprocess.CompletedProcess(command, 124, stdout=exc.stdout or "", stderr=exc.stderr or "")
        timed_out = True
    return {
        "executed": True,
        "profile": profile,
        "command": command,
        "returncode": completed.returncode,
        "timed_out": timed_out,
        "stdout_tail": str(completed.stdout)[-4000:],
        "stderr_tail": str(completed.stderr)[-4000:],
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def write_report(report: dict[str, Any], output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"profile_behavioral_eval_queue_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", default=str(DEFAULT_SPEC))
    parser.add_argument("--routing-config", default=str(DEFAULT_ROUTING_CONFIG))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--execute", action="store_true", help="Run the next pending profile evaluation once.")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    spec_path = Path(args.spec).expanduser()
    if not spec_path.is_absolute():
        spec_path = PROJECT_ROOT / spec_path
    routing_path = Path(args.routing_config).expanduser()
    if not routing_path.is_absolute():
        routing_path = PROJECT_ROOT / routing_path
    queue = build_queue(spec=load_yaml(spec_path), routing_config=load_yaml(routing_path))
    if args.execute:
        queue["execution"] = run_next_profile(queue, timeout=args.timeout)
    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    path = write_report(queue, output_dir)
    payload = {
        "status": queue["status"],
        "passed_profile_count": queue["passed_profile_count"],
        "pending_profile_count": queue["pending_profile_count"],
        "next_profile": queue["next_profile"],
        "report": str(path),
        "executed": bool(queue.get("execution")),
    }
    print(json.dumps(payload, indent=2) if args.json else f"Profile eval queue {queue['status']}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
