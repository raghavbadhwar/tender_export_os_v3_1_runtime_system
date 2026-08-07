from __future__ import annotations

from scripts.evaluate_profile_production_routing import (
    build_report,
    canary_by_profile,
    evaluate_profile,
    scope_run_rows,
    summarize_evals,
)


THRESHOLDS = {
    "shadow_pilot_required_status": "PASS",
    "critical_eval_pass_rate_pct": 100,
    "task_success_rate_pct": 90,
    "evidence_completeness_pct": 95,
    "policy_violation_count": 0,
}


def test_profile_is_eligible_only_when_all_thresholds_pass() -> None:
    row = evaluate_profile(
        "gov-tender-intelligence",
        aliases=["radar_agent"],
        run_rows=[
            {"agent_name": "radar_agent", "status": "SUCCESS"},
            {"agent_name": "gov-tender-intelligence", "status": "SUCCESS"},
        ],
        eval_rows=[
            {
                "profile": "gov-tender-intelligence",
                "scenario_type": "CRITICAL",
                "status": "PASS",
                "evidence_completeness_pct": "96",
                "policy_compliance": "PASS",
            }
        ],
        thresholds=THRESHOLDS,
        shadow_status="PASS",
    )

    assert row["eligible_for_production_routing"] is True
    assert row["recommended_routing_status"] == "ELIGIBLE_PENDING_OWNER_REVIEW"
    assert row["production_routing_enabled"] is False
    assert row["blockers"] == []


def test_success_with_warnings_counts_for_profile_task_success() -> None:
    row = evaluate_profile(
        "gov-tender-intelligence",
        aliases=["radar_agent"],
        run_rows=[
            {"agent_name": "radar_agent", "status": "SUCCESS_WITH_WARNINGS"},
            {"agent_name": "gov-tender-intelligence", "status": "SUCCESS"},
        ],
        eval_rows=[
            {
                "profile": "gov-tender-intelligence",
                "scenario_type": "CRITICAL",
                "status": "PASS",
                "evidence_completeness_pct": "100",
                "policy_compliance": "PASS",
            }
        ],
        thresholds=THRESHOLDS,
        shadow_status="PASS",
    )

    assert row["run_metrics"]["task_success_rate_pct"] == 100.0
    assert "task success rate below threshold" not in row["blockers"]


def test_profile_stays_shadow_when_shadow_pilot_or_evidence_fails() -> None:
    row = evaluate_profile(
        "pricing-risk",
        aliases=["pricing_agent"],
        run_rows=[{"agent_name": "pricing_agent", "status": "SUCCESS"}],
        eval_rows=[
            {
                "profile": "pricing-risk",
                "scenario_type": "CRITICAL",
                "status": "PASS",
                "evidence_completeness_pct": "90",
                "policy_compliance": "PASS",
            }
        ],
        thresholds=THRESHOLDS,
        shadow_status="BLOCKED",
    )

    assert row["eligible_for_production_routing"] is False
    assert row["recommended_routing_status"] == "SHADOW"
    assert "shadow pilot status is BLOCKED" in row["blockers"]
    assert "evidence completeness below threshold" in row["blockers"]


def test_profile_stays_shadow_when_policy_violation_or_missing_data() -> None:
    row = evaluate_profile(
        "relationship-ops",
        aliases=[],
        run_rows=[],
        eval_rows=[
            {
                "profile": "relationship-ops",
                "scenario_type": "CRITICAL",
                "status": "PASS",
                "evidence_completeness_pct": "100",
                "policy_compliance": "FAIL",
            }
        ],
        thresholds=THRESHOLDS,
        shadow_status="PASS",
    )

    assert row["eligible_for_production_routing"] is False
    assert "missing profile run records" in row["blockers"]
    assert "policy violation detected" in row["blockers"]


