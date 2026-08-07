from __future__ import annotations

import subprocess

from scripts.validate_computer_use_readiness import build_readiness, summarize_output


def runner_with(outputs: dict[tuple[str, ...], tuple[int, str, str]]):
    def runner(command, cwd, capture_output, text, timeout, check):
        returncode, stdout, stderr = outputs.get(tuple(command), (0, "", ""))
        return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr=stderr)

    return runner


def test_summarize_computer_use_doctor_detects_permissions_and_display_warning() -> None:
    summary = summarize_output(
        "✅ tcc_accessibility: Accessibility is granted.\n"
        "✅ tcc_screen_recording: Screen Recording is granted.\n"
        "✅ screen_capture_capability: ScreenCaptureKit reachable; 0 display(s) shareable.\n"
    )

    assert summary["accessibility_granted"] is True
    assert summary["screen_recording_granted"] is True
    assert summary["display_shareable_count_zero"] is True


def test_computer_use_readiness_blocks_zero_shareable_display() -> None:
    report = build_readiness(
        config={"portal_assist_enabled": False, "forbidden_actions": ["payment"]},
        runner=runner_with(
            {
                ("hermes", "doctor"): (0, "✓ computer_use", ""),
                ("hermes", "computer-use", "status"): (0, "cua-driver installed", ""),
                ("hermes", "computer-use", "doctor"): (0, "0 display(s) shareable", ""),
            }
        ),
    )

    assert report["status"] == "BLOCKED"
    assert "computer-use doctor reports 0 display(s) shareable" in report["blockers"]
    assert any("visible display" in step for step in report["remediation_steps"])
    assert report["portal_assist_enabled"] is False
    assert report["external_actions_executed"] is False


def test_computer_use_readiness_is_ready_for_read_only_canary_when_checks_pass() -> None:
    report = build_readiness(
        config={"portal_assist_enabled": False, "forbidden_actions": []},
        runner=runner_with(
            {
                ("hermes", "doctor"): (0, "✓ computer_use", ""),
                ("hermes", "computer-use", "status"): (0, "cua-driver installed", ""),
                ("hermes", "computer-use", "doctor"): (0, "Accessibility is granted\nScreen Recording is granted\n1 display(s) shareable", ""),
            }
        ),
    )

    assert report["status"] == "READY_FOR_READ_ONLY_CANARY"
    assert report["blockers"] == []
    assert report["remediation_steps"] == []
