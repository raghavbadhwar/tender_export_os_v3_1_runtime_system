from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from scripts.run_upgrade_phase0_validation import (
    PHASE0_COMMANDS,
    build_report,
    write_report,
)


def test_phase0_command_set_covers_required_validators_and_focused_tests() -> None:
    flattened = [" ".join(command) for command in PHASE0_COMMANDS]

    for required in (
        "scripts/validate_agent_loops.py",
        "scripts/validate_loop_schedule.py",
        "scripts/validate_register_schemas.py",
        "scripts/validate_event_type_registry.py",
        "scripts/check_projection_integrity.py --fail-on-drift",
        "scripts/evaluate_hermes_behavioral_contracts.py --validate-only",
        "scripts/tender_os_policy.py --self-test",
    ):
        assert any(required in command for command in flattened)

    pytest_commands = [command for command in PHASE0_COMMANDS if command[:2] == ["-m", "pytest"]]
    assert len(pytest_commands) == 1
    assert "tests/test_capture_upgrade_baseline.py" in pytest_commands[0]
    assert "tests/test_mcp_discovery_reliability.py" in pytest_commands[0]
    assert "tests/test_run_upgrade_phase0_validation.py" in pytest_commands[0]


def test_build_report_preserves_complete_results_and_fails_closed() -> None:
    passing = subprocess.CompletedProcess(["python", "ok.py"], 0, "all output", "")
    failing = subprocess.CompletedProcess(["python", "bad.py"], 3, "partial", "exact failure")

    report = build_report(
        [
            {"command": ["python", "ok.py"], "completed": passing, "duration_seconds": 0.1},
            {"command": ["python", "bad.py"], "completed": failing, "duration_seconds": 0.2},
        ]
    )

    assert report["status"] == "FAIL"
    assert report["passed"] == 1
    assert report["failed"] == 1
    assert report["results"][1]["returncode"] == 3
    assert report["results"][1]["stdout"] == "partial"
    assert report["results"][1]["stderr"] == "exact failure"


def test_write_report_uses_private_permissions(tmp_path: Path) -> None:
    output = tmp_path / "validation.json"
    report = {"status": "PASS", "results": []}

    write_report(output, report)

    assert json.loads(output.read_text(encoding="utf-8")) == report
    assert os.stat(output).st_mode & 0o777 == 0o600
