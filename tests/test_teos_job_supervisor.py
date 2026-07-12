import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.teos_job_supervisor import build_command, execute_job, find_job, load_config


def project_fixture(tmp_path: Path) -> Path:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "receipts" / "job_runs").mkdir(parents=True)
    (tmp_path / "outputs" / "locks" / "jobs").mkdir(parents=True)
    (tmp_path / "scripts" / "safe_task.py").write_text("print('safe task')\n", encoding="utf-8")
    return tmp_path


def test_build_command_uses_repo_interpreter_and_rejects_shell_chaining(tmp_path: Path) -> None:
    project = project_fixture(tmp_path)
    command = build_command("python3 scripts/safe_task.py --json", project)
    assert command[0] == sys.executable
    assert command[1:] == ["scripts/safe_task.py", "--json"]

    with pytest.raises(ValueError, match="shell operators"):
        build_command("python3 scripts/safe_task.py && echo unsafe", project)


def test_build_command_rejects_scripts_outside_project_scripts(tmp_path: Path) -> None:
    project = project_fixture(tmp_path)
    with pytest.raises(ValueError, match="scripts directory"):
        build_command("python3 ../outside.py", project)


def test_execute_job_writes_receipt_events_and_truthful_status(tmp_path: Path) -> None:
    project = project_fixture(tmp_path)
    events = project / "data" / "events.jsonl"
    run_log = project / "data" / "agent_run_log.csv"

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 7, stdout="partial output", stderr="task failed")

    result = execute_job(
        {"id": "safe_job", "task_command": "python3 scripts/safe_task.py", "max_runtime_minutes": 1},
        project_root=project,
        events_file=events,
        run_log_file=run_log,
        runner=runner,
        now=lambda: dt.datetime(2026, 7, 12, 6, 0, tzinfo=dt.timezone.utc),
        revision="abc123",
    )

    assert result["status"] == "FAILURE"
    assert result["exit_code"] == 7
    receipt = json.loads((project / result["receipt_path"]).read_text(encoding="utf-8"))
    assert receipt["revision"] == "abc123"
    assert receipt["external_business_actions"] is False
    event_rows = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
    assert [row["event_type"] for row in event_rows] == ["job.started", "job.failed"]
    assert event_rows[1]["causation_id"] == event_rows[0]["event_id"]
    assert "FAILURE" in run_log.read_text(encoding="utf-8")


def test_execute_job_success_is_idempotent_for_same_run_id(tmp_path: Path) -> None:
    project = project_fixture(tmp_path)
    events = project / "data" / "events.jsonl"

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    kwargs = {
        "project_root": project,
        "events_file": events,
        "run_log_file": project / "data" / "agent_run_log.csv",
        "runner": runner,
        "now": lambda: dt.datetime(2026, 7, 12, 6, 0, tzinfo=dt.timezone.utc),
        "revision": "abc123",
        "run_id": "JOB-20260712-SAFE",
    }
    first = execute_job({"id": "safe_job", "task_command": "python3 scripts/safe_task.py"}, **kwargs)
    second = execute_job({"id": "safe_job", "task_command": "python3 scripts/safe_task.py"}, **kwargs)

    assert first["receipt_path"] == second["receipt_path"]
    assert len(events.read_text(encoding="utf-8").splitlines()) == 2


def test_enabled_hermes_jobs_are_supervised_and_have_valid_tasks() -> None:
    project = Path(__file__).resolve().parents[1]
    config = load_config(project / "config" / "hermes_cron.yaml")
    jobs = config["jobs"]

    for job in jobs:
        if job.get("enabled") is False or job.get("cadence") == "owner-approved":
            continue
        assert job["command"] == (
            f".venv/bin/python scripts/teos_job_supervisor.py --job-id {job['id']}"
        )
        assert job["run_log_agent"] == "teos_job_supervisor"
        build_command(job["task_command"], project)

    assert find_job(config, "supplier_followup_review")["task_command"] == (
        "python3 scripts/generate_intraday_monitor.py"
    )
