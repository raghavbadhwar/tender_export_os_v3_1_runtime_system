from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import subprocess

import scripts.check_runtime_slos as runtime_slos
from scripts.check_runtime_slos import (
    build_exception_cards,
    check_age,
    check_json_age,
    check_operational_metrics,
    check_scheduler,
    pass_fail,
    run_checks,
)


def test_check_age_fails_when_no_matching_artifact() -> None:
    result = check_age("missing", "outputs/no-such-file-*.json", 1)

    assert result["status"] == "FAIL"
    assert result["path"] == ""
    assert result["age_hours"] is None


def test_check_json_age_fails_when_fresh_report_status_is_not_allowed(
    tmp_path: Path, monkeypatch
) -> None:
    report = tmp_path / "report.json"
    report.write_text('{"status": "FAIL"}\n', encoding="utf-8")
    monkeypatch.setattr(runtime_slos, "latest_match", lambda _: report)
    monkeypatch.setattr(runtime_slos, "file_age_hours", lambda _: 0.25)

    result = check_json_age("source_canary", "ignored.json", 24, {"PASS"})

    assert result["status"] == "FAIL"
    assert result["artifact_status"] == "FAIL"
    assert result["allowed_statuses"] == ["PASS"]


def test_scheduler_heartbeat_interprets_log_timestamp_in_local_timezone(monkeypatch) -> None:
    monkeypatch.setattr(
        runtime_slos,
        "load_csv",
        lambda _: [{"run_date": "2026-07-30", "run_time": "20:30:00"}],
    )

    result = check_scheduler(
        24,
        now=dt.datetime(2026, 7, 30, 15, 5, tzinfo=dt.timezone.utc),
        local_tz=dt.timezone(dt.timedelta(hours=5, minutes=30)),
    )

    assert result["status"] == "PASS"
    assert result["age_hours"] == 0.083


def test_exception_cards_are_written_only_for_failures(tmp_path: Path) -> None:
    checks = [
        pass_fail("good", True, {"detail": 1}),
        pass_fail("bad", False, {"detail": 2}),
    ]

    paths = build_exception_cards(checks, tmp_path)

    assert len(paths) == 1
    card = json.loads(Path(paths[0]).read_text(encoding="utf-8"))
    assert card["check"] == "bad"
    assert card["kanban_mutated"] is False
    assert "recommended_owner_action" in card


def test_runtime_slo_includes_production_readiness_gate_freshness(tmp_path: Path) -> None:
    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "gateway" in command:
            return subprocess.CompletedProcess(command, 0, stdout="gateway running", stderr="")
        if "kanban" in command:
            return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    report = run_checks(
        config={
            "thresholds": {"production_readiness_gate_max_age_hours": 24},
            "exception_routing": {"output_dir": str(tmp_path / "exception_cards")},
        },
        runner=runner,
    )

    names = {check["name"] for check in report["checks"]}
    readiness = next(check for check in report["checks"] if check["name"] == "production_readiness_gate_freshness")
    assert "production_readiness_gate_freshness" in names
    assert readiness["max_age_hours"] == 24.0


def test_runtime_slo_targets_the_configured_profile(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        stdout = "[]" if "kanban" in command else "gateway running"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    run_checks(
        config={
            "profile": "tender-export-os",
            "exception_routing": {"output_dir": str(tmp_path / "cards")},
        },
        runner=runner,
    )

    assert ["hermes", "-p", "tender-export-os", "gateway", "status"] in calls
    assert ["hermes", "-p", "tender-export-os", "kanban", "--board", "tender-export-os", "list", "--json"] in calls


def test_runtime_slo_main_returns_nonzero_for_failed_report(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "runtime_slo.yaml"
    config.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        runtime_slos,
        "run_checks",
        lambda **_: {"status": "FAIL", "exception_cards": ["failure.json"]},
    )
    monkeypatch.setattr(runtime_slos, "write_report", lambda report: str(tmp_path / "report.json"))

    assert runtime_slos.main(["--config", str(config)]) == 1


def test_operational_metrics_check_covers_latency_success_and_receipts(tmp_path: Path) -> None:
    metrics = tmp_path / "runtime_metrics.json"
    metrics.write_text(
        json.dumps(
            {
                "kanban_dispatch_p95_ms": 1200,
                "worker_success_rate_pct": 100,
                "mcp_cold_start_p95_ms": 800,
                "event_to_task_p95_ms": 1500,
                "owner_channel_delivery_age_hours": 0.5,
                "receipt_completeness_pct": 100,
            }
        ),
        encoding="utf-8",
    )
    checks = check_operational_metrics(
        metrics,
        {
            "kanban_dispatch_p95_ms": 300000,
            "worker_success_rate_min_pct": 100,
            "mcp_cold_start_p95_ms": 30000,
            "event_to_task_p95_ms": 300000,
            "owner_channel_delivery_max_age_hours": 24,
            "receipt_completeness_min_pct": 100,
        },
    )

    assert {check["name"] for check in checks} == {
        "kanban_dispatch_latency",
        "worker_success_rate",
        "mcp_cold_start",
        "event_to_task_latency",
        "owner_channel_delivery",
        "receipt_completeness",
    }
    assert all(check["status"] == "PASS" for check in checks)


def test_operational_metrics_fail_closed_when_evidence_is_missing(tmp_path: Path) -> None:
    checks = check_operational_metrics(tmp_path / "missing.json", {})

    assert len(checks) == 6
    assert all(check["status"] == "FAIL" for check in checks)
