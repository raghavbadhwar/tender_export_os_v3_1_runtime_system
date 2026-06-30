#!/usr/bin/env python3
"""Structural tests for Tender Export OS 90+ upgrade scripts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", *args],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def assert_ok(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stderr or result.stdout


def test_mobile_approval_payload_dry_run_outputs_pending_approvals() -> None:
    result = run_cmd("scripts/render_mobile_approval_payload.py", "--all-pending", "--dry-run")
    assert_ok(result)
    assert "APPROVE" in result.stdout
    assert "REJECT" in result.stdout
    assert "CHANGES" in result.stdout


def test_drive_manifest_dry_run_writes_manifest_and_receipt() -> None:
    result = run_cmd("scripts/sync_drive_manifest.py", "--dry-run", "--case-id", "GOV-20260630-001")
    assert_ok(result)
    assert "DRY_RUN" in result.stdout
    assert (PROJECT_ROOT / "data" / "drive_manifest.csv").exists()


def test_source_adapter_harness_safe_mode_writes_report() -> None:
    result = run_cmd("scripts/test_source_adapters.py", "--safe", "--limit", "5")
    assert_ok(result)
    report = PROJECT_ROOT / "outputs" / "source_adapter_tests" / "source_adapter_test_report.json"
    assert report.exists()
    data = json.loads(report.read_text())
    assert data["summary"]["adapters_checked"] >= 1


def test_founder_dashboard_and_scorecard_generate() -> None:
    assert_ok(run_cmd("scripts/generate_founder_dashboard.py"))
    assert_ok(run_cmd("scripts/generate_90_plus_scorecard.py"))
    assert (PROJECT_ROOT / "outputs" / "dashboards" / "founder_dashboard.html").exists()
    assert (PROJECT_ROOT / "outputs" / "scorecards" / "90_plus_scorecard.html").exists()


def test_agent_prompt_audit_passes() -> None:
    result = run_cmd("scripts/audit_agent_prompts.py")
    assert_ok(result)
    assert "PASS" in result.stdout


def test_source_health_report_generates() -> None:
    result = run_cmd("scripts/generate_source_health_report.py")
    assert_ok(result)
    assert (PROJECT_ROOT / "outputs" / "source_health" / "source_health_report.html").exists()


def test_plugin_receipt_help_and_mobile_dashboard() -> None:
    assert_ok(run_cmd("scripts/record_plugin_run_receipt.py", "--help"))
    result = run_cmd("scripts/render_mobile_dashboard_summary.py", "--dry-run")
    assert_ok(result)
    assert "Recommended action" in result.stdout
