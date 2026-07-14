from __future__ import annotations

import json
from pathlib import Path

import subprocess

from scripts.check_runtime_slos import build_exception_cards, check_age, check_operational_metrics, pass_fail, run_checks


def test_check_age_fails_when_no_matching_artifact() -> None:
    result = check_age("missing", "outputs/no-such-file-*.json", 1)

    assert result["status"] == "FAIL"
    assert result["path"] == ""
    assert result["age_hours"] is None


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
        if command[:2] == ["hermes", "gateway"]:
            return subprocess.CompletedProcess(command, 0, stdout="gateway running", stderr="")
        if command[:2] == ["hermes", "kanban"]:
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
