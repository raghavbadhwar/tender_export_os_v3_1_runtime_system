from __future__ import annotations

from pathlib import Path

from scripts.validate_live_cron_installation import build_report


def config() -> dict:
    return {
        "jobs": [
            {
                "id": "morning_review",
                "cadence": "45 8 * * *",
                "hermes_name": "Morning Review",
                "hermes_script": "teos_morning_review.py",
            },
            {"id": "manual_research", "cadence": "owner-approved"},
        ]
    }


def live_job(*, schedule: str = "45 8 * * *") -> dict:
    return {
        "jobs": [
            {
                "id": "live-1",
                "name": "Morning Review",
                "script": "teos_morning_review.py",
                "enabled": True,
                "no_agent": True,
                "workdir": str(Path(__file__).resolve().parents[1]),
                "schedule": {"expr": schedule},
                "last_status": "ok",
            }
        ]
    }


def test_live_cron_installation_passes_when_desired_job_is_installed(tmp_path: Path) -> None:
    (tmp_path / "teos_morning_review.py").write_text("# wrapper\n", encoding="utf-8")
    report = build_report(config(), live_job(), scripts_dir=tmp_path)

    assert report["status"] == "PASS"
    assert report["installed_job_count"] == 1


def test_live_cron_installation_flags_missing_job_and_wrapper(tmp_path: Path) -> None:
    report = build_report(config(), {"jobs": []}, scripts_dir=tmp_path)

    assert report["status"] == "BLOCKED"
    assert {item["code"] for item in report["findings"]} == {"CRON_WRAPPER_MISSING", "LIVE_CRON_JOB_MISSING"}


def test_live_cron_installation_flags_schedule_mismatch(tmp_path: Path) -> None:
    (tmp_path / "teos_morning_review.py").write_text("# wrapper\n", encoding="utf-8")
    report = build_report(config(), live_job(schedule="0 8 * * *"), scripts_dir=tmp_path)

    assert report["status"] == "BLOCKED"
    assert report["findings"][0]["code"] == "LIVE_CRON_JOB_MISMATCH"
