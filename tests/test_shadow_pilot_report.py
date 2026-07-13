from __future__ import annotations

import datetime as dt

from scripts.generate_shadow_pilot_report import build_report, render_html, summarize_daily_profile_telemetry, summarize_evaluations, summarize_run_log


def _config() -> dict:
    return {
        "mode": "SHADOW_ONLY",
        "duration_days": 14,
        "baseline_days": 14,
        "allowed_internal_actions": ["read", "research", "draft"],
        "prohibited_external_actions": ["email_send", "portal_submit", "payment"],
        "success_metrics": {
            "task_success_rate": {"minimum_shadow_target": 90},
            "evidence_completeness_pct": {"minimum_shadow_target": 95},
            "policy_violation_count": {"maximum_shadow_target": 0},
        },
    }


def test_run_log_summary_tracks_success_latency_and_external_markers() -> None:
    rows = [
        {
            "run_id": "RUN-1",
            "status": "SUCCESS",
            "runtime_seconds": "10",
            "cases_processed": "2",
            "cases_created": "1",
            "cases_updated": "1",
            "errors": "0",
            "warnings": "1",
            "actions_taken": "internal_research",
            "agent_name": "gov-tender-intelligence",
        },
        {
            "run_id": "RUN-2",
            "status": "FAIL",
            "runtime_seconds": "30",
            "cases_processed": "0",
            "cases_created": "0",
            "cases_updated": "0",
            "errors": "1",
            "warnings": "0",
            "actions_taken": "send buyer email",
            "agent_name": "relationship-ops",
        },
    ]

    summary = summarize_run_log(rows)

    assert summary["run_count"] == 2
    assert summary["task_success_rate"] == 50.0
    assert summary["median_task_latency_seconds"] == 20.0
    assert summary["external_action_marker_count"] == 1
    assert summary["external_action_marker_run_ids"] == ["RUN-2"]


def test_success_with_warnings_counts_as_successful_run() -> None:
    summary = summarize_run_log(
        [
            {"run_id": "RUN-1", "status": "SUCCESS_WITH_WARNINGS", "warnings": "2"},
            {"run_id": "RUN-2", "status": "FAILURE", "errors": "1"},
        ]
    )

    assert summary["success_count"] == 1
    assert summary["task_success_rate"] == 50.0


def test_run_log_external_marker_is_word_aware() -> None:
    rows = [
        {
            "run_id": "RUN-SAFE-NEGATED",
            "status": "SUCCESS",
            "actions_taken": "local_report",
            "notes": "no supplier/buyer/submission/payment/DSC/final classification/origin/price action",
            "agent_name": "external_task_intake",
        },
        {
            "run_id": "RUN-ACTUAL",
            "status": "SUCCESS",
            "actions_taken": "submit portal form",
            "notes": "",
            "agent_name": "relationship-ops",
        },
    ]

    summary = summarize_run_log(rows)

    assert summary["external_action_marker_count"] == 1
    assert summary["external_action_marker_run_ids"] == ["RUN-ACTUAL"]


def test_evaluation_summary_tracks_policy_evidence_cost_and_latency() -> None:
    rows = [
        {
            "status": "PASS",
            "evidence_completeness_pct": "100",
            "policy_compliance": "PASS",
            "latency_ms": "200",
            "cost_usd": "0.02",
        },
        {
            "evaluation_id": "EVAL-2",
            "status": "FAIL",
            "evidence_completeness_pct": "80",
            "policy_compliance": "FAIL",
            "latency_ms": "100",
            "cost_usd": "0.03",
        },
    ]

    summary = summarize_evaluations(rows)

    assert summary["evaluation_count"] == 2
    assert summary["evaluation_pass_rate"] == 50.0
    assert summary["average_evidence_completeness_pct"] == 90.0
    assert summary["policy_violation_count"] == 1
    assert summary["policy_violation_ids"] == ["EVAL-2"]
    assert summary["total_cost_usd"] == 0.05
    assert summary["median_model_latency_ms"] == 150.0


def test_shadow_pilot_report_blocks_external_markers_and_never_enables_production() -> None:
    end = dt.date(2026, 7, 14)
    report = build_report(
        config=_config(),
        end_date=end,
        days=14,
        run_log=[
            {
                "run_id": "RUN-1",
                "run_date": "2026-07-13",
                "status": "SUCCESS",
                "runtime_seconds": "60",
                "cases_processed": "1",
                "cases_created": "0",
                "cases_updated": "1",
                "errors": "0",
                "warnings": "0",
                "actions_taken": "send supplier request",
                "agent_name": "supplier-commercial",
            }
        ],
        evaluations=[],
        cases=[],
    )

    assert report["status"] == "BLOCKED"
    assert report["production_routing_enabled"] is False
    assert report["external_actions_authorized"] is False
    assert "run log contains external-action markers inside the shadow window" in report["blockers"]


def test_shadow_pilot_report_passes_internal_only_measured_window() -> None:
    end = dt.date(2026, 7, 14)
    report = build_report(
        config=_config(),
        end_date=end,
        days=14,
        run_log=[
            {
                "run_id": "RUN-1",
                "run_date": "2026-07-13",
                "status": "SUCCESS",
                "runtime_seconds": "60",
                "cases_processed": "1",
                "cases_created": "0",
                "cases_updated": "1",
                "errors": "0",
                "warnings": "0",
                "actions_taken": "internal_research",
                "agent_name": "gov-tender-intelligence",
            }
        ],
        evaluations=[
            {
                "evaluation_id": "EVAL-1",
                "evaluated_at": "2026-07-13T10:00:00+00:00",
                "status": "PASS",
                "evidence_completeness_pct": "100",
                "policy_compliance": "PASS",
                "latency_ms": "100",
                "cost_usd": "0.01",
            }
        ],
        cases=[
            {
                "case_id": "GOV-1",
                "created_at": "2026-07-13",
                "status": "WATCHLIST",
            }
        ],
    )

    assert report["status"] == "PASS"
    assert report["current"]["run_log"]["task_success_rate"] == 100.0
    assert report["current"]["evaluations"]["average_evidence_completeness_pct"] == 100.0
    assert report["current"]["cases"]["qualified_opportunity_count"] == 1


