from __future__ import annotations

from scripts.run_production_readiness_gate import POST_SEAL_COMMANDS, READINESS_COMMANDS, apply_seal_results, build_report


def test_production_gate_includes_live_cron_installation_validation() -> None:
    assert ["scripts/validate_live_cron_installation.py", "--json"] in READINESS_COMMANDS
    assert ["scripts/validate_live_cron_installation.py", "--json"] in POST_SEAL_COMMANDS


def _record(command: str, *, ok: bool = True, payload: dict | None = None) -> dict:
    return {
        "command": ["python", *command.split()],
        "command_text": f"python {command}",
        "returncode": 0 if ok else 1,
        "ok": ok,
        "duration_seconds": 0.01,
        "stdout_tail": "",
        "stderr_tail": "",
        "json": payload or {},
    }


def test_production_readiness_gate_reports_blocked_readiness_without_failure() -> None:
    report = build_report(
        [
            _record("scripts/validate_register_schemas.py"),
            _record(
                "scripts/generate_owner_action_packet.py --json",
                payload={"json": "owner.json", "markdown": "owner.md", "blocking_task_count": 2},
            ),
            _record(
                "scripts/generate_final_readiness_receipt.py --json",
                payload={"status": "BLOCKED", "receipt": "final.json", "blocking_tasks": 2},
            ),
        ]
    )

    assert report["status"] == "BLOCKED"
    assert report["failure_count"] == 0
    assert report["readiness_status"] == "BLOCKED"
    assert report["blocking_task_count"] == 2
    assert report["blocking_task_ids"] == []
    assert report["owner_action_packet"]["markdown"] == "owner.md"
    assert report["external_actions_executed"] is False
    assert report["production_routing_enabled"] is False


def test_production_readiness_gate_reports_fail_on_command_failure() -> None:
    report = build_report(
        [
            _record("scripts/validate_register_schemas.py", ok=False),
            _record("scripts/generate_final_readiness_receipt.py --json", payload={"status": "READY"}),
        ]
    )

    assert report["status"] == "FAIL"
    assert report["failure_count"] == 1


def test_production_readiness_gate_reports_ready_for_owner_signoff() -> None:
    report = build_report(
        [
            _record(
                "scripts/generate_final_readiness_receipt.py --json",
                payload={"status": "READY_FOR_OWNER_SIGNOFF", "receipt": "final.json", "blocking_tasks": 0},
            )
        ]
    )

    assert report["status"] == "READY_FOR_OWNER_SIGNOFF"


def test_production_readiness_gate_seal_updates_current_readiness_and_owner_packet() -> None:
    report = build_report(
        [
            _record(
                "scripts/generate_final_readiness_receipt.py --json",
                payload={"status": "BLOCKED", "receipt": "old-final.json", "blocking_tasks": 2},
            )
        ]
    )

    sealed = apply_seal_results(
        report,
        [
            _record("scripts/generate_final_readiness_receipt.py --json", payload={"status": "BLOCKED", "receipt": "current-final-1.json", "blocking_tasks": 2}),
            _record("scripts/generate_owner_action_packet.py --json", payload={"json": "current-owner.json", "markdown": "current-owner.md", "blocking_task_count": 2}),
            _record("scripts/audit_upgrade_plan_status.py --json", payload={"status": "PASS"}),
            _record("scripts/generate_final_readiness_receipt.py --json", payload={"status": "BLOCKED", "receipt": "current-final-2.json", "blocking_tasks": 2}),
        ],
    )

    assert sealed["sealed"] is True
    assert sealed["seal_failure_count"] == 0
    assert sealed["readiness_receipt"] == "current-final-2.json"
    assert sealed["blocking_task_count"] == 2
    assert sealed["blocking_task_ids"] == []
    assert sealed["owner_action_packet"]["markdown"] == "current-owner.md"
    assert sealed["command_count"] == 5
