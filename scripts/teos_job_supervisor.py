#!/usr/bin/env python3
"""Run one internal Tender Export OS job with locking, receipts, and truthful status."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows development fallback
    fcntl = None  # type: ignore[assignment]

try:
    import yaml
except ImportError:  # pragma: no cover - reported by CLI preflight
    yaml = None

try:
    from event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover - package import path used by pytest
    from scripts.event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "hermes_cron.yaml"
RUN_LOG_HEADERS = [
    "run_id", "run_date", "run_time", "agent_name", "trigger_type", "cases_processed",
    "cases_created", "cases_rejected", "cases_updated", "sources_checked", "sources_failed",
    "actions_taken", "approval_cards_created", "receipts_created", "errors", "warnings",
    "runtime_seconds", "status", "notes",
]
SHELL_OPERATORS = {"&&", "||", ";", "|", ">", ">>", "<", "2>", "&"}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def build_command(command_text: str, project_root: Path = PROJECT_ROOT) -> list[str]:
    if not command_text.strip():
        raise ValueError("job task_command is empty")
    if "\n" in command_text or any(operator in shlex.split(command_text) for operator in SHELL_OPERATORS):
        raise ValueError("shell operators are not allowed in supervised job commands")
    tokens = shlex.split(command_text)
    if len(tokens) < 2 or Path(tokens[0]).name not in {"python", "python3"}:
        raise ValueError("supervised jobs must invoke one Python script")

    script_path = (project_root / tokens[1]).resolve()
    scripts_root = (project_root / "scripts").resolve()
    try:
        script_path.relative_to(scripts_root)
    except ValueError as exc:
        raise ValueError("supervised job script must stay inside the project scripts directory") from exc
    if script_path.name == Path(__file__).name:
        raise ValueError("job supervisor cannot recursively invoke itself")
    if script_path.suffix != ".py" or not script_path.is_file():
        raise ValueError(f"supervised job script does not exist: {script_path}")

    repo_python = project_root / ".venv" / "bin" / "python"
    python = str(repo_python) if repo_python.is_file() else sys.executable
    return [python, relative(script_path, project_root), *tokens[2:]]


def build_project_environment(project_root: Path, job_id: str, run_id: str) -> dict[str, str]:
    """Build a deterministic project-local environment for a supervised job."""
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)

    venv_dir = project_root / ".venv"
    venv_bin = venv_dir / "bin"
    if venv_dir.is_dir():
        environment["VIRTUAL_ENV"] = str(venv_dir)
        current_path = environment.get("PATH", "")
        environment["PATH"] = str(venv_bin) + (os.pathsep + current_path if current_path else "")
    else:
        environment.pop("VIRTUAL_ENV", None)

    environment.update(
        {
            "TEOS_JOB_ID": job_id,
            "TEOS_RUN_ID": run_id,
            "PYTHONUNBUFFERED": "1",
            "PYTHONNOUSERSITE": "1",
        }
    )
    return environment


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def append_run_log(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", newline="", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.seek(0, os.SEEK_END)
            write_header = handle.tell() == 0
            writer = csv.DictWriter(handle, fieldnames=RUN_LOG_HEADERS)
            if write_header:
                writer.writeheader()
            writer.writerow(
                {
                    "run_id": receipt["run_id"],
                    "run_date": receipt["started_at"][:10],
                    "run_time": receipt["started_at"][11:19],
                    "agent_name": "teos_job_supervisor",
                    "trigger_type": f"scheduled_job:{receipt['job_id']}",
                    "cases_processed": 0,
                    "cases_created": 0,
                    "cases_rejected": 0,
                    "cases_updated": 0,
                    "sources_checked": 0,
                    "sources_failed": 0,
                    "actions_taken": f"supervise:{receipt['job_id']}",
                    "approval_cards_created": 0,
                    "receipts_created": 1,
                    "errors": 0 if receipt["status"] == "SUCCESS" else 1,
                    "warnings": 0,
                    "runtime_seconds": receipt["runtime_seconds"],
                    "status": receipt["status"],
                    "notes": f"receipt={receipt['receipt_path']}; exit_code={receipt['exit_code']}",
                }
            )
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def current_revision(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_root, text=True, capture_output=True, check=False, timeout=10
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def execute_job(
    job: dict[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
    events_file: Path | None = None,
    run_log_file: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    now: Callable[[], dt.datetime] = utc_now,
    revision: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    job_id = str(job.get("id", "") or "").strip()
    if not job_id:
        raise ValueError("job id is required")
    command = build_command(str(job.get("task_command") or job.get("command") or ""), project_root)
    started = now().astimezone(dt.timezone.utc).replace(microsecond=0)
    run_id = run_id or f"JOB-{started.strftime('%Y%m%dT%H%M%SZ')}-{job_id}-{uuid.uuid4().hex[:6]}"
    receipt_path = project_root / "receipts" / "job_runs" / job_id / f"{run_id}.json"
    if receipt_path.is_file():
        return json.loads(receipt_path.read_text(encoding="utf-8"))

    lock_path = project_root / "outputs" / "locks" / "jobs" / f"{job_id}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    events_file = events_file or project_root / "data" / "events.jsonl"
    run_log_file = run_log_file or project_root / "data" / "agent_run_log.csv"
    timeout_seconds = max(1, int(job.get("max_runtime_minutes") or 30) * 60)

    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        if fcntl is not None:
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError(f"job already running: {job_id}") from exc
        try:
            start_event = append_event(
                "job.started",
                "teos_job_supervisor",
                object_type="job_run",
                object_id=run_id,
                payload={"run_id": run_id, "job_id": job_id, "command": command, "started_at": started.isoformat()},
                citations=["config/hermes_cron.yaml"],
                correlation_id=run_id,
                idempotency_key=f"job:{run_id}:started",
                events_file=events_file,
            )

            environment = build_project_environment(project_root, job_id, run_id)
            timed_out = False
            try:
                completed = runner(
                    command,
                    cwd=project_root,
                    text=True,
                    capture_output=True,
                    timeout=timeout_seconds,
                    check=False,
                    env=environment,
                )
                exit_code = int(completed.returncode)
                stdout = completed.stdout or ""
                stderr = completed.stderr or ""
            except subprocess.TimeoutExpired as exc:
                exit_code = 124
                timed_out = True
                stdout = exc.stdout if isinstance(exc.stdout, str) else ""
                stderr = exc.stderr if isinstance(exc.stderr, str) else f"Timed out after {timeout_seconds}s"

            completed_at = now().astimezone(dt.timezone.utc).replace(microsecond=0)
            status = "SUCCESS" if exit_code == 0 else "FAILURE"
            receipt = {
                "run_id": run_id,
                "job_id": job_id,
                "status": status,
                "exit_code": exit_code,
                "timed_out": timed_out,
                "started_at": started.isoformat(),
                "completed_at": completed_at.isoformat(),
                "runtime_seconds": max(0, int((completed_at - started).total_seconds())),
                "command": command,
                "revision": revision or current_revision(project_root),
                "stdout_tail": stdout[-8000:],
                "stderr_tail": stderr[-8000:],
                "receipt_path": relative(receipt_path, project_root),
                "external_business_actions": False,
                "approval_boundary": "Internal supervised execution only; external business actions remain separately approval-gated.",
            }
            atomic_write_json(receipt_path, receipt)
            append_event(
                "job.completed" if status == "SUCCESS" else "job.failed",
                "teos_job_supervisor",
                object_type="job_run",
                object_id=run_id,
                payload={
                    "run_id": run_id,
                    "job_id": job_id,
                    "receipt_path": receipt["receipt_path"],
                    "exit_code": exit_code,
                    "status": status,
                },
                citations=[receipt["receipt_path"]],
                correlation_id=run_id,
                causation_id=start_event["event_id"],
                idempotency_key=f"job:{run_id}:finished",
                events_file=events_file,
            )
            append_run_log(run_log_file, receipt)
            return receipt
        finally:
            if fcntl is not None:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def load_config(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required; run this through the repository virtual environment")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("cron config must be a mapping")
    return payload


def find_job(config: dict[str, Any], job_id: str) -> dict[str, Any]:
    for job in config.get("jobs", []) or []:
        if str(job.get("id", "")) == job_id:
            return job
    raise KeyError(f"unknown job id: {job_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-disabled", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    job = find_job(load_config(config_path), args.job_id)
    if job.get("enabled") is False and not args.allow_disabled:
        print(f"Job is disabled: {args.job_id}", file=sys.stderr)
        return 2
    if args.dry_run:
        payload = {"job_id": args.job_id, "command": build_command(str(job.get("task_command") or job.get("command") or "")), "dry_run": True}
        print(json.dumps(payload, indent=2) if args.json else f"Validated supervised job: {args.job_id}")
        return 0

    receipt = execute_job(job)
    print(json.dumps(receipt, indent=2) if args.json else f"{receipt['job_id']}: {receipt['status']} ({receipt['receipt_path']})")
    return int(receipt["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