def test_explicit_shadow_pilot_start_excludes_historical_external_markers_and_stays_in_progress() -> None:
    end = dt.date(2026, 7, 14)
    report = build_report(
        config=_config(),
        end_date=end,
        days=14,
        start_date=dt.date(2026, 7, 13),
        pilot_state={"pilot_id": "SHADOW-20260713", "start_date": "2026-07-13"},
        run_log=[
            {
                "run_id": "RUN-HISTORICAL",
                "run_date": "2026-07-10",
                "status": "SUCCESS",
                "runtime_seconds": "60",
                "actions_taken": "send supplier request",
                "agent_name": "supplier-commercial",
            },
            {
                "run_id": "RUN-PILOT",
                "run_date": "2026-07-13",
                "status": "SUCCESS",
                "runtime_seconds": "60",
                "actions_taken": "internal_research",
                "agent_name": "gov-tender-intelligence",
            },
        ],
        evaluations=[],
        cases=[],
    )

    assert report["status"] == "IN_PROGRESS"
    assert report["pilot_window"]["start"] == "2026-07-13"
    assert report["current"]["run_log"]["external_action_marker_count"] == 0
    assert report["warnings"]
    assert report["production_routing_enabled"] is False


def test_completed_shadow_pilot_blocks_when_metric_target_fails() -> None:
    end = dt.date(2026, 7, 26)
    report = build_report(
        config=_config(),
        end_date=end,
        days=14,
        start_date=dt.date(2026, 7, 13),
        pilot_state={"pilot_id": "SHADOW-20260713", "start_date": "2026-07-13"},
        run_log=[
            {
                "run_id": "RUN-FAIL",
                "run_date": "2026-07-13",
                "status": "FAIL",
                "runtime_seconds": "60",
                "actions_taken": "internal_research",
                "agent_name": "gov-tender-intelligence",
            }
        ],
        evaluations=[],
        cases=[],
    )

    assert report["status"] == "BLOCKED"
    assert any("task_success_rate" in blocker for blocker in report["blockers"])


def test_daily_profile_telemetry_requires_every_profile_each_calendar_day() -> None:
    config = _config() | {
        "daily_profile_telemetry": {
            "required": True,
            "expected_profiles": ["profile-a", "profile-b"],
            "probe_trigger_type": "shadow_profile_probe",
            "evaluation_scenario_id": "shadow_profile_probe",
        }
    }
    report = build_report(
        config=config,
        end_date=dt.date(2026, 7, 26),
        days=14,
        start_date=dt.date(2026, 7, 13),
        pilot_state={"pilot_id": "SHADOW-20260713", "start_date": "2026-07-13"},
        run_log=[
            {"run_date": "2026-07-13", "trigger_type": "shadow_profile_probe", "agent_name": "profile-a", "status": "SUCCESS"},
            {"run_date": "2026-07-13", "trigger_type": "shadow_profile_probe", "agent_name": "profile-b", "status": "SUCCESS"},
        ],
        evaluations=[
            {"evaluated_at": "2026-07-13T06:00:00+00:00", "scenario_id": "shadow_profile_probe", "profile": "profile-a", "status": "PASS", "evidence_completeness_pct": "100", "policy_compliance": "PASS"},
            {"evaluated_at": "2026-07-13T06:00:00+00:00", "scenario_id": "shadow_profile_probe", "profile": "profile-b", "status": "PASS", "evidence_completeness_pct": "100", "policy_compliance": "PASS"},
        ],
        cases=[],
    )

    assert report["status"] == "BLOCKED"
    assert report["daily_profile_telemetry"]["complete_day_count"] == 1
    assert "2026-07-14" in report["daily_profile_telemetry"]["missing_by_day"]
    assert any("daily profile probe/evaluation coverage" in blocker for blocker in report["blockers"])
    assert "Daily Profile Telemetry" in render_html(report)


def test_daily_profile_telemetry_counts_one_day_once_despite_repeated_runs() -> None:
    telemetry = summarize_daily_profile_telemetry(
        config={
            "daily_profile_telemetry": {
                "required": True,
                "expected_profiles": ["profile-a"],
                "probe_trigger_type": "shadow_profile_probe",
                "evaluation_scenario_id": "shadow_profile_probe",
            }
        },
        run_rows=[
            {"run_date": "2026-07-13", "trigger_type": "shadow_profile_probe", "agent_name": "profile-a"},
            {"run_date": "2026-07-13", "trigger_type": "shadow_profile_probe", "agent_name": "profile-a"},
        ],
        evaluation_rows=[
            {"evaluated_at": "2026-07-13T06:00:00+00:00", "scenario_id": "shadow_profile_probe", "profile": "profile-a"},
            {"evaluated_at": "2026-07-13T07:00:00+00:00", "scenario_id": "shadow_profile_probe", "profile": "profile-a"},
        ],
        start=dt.date(2026, 7, 13),
        end=dt.date(2026, 7, 13),
    )

    assert telemetry["status"] == "PASS"
    assert telemetry["observed_day_count"] == 1
    assert telemetry["complete_day_count"] == 1
