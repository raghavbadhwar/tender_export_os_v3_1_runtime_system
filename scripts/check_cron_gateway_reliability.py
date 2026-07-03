#!/usr/bin/env python3
"""Read-only Hermes cron and gateway reliability check."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CRON = PROJECT_ROOT / "config" / "hermes_cron.yaml"
RUN_LOG = PROJECT_ROOT / "data" / "agent_run_log.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "cron_gateway"

LOCAL_ONLY_NOTE = (
    "Cron output visible in a local TUI/session is local-only unless the run is delivered "
    "through a gateway-connected platform such as the configured owner gateway."
)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ModuleNotFoundError:
        data: dict[str, Any] = {"jobs": []}
        current_job: dict[str, Any] | None = None
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.rstrip()
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("- id:"):
                current_job = {"id": stripped.partition(":")[2].strip().strip('"')}
                data["jobs"].append(current_job)
                continue
            if current_job is not None and line.startswith("    ") and ":" in stripped:
                key, _, value = stripped.partition(":")
                current_job[key.strip()] = value.strip().strip('"')
            elif not line.startswith(" ") and ":" in stripped:
                key, _, value = stripped.partition(":")
                if key.strip() == "jobs" and not value.strip():
                    data.setdefault("jobs", [])
                else:
                    data[key.strip()] = value.strip().strip('"')
        return data


def load_run_log(path: Path = RUN_LOG) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def parse_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def visible_cron_paths(default_path: Path, profile_globs: list[str]) -> list[Path]:
    paths = [default_path] if default_path.exists() else []
    for pattern in profile_globs:
        for match in glob.glob(os.path.expanduser(pattern)):
            path = Path(match)
            if path.exists() and path not in paths:
                paths.append(path)
    return paths


def duplicate_jobs(configs: list[tuple[Path, dict[str, Any]]]) -> list[dict[str, Any]]:
    seen: dict[str, list[str]] = {}
    for path, config in configs:
        for job in config.get("jobs", []) or []:
            job_id = str(job.get("id", "")).strip()
            if job_id:
                seen.setdefault(job_id, []).append(display_path(path))
    return [
        {"job_id": job_id, "profiles": profiles}
        for job_id, profiles in sorted(seen.items())
        if len(profiles) > 1
    ]


def stale_run_findings(config: dict[str, Any], run_rows: list[dict[str, str]], today: dt.date) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not run_rows:
        return findings
    latest_success = max((parse_date(row.get("run_date", "")) for row in run_rows if row.get("status") == "SUCCESS"), default=None)
    for job in config.get("jobs", []) or []:
        if job.get("enabled") is False:
            continue
        cadence = str(job.get("cadence", "")).lower()
        if "daily" not in cadence and "* * *" not in cadence:
            continue
        if latest_success is None:
            findings.append({"job_id": job.get("id", ""), "status": "NO_SUCCESS_RECORDS", "detail": "run log exists but has no SUCCESS rows"})
        elif (today - latest_success).days > 1:
            findings.append(
                {
                    "job_id": job.get("id", ""),
                    "status": "STALE_SUCCESS_RECORDS",
                    "detail": f"latest SUCCESS row is {latest_success.isoformat()}",
                }
            )
    return findings


def run_hermes_cron_status(
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Return parsed `hermes cron status` output without mutating scheduler state."""
    hermes_path = shutil.which("hermes")
    if not hermes_path and runner is subprocess.run:
        return {"available": False, "raw_output": "", "gateway_running": None, "active_jobs": None, "next_run": ""}
    command_path = hermes_path or "hermes"
    try:
        completed = runner(
            [command_path, "cron", "status"],
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive for local CLI failures
        return {"available": True, "raw_output": str(exc), "gateway_running": None, "active_jobs": None, "next_run": ""}
    raw = "\n".join(part for part in [completed.stdout, completed.stderr] if part).strip()
    lowered = raw.lower()
    active_match = re.search(r"(\d+)\s+active job", raw)
    next_run_match = re.search(r"Next run:\s*([^\n]+)", raw)
    gateway_not_running = "gateway is not running" in lowered or "cron jobs will not fire" in lowered
    gateway_running = False if gateway_not_running else (True if "gateway" in lowered and "not running" not in lowered else None)
    return {
        "available": True,
        "returncode": completed.returncode,
        "raw_output": raw,
        "gateway_running": gateway_running,
        "active_jobs": int(active_match.group(1)) if active_match else None,
        "next_run": next_run_match.group(1).strip() if next_run_match else "",
    }


def build_report(
    *,
    cron_paths: list[Path] | None = None,
    run_rows: list[dict[str, str]] | None = None,
    now: dt.datetime | None = None,
    cron_status: dict[str, Any] | None = None,
    cron_status_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    now = now or dt.datetime.now(dt.timezone.utc)
    cron_paths = cron_paths or visible_cron_paths(DEFAULT_CRON, [])
    configs = [(path, load_yaml(path)) for path in cron_paths if path.exists()]
    primary = configs[0][1] if configs else {}
    run_rows = load_run_log() if run_rows is None else run_rows
    duplicates = duplicate_jobs(configs)
    stale = stale_run_findings(primary, run_rows, now.date()) if configs else []
    hermes_cli = shutil.which("hermes")
    owner_gateway = str(primary.get("owner_gateway", "") or "")
    gateway_connected = bool(os.environ.get("HERMES_GATEWAY_URL") or os.environ.get("TELEGRAM_BOT_TOKEN"))
    cron_status = cron_status if cron_status is not None else run_hermes_cron_status(cron_status_runner)

    findings: list[dict[str, str]] = []
    if not configs:
        findings.append({"severity": "BLOCKER", "code": "CRON_CONFIG_MISSING", "detail": "config/hermes_cron.yaml not visible"})
    if not hermes_cli:
        findings.append({"severity": "WARN", "code": "HERMES_CLI_NOT_FOUND", "detail": "Hermes CLI not found on PATH; scheduler may still exist elsewhere"})
    if cron_status.get("gateway_running") is False:
        detail = "hermes cron status reports gateway is not running; cron jobs will not fire"
        if cron_status.get("active_jobs") is not None:
            detail += f"; active_jobs={cron_status['active_jobs']}"
        if cron_status.get("next_run"):
            detail += f"; next_run={cron_status['next_run']}"
        findings.append({"severity": "BLOCKER", "code": "GATEWAY_NOT_RUNNING", "detail": detail})
    elif owner_gateway and not gateway_connected:
        findings.append({"severity": "WARN", "code": "GATEWAY_CONNECTION_NOT_CONFIRMED", "detail": f"owner_gateway={owner_gateway}; no gateway env marker visible"})
    for item in duplicates:
        findings.append({"severity": "WARN", "code": "DUPLICATE_JOB_ID", "detail": f"{item['job_id']} in {', '.join(item['profiles'])}"})
    for item in stale:
        findings.append({"severity": "WARN", "code": item["status"], "detail": f"{item['job_id']}: {item['detail']}"})

    return {
        "generated_at": now.replace(microsecond=0).isoformat(),
        "cron_profiles_checked": [display_path(path) for path in cron_paths],
        "owner_gateway": owner_gateway,
        "hermes_cli_visible": bool(hermes_cli),
        "gateway_connection_confirmed": gateway_connected,
        "hermes_cron_status": cron_status,
        "duplicate_jobs": duplicates,
        "stale_or_missed_runs": stale,
        "findings": findings,
        "status": "PASS" if not any(item["severity"] == "BLOCKER" for item in findings) else "BLOCKED",
        "tui_delivery_note": LOCAL_ONLY_NOTE,
        "safety_note": "Read-only reliability check. No cron creation, credential use, sends, uploads, submissions, or external actions.",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Cron Gateway Reliability Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Status: **{report['status']}**",
        f"- Hermes CLI visible: {report['hermes_cli_visible']}",
        f"- Gateway connection confirmed: {report['gateway_connection_confirmed']}",
        f"- Hermes cron gateway running: {report.get('hermes_cron_status', {}).get('gateway_running')}",
        f"- Active cron jobs: {report.get('hermes_cron_status', {}).get('active_jobs')}",
        f"- Next cron run: {report.get('hermes_cron_status', {}).get('next_run') or 'unknown'}",
        f"- Profiles checked: `{', '.join(report['cron_profiles_checked'])}`",
        "",
        report["tui_delivery_note"],
        "",
        report["safety_note"],
        "",
        "## Findings",
        "",
    ]
    if not report["findings"]:
        lines.append("- None")
    for finding in report["findings"]:
        lines.append(f"- {finding['severity']} {finding['code']}: {finding['detail']}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Hermes cron/gateway reliability without side effects")
    parser.add_argument("--cron", default=str(DEFAULT_CRON))
    parser.add_argument("--profile-glob", action="append", default=[], help="Optional visible cron profile glob to inspect")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cron = Path(args.cron)
    if not cron.is_absolute():
        cron = PROJECT_ROOT / cron
    paths = visible_cron_paths(cron, args.profile_glob)
    report = build_report(cron_paths=paths)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"cron_gateway_reliability_{stamp}.json"
    md_path = output_dir / f"cron_gateway_reliability_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, report)
    payload = {"status": report["status"], "json": display_path(json_path), "markdown": display_path(md_path)}
    print(json.dumps(payload, indent=2) if args.json else f"Cron gateway reliability {report['status']}: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