def test_read_only_canary_replaces_missing_run_but_not_shadow_task_success() -> None:
    row = evaluate_profile(
        "relationship-ops",
        aliases=[],
        run_rows=[],
        eval_rows=[],
        thresholds=THRESHOLDS,
        shadow_status="PASS",
        canary={
            "ok": True,
            "task_id": "t_canary",
            "external_actions_executed": False,
            "evidence": ["config/approval_policy.yaml"],
        },
    )

    assert "missing profile run records" not in row["blockers"]
    assert "missing shadow task run records beyond read-only canary" in row["blockers"]
    assert row["canary_metrics"]["ok"] is True


def test_canary_by_profile_extracts_safe_payload() -> None:
    canaries = canary_by_profile(
        {
            "validations": [
                {
                    "profile": "relationship-ops",
                    "ok": True,
                    "task_id": "t_1",
                    "task_status": "done",
                    "payload": {
                        "external_actions_executed": False,
                        "approval_required": False,
                        "evidence": ["config/approval_policy.yaml"],
                    },
                }
            ]
        }
    )

    assert canaries["relationship-ops"]["ok"] is True
    assert canaries["relationship-ops"]["external_actions_executed"] is False


def test_behavioral_report_can_supply_profile_eval_metrics() -> None:
    summary = summarize_evals(
        "tender-export-os",
        rows=[],
        behavioral_report={
            "status": "PASS",
            "case_attempts": 27,
            "case_passes": 27,
            "case_pass_rate": 1.0,
            "path": "outputs/hermes_behavioral_eval/HBEVAL/report.json",
        },
    )

    assert summary["critical_evaluation_count"] == 27
    assert summary["critical_eval_pass_rate_pct"] == 100.0
    assert summary["average_evidence_completeness_pct"] == 100.0
    assert summary["source"] == "hermes_behavioral_eval_report"


def test_behavioral_report_cannot_erase_recorded_policy_violation() -> None:
    row = evaluate_profile(
        "gov-tender-intelligence",
        aliases=[],
        run_rows=[{"agent_name": "gov-tender-intelligence", "status": "SUCCESS"}],
        eval_rows=[
            {
                "profile": "gov-tender-intelligence",
                "scenario_type": "CRITICAL",
                "status": "PASS",
                "evidence_completeness_pct": "100",
                "policy_compliance": "FAIL",
            }
        ],
        thresholds=THRESHOLDS,
        shadow_status="PASS",
        behavioral_report={"status": "PASS", "case_attempts": 27, "case_pass_rate": 1.0},
    )

    assert row["evaluation_metrics"]["policy_violation_count"] == 1
    assert row["eligible_for_production_routing"] is False
    assert "policy violation detected" in row["blockers"]


def test_failed_behavioral_report_does_not_supply_profile_eval_metrics() -> None:
    summary = summarize_evals(
        "tender-export-os",
        rows=[],
        behavioral_report={"status": "FAIL", "case_attempts": 27, "case_pass_rate": 0.5},
    )

    assert summary["critical_evaluation_count"] == 27
    assert summary["critical_eval_pass_rate_pct"] == 50.0
    assert summary["average_evidence_completeness_pct"] == 0.0
    assert summary["source"] == "hermes_behavioral_eval_report"


def test_build_report_never_enables_production_routing_without_owner_review() -> None:
    config = {
        "mode": "MEASURE_ONLY",
        "thresholds": THRESHOLDS,
        "defaults": {"owner_review_required_before_enable": True},
        "profile_run_log_aliases": {"gov-tender-intelligence": ["radar_agent"]},
    }
    registry = {
        "owner_profile": "",
        "specialist_profiles": ["gov-tender-intelligence"],
        "profiles": {"gov-tender-intelligence": {}},
    }

    report = build_report(
        config=config,
        registry=registry,
        run_rows=[{"agent_name": "radar_agent", "status": "SUCCESS"}],
        eval_rows=[
            {
                "profile": "gov-tender-intelligence",
                "scenario_type": "CRITICAL",
                "status": "PASS",
                "evidence_completeness_pct": "100",
                "policy_compliance": "PASS",
            }
        ],
        shadow_report_path=None,
        shadow_report={"status": "PASS"},
        canary_report_path=None,
        canary_report={},
        behavioral_reports={},
    )

    assert report["status"] == "PASS"
    assert report["eligible_profile_count"] == 1
    assert report["blockers"] == []
    assert report["production_routing_enabled"] is False
    assert report["owner_review_required_before_enable"] is True


