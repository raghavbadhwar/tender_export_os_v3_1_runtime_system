import datetime as dt
import subprocess
from pathlib import Path

from scripts.check_cron_gateway_reliability import build_report, run_hermes_cron_status


def test_cron_gateway_reports_duplicate_visible_jobs(tmp_path: Path) -> None:
    cron1 = tmp_path / "a.yaml"
    cron2 = tmp_path / "b.yaml"
    body = """
owner_gateway: telegram
jobs:
  - id: daily_job
    cadence: "0 6 * * *"
"""
    cron1.write_text(body, encoding="utf-8")
    cron2.write_text(body, encoding="utf-8")

    report = build_report(
        cron_paths=[cron1, cron2],
        run_rows=[{"run_date": "2026-07-01", "status": "SUCCESS"}],
        now=dt.datetime(2026, 7, 3, tzinfo=dt.timezone.utc),
    )

    assert report["duplicate_jobs"][0]["job_id"] == "daily_job"
    assert any(item["code"] == "DUPLICATE_JOB_ID" for item in report["findings"])
    assert "local-only" in report["tui_delivery_note"]


def test_hermes_cron_status_gateway_not_running_is_blocker() -> None:
    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="✗ Gateway is not running — cron jobs will NOT fire\n\n  6 active job(s)\n  Next run: 2026-07-02T06:00:00+05:30\n",
            stderr="",
        )

    parsed = run_hermes_cron_status(runner=runner)
    report = build_report(
        cron_paths=[],
        run_rows=[],
        cron_status=parsed,
        now=dt.datetime(2026, 7, 3, tzinfo=dt.timezone.utc),
    )

    assert parsed["gateway_running"] is False
    assert parsed["active_jobs"] == 6
    assert report["status"] == "BLOCKED"
    assert any(item["code"] == "GATEWAY_NOT_RUNNING" for item in report["findings"])


def test_staleness_is_calculated_per_job_not_from_global_success(tmp_path: Path) -> None:
    cron = tmp_path / "cron.yaml"
    cron.write_text(
        """
owner_gateway: telegram
jobs:
  - id: morning_job
    cadence: "0 6 * * *"
    run_log_agent: morning_agent
  - id: evening_job
    cadence: "30 20 * * *"
    run_log_agent: evening_agent
""",
        encoding="utf-8",
    )
    report = build_report(
        cron_paths=[cron],
        run_rows=[
            {"run_date": "2026-07-03", "status": "SUCCESS", "agent_name": "morning_agent"},
            {"run_date": "2026-06-30", "status": "SUCCESS", "agent_name": "evening_agent"},
        ],
        cron_status={"gateway_running": True, "active_jobs": 2, "next_run": "soon"},
        now=dt.datetime(2026, 7, 3, tzinfo=dt.timezone.utc),
    )

    assert [item["job_id"] for item in report["stale_or_missed_runs"]] == ["evening_job"]


def test_latest_failed_enabled_job_blocks_reliability(tmp_path: Path) -> None:
    cron = tmp_path / "cron.yaml"
    cron.write_text(
        """
owner_gateway: local
jobs:
  - id: midday_radar
    cadence: "0 13 * * *"
    run_log_agent: midday_agent
""",
        encoding="utf-8",
    )
    report = build_report(
        cron_paths=[cron],
        run_rows=[
            {"run_date": "2026-07-29", "run_time": "13:00:00", "status": "SUCCESS", "agent_name": "midday_agent"},
            {"run_date": "2026-07-30", "run_time": "13:00:00", "status": "FAILURE", "agent_name": "midday_agent"},
        ],
        cron_status={"gateway_running": True, "active_jobs": 1, "next_run": "soon"},
        now=dt.datetime(2026, 7, 30, 14, tzinfo=dt.timezone.utc),
    )

    assert report["status"] == "BLOCKED"
    assert any(item["code"] == "LATEST_JOB_RUN_FAILED" for item in report["findings"])
