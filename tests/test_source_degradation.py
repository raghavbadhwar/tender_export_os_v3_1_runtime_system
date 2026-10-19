from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

from scripts.source_degradation import apply_degradation_actions, build_degradation_actions


ROOT = Path(__file__).resolve().parents[1]


def test_degradation_requires_configured_consecutive_failure_threshold() -> None:
    health = [
        {"source_name": "CPPP — Central Public Procurement Portal", "consecutive_failures": "2", "workflow": "GOV"},
        {"source_name": "GeM — Government e-Marketplace", "consecutive_failures": "0", "workflow": "GOV"},
    ]
    results = [
        {"adapter": "cppp", "status": "ERROR", "artifact_path": "outputs/cppp.json"},
        {"adapter": "gem", "status": "HEALTHY", "artifact_path": "outputs/gem.json"},
    ]

    actions = build_degradation_actions(health, results, threshold=3, receipt_path="outputs/canary.json")

    assert len(actions) == 1
    action = actions[0]
    assert action["source_name"] == "CPPP — Central Public Procurement Portal"
    assert action["consecutive_failures"] == 3
    assert action["event_idempotency_key"].endswith(":streak-3")
    assert action["task"]["assignee"] == "gov-tender-intelligence"
    assert action["task"]["idempotency_key"].endswith(":streak-3")


def test_same_source_and_failure_streak_produces_one_action() -> None:
    health = [{"source_name": "UN Global Marketplace (UNGM)", "consecutive_failures": "3", "workflow": "EXPORT"}]
    duplicate_results = [
        {"adapter": "ungm", "status": "BLOCKED"},
        {"adapter": "ungm", "status": "ERROR"},
    ]

    actions = build_degradation_actions(health, duplicate_results, threshold=3, receipt_path="outputs/canary.json")

    assert len(actions) == 1
    assert actions[0]["task"]["assignee"] == "export-buyer-intelligence"


def test_degradation_apply_emits_event_and_idempotent_repair_card() -> None:
    action = build_degradation_actions(
        [{"source_name": "CPPP — Central Public Procurement Portal", "consecutive_failures": "2", "workflow": "GOV"}],
        [{"adapter": "cppp", "status": "ERROR"}],
        threshold=3,
        receipt_path="outputs/canary.json",
    )[0]
    events: list[dict] = []
    commands: list[list[str]] = []

    def append_event(event_type: str, actor: str, **kwargs):
        events.append({"event_type": event_type, "actor": actor, **kwargs})
        return {"event_id": "EVT-1"}

    def runner(command: list[str], **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"id": "t_repair"}), stderr="")

    applied = apply_degradation_actions([action], event_appender=append_event, runner=runner)

    assert applied == [{"source_name": action["source_name"], "event_id": "EVT-1", "task_id": "t_repair"}]
    assert events[0]["event_type"] == "source.adapter_degraded"
    assert events[0]["idempotency_key"] == action["event_idempotency_key"]
    assert "--idempotency-key" in commands[0]
    assert action["task"]["idempotency_key"] in commands[0]


def test_intentional_paywall_or_login_stop_does_not_create_repair_noise() -> None:
    actions = build_degradation_actions(
        [
            {
                "source_name": "Paid Aggregator",
                "consecutive_failures": "8",
                "workflow": "GOV",
                "paywalled": "TRUE",
                "login_required": "TRUE",
                "health_status": "Paywalled",
            }
        ],
        [{"adapter": "paid aggregator", "source_name": "Paid Aggregator", "status": "FAILING"}],
        threshold=3,
        receipt_path="outputs/yield.json",
        increment_failure=False,
    )

    assert actions == []


def test_direct_cron_style_execution_falls_back_to_local_event_ledger(tmp_path: Path) -> None:
    """Direct script execution has no project-root `scripts` package on sys.path."""
    events_path = tmp_path / "events.jsonl"
    code = textwrap.dedent(
        f"""
        import json
        import os
        import subprocess
        import sys
        from pathlib import Path

        root = Path({str(ROOT)!r})
        os.environ["TENDER_OS_EVENTS_FILE"] = {str(events_path)!r}
        sys.path = [str(root / "scripts")] + [item for item in sys.path if item not in {{"", str(root)}}]
        os.chdir({str(tmp_path)!r})
        import source_degradation

        action = source_degradation.build_degradation_actions(
            [{{"source_name": "CPPP — Central Public Procurement Portal", "consecutive_failures": "2", "workflow": "GOV"}}],
            [{{"adapter": "cppp", "status": "ERROR"}}],
            threshold=3,
            receipt_path="outputs/canary.json",
        )[0]
        result = source_degradation.apply_degradation_actions(
            [action],
            runner=lambda command, **kwargs: subprocess.CompletedProcess(command, 0, stdout=json.dumps({{"id": "repair-1"}}), stderr=""),
        )
        print(json.dumps(result))
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)[0]["task_id"] == "repair-1"
    assert events_path.is_file()
