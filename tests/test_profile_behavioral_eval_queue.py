from __future__ import annotations

import subprocess

from scripts.run_profile_behavioral_eval_queue import build_queue, run_next_profile


def test_profile_behavioral_eval_queue_marks_missing_profiles_pending() -> None:
    spec = {
        "profile": "owner",
        "profile_scope": {
            "include_owner_profile": False,
            "include_specialist_profiles": False,
        },
    }
    routing = {"behavioral_eval_report_glob": "does-not-exist/**/*.json"}

    queue = build_queue(spec=spec, routing_config=routing)

    assert queue["status"] == "PENDING"
    assert queue["pending_profile_count"] == 1
    assert queue["next_profile"] == "owner"


def test_run_next_profile_uses_single_profile_command() -> None:
    calls = []

    def fake_runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout='{"status":"PASS"}', stderr="")

    result = run_next_profile({"next_profile": "pricing-risk"}, runner=fake_runner)

    assert result["status"] == "PASS"
    assert result["profile"] == "pricing-risk"
    assert "--profile" in calls[0]
    assert "pricing-risk" in calls[0]
