from __future__ import annotations

from scripts.generate_owner_action_packet import build_packet, render_markdown


def _readiness() -> dict:
    return {
        "status": "BLOCKED",
        "blocking_tasks": [
            {
                "task_id": "TASK-097",
                "owner": "Owner + Hermes Chief Operator",
                "reason": "Computer Use blocked",
                "next_action": "Fix display",
                "proof_required": "Computer Use PASS",
                "observed_evidence": {"status": "BLOCKED"},
            },
            {
                "task_id": "TASK-092",
                "owner": "Hermes Chief Operator",
                "reason": "Pilot in progress",
                "next_action": "Wait",
                "proof_required": "Shadow pilot PASS",
                "observed_evidence": {"status": "IN_PROGRESS"},
            },
            {
                "task_id": "TASK-095",
                "owner": "Owner + Tooling Integration Lead",
                "reason": "Approval required",
                "next_action": "Approve design",
                "proof_required": "Approval receipt",
                "observed_evidence": {"approved_connector_design": False},
            },
        ],
    }


def test_owner_action_packet_orders_blockers_and_remains_safe() -> None:
    packet = build_packet(_readiness(), generated_at="2026-07-13T00:00:00+00:00")

    assert packet["blocking_task_count"] == 3
    assert [row["task_id"] for row in packet["actions"]] == ["TASK-092", "TASK-095", "TASK-097"]
    assert packet["production_routing_enabled"] is False
    assert packet["external_actions_executed"] is False
    assert packet["actions"][0]["external_authority_required"] is False
    assert packet["actions"][1]["external_authority_required"] is True
    assert any("record_contact_form_connector_approval.py" in cmd for cmd in packet["actions"][1]["verification_commands"])
    assert any("record_computer_use_read_only_canary.py" in cmd for cmd in packet["actions"][2]["verification_commands"])


def test_owner_action_packet_markdown_includes_commands_and_safety_note() -> None:
    packet = build_packet(_readiness(), generated_at="2026-07-13T00:00:00+00:00")
    markdown = render_markdown(packet)

    assert "# Tender Export OS Owner Action Packet" in markdown
    assert "Action packet only" in markdown
    assert "scripts/generate_shadow_pilot_report.py --json" in markdown
    assert "hermes computer-use doctor" in markdown