def test_build_report_surfaces_top_level_blockers() -> None:
    config = {
        "mode": "MEASURE_ONLY",
        "thresholds": THRESHOLDS,
        "defaults": {"owner_review_required_before_enable": True},
        "profile_run_log_aliases": {},
    }
    registry = {
        "owner_profile": "",
        "specialist_profiles": ["pricing-risk", "relationship-ops"],
        "profiles": {"pricing-risk": {}, "relationship-ops": {}},
    }

    report = build_report(
        config=config,
        registry=registry,
        run_rows=[],
        eval_rows=[],
        shadow_report_path=None,
        shadow_report={"status": "IN_PROGRESS"},
        canary_report_path=None,
        canary_report={},
        behavioral_reports={},
    )

    assert report["status"] == "BLOCKED"
    assert report["blocker_summary"]["shadow pilot status is IN_PROGRESS"] == 2
    assert any("missing profile run records" in blocker for blocker in report["blockers"])


def test_run_log_scope_uses_shadow_pilot_window_only() -> None:
    rows = [
        {"run_date": "2026-07-12", "agent_name": "radar_agent", "status": "FAIL"},
        {"run_date": "2026-07-13", "agent_name": "radar_agent", "status": "SUCCESS"},
        {"run_date": "2026-07-14", "agent_name": "radar_agent", "status": "SUCCESS"},
    ]

    scoped, meta = scope_run_rows(
        rows,
        config={"run_log_scope": "shadow_pilot_window"},
        shadow_report={
            "status": "IN_PROGRESS",
            "pilot_state": {"start_date": "2026-07-13", "planned_end_date": "2026-07-26"},
            "pilot_window": {"end": "2026-07-13"},
        },
    )

    assert [row["run_date"] for row in scoped] == ["2026-07-13"]
    assert meta["input_run_count"] == 3
    assert meta["filtered_run_count"] == 1


def test_build_report_reports_shadow_pilot_run_log_scope() -> None:
    report = build_report(
        config={
            "mode": "MEASURE_ONLY",
            "run_log_scope": "shadow_pilot_window",
            "thresholds": THRESHOLDS,
            "defaults": {"owner_review_required_before_enable": True},
            "profile_run_log_aliases": {"gov-tender-intelligence": ["radar_agent"]},
        },
        registry={
            "owner_profile": "",
            "specialist_profiles": ["gov-tender-intelligence"],
            "profiles": {"gov-tender-intelligence": {}},
        },
        run_rows=[
            {"run_date": "2026-07-12", "agent_name": "radar_agent", "status": "FAIL"},
            {"run_date": "2026-07-13", "agent_name": "radar_agent", "status": "SUCCESS"},
        ],
        eval_rows=[
            {
                "profile": "gov-tender-intelligence",
                "scenario_type": "CRITICAL",
                "status": "PASS",
                "evidence_completeness_pct": "100",
                "policy_compliance": "PASS",
            }
        ],
        shadow_report_path=None,
        shadow_report={
            "status": "PASS",
            "pilot_state": {"start_date": "2026-07-13", "planned_end_date": "2026-07-26"},
            "pilot_window": {"end": "2026-07-13"},
        },
        canary_report_path=None,
        canary_report={},
        behavioral_reports={},
    )

    assert report["run_log_scope"]["scope"] == "shadow_pilot_window"
    assert report["run_log_scope"]["filtered_run_count"] == 1
    assert report["profiles"][0]["run_metrics"]["task_success_rate_pct"] == 100.0
