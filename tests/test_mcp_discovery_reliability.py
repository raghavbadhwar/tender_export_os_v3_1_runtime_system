from __future__ import annotations

import json
import subprocess

from scripts.check_mcp_discovery_reliability import (
    parse_cold_result,
    parse_warm_result,
    run_trials,
)


def test_parse_cold_result_requires_connection_and_expected_tool_count() -> None:
    result = subprocess.CompletedProcess(
        args=["hermes"],
        returncode=0,
        stdout="✓ Connected (2050ms)\n✓ Tools discovered: 9\n",
        stderr="",
    )

    parsed = parse_cold_result(result, expected_tools=9, duration_seconds=2.1)

    assert parsed["ok"] is True
    assert parsed["connected"] is True
    assert parsed["tools_discovered"] == 9
    assert parsed["duration_seconds"] == 2.1


def test_parse_warm_result_requires_strict_canary_json() -> None:
    good = subprocess.CompletedProcess(
        args=["hermes"],
        returncode=0,
        stdout=json.dumps(
            {
                "mcp_tools_visible": True,
                "status": "success",
                "external_actions": False,
            }
        ),
        stderr="",
    )
    bad = subprocess.CompletedProcess(
        args=["hermes"], returncode=0, stdout="MCP probably works", stderr=""
    )

    assert parse_warm_result(good, duration_seconds=1.0)["ok"] is True
    assert parse_warm_result(bad, duration_seconds=1.0)["ok"] is False


def test_run_trials_reports_pass_only_when_every_trial_passes() -> None:
    calls: list[list[str]] = []

    def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "test" in command:
            return subprocess.CompletedProcess(
                command, 0, "✓ Connected (100ms)\n✓ Tools discovered: 9\n", ""
            )
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(
                {
                    "mcp_tools_visible": True,
                    "status": "success",
                    "external_actions": False,
                }
            ),
            "",
        )

    report = run_trials(
        profile="tender-export-os",
        server="tender_os",
        cold_trials=2,
        warm_trials=3,
        expected_tools=9,
        runner=runner,
    )

    assert report["status"] == "PASS"
    assert report["cold_passed"] == 2
    assert report["warm_passed"] == 3
    assert len(calls) == 5
    assert report["external_actions_executed"] is False
