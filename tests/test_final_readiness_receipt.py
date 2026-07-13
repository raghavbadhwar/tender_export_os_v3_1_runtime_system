from __future__ import annotations

from pathlib import Path

from scripts.generate_final_readiness_receipt import cli_payload, generate_receipt


def test_final_readiness_is_blocked_until_pilot_and_auth_gates_pass() -> None:
    receipt = generate_receipt()

    assert receipt["status"] == "BLOCKED"
    assert receipt["plan_completed"] is False
    assert receipt["owner_signoff_present"] is False
    assert any(row["task_id"] == "TASK-092" for row in receipt["blocking_tasks"])
    assert receipt["all_blockers_have_owner_action_and_proof"] is True
    assert all(row["owner"] and row["next_action"] and row["proof_required"] for row in receipt["blocking_tasks"])
    assert "profile_routing" in receipt["evidence"]
    assert "blockers" in receipt["evidence"]["profile_routing"]
    assert "computer_use" in receipt["evidence"]
    assert "blockers" in receipt["evidence"]["computer_use"]
    assert "computer_use_canary" in receipt["evidence"]
    assert receipt["evidence"]["computer_use_canary"]["status"] in {"PASS", "FAIL", "MISSING"}
    assert "drive_revalidation" in receipt["evidence"]
    assert "remediation_steps" in receipt["evidence"]["drive_revalidation"]
    assert "owner_action_packet" in receipt["evidence"]
    assert "production_readiness_gate" in receipt["evidence"]
    assert "plan_status_audit" in receipt["evidence"]
    assert receipt["evidence"]["production_readiness_gate"].get("production_routing_enabled") is not True
    assert receipt["evidence"]["plan_status_audit"].get("external_actions_executed") is not True


def test_final_readiness_cli_payload_has_exact_blocker_ids() -> None:
    payload = cli_payload(
        {"status": "BLOCKED", "blocking_tasks": [{"task_id": "TASK-092"}, {"task_id": "TASK-097"}]},
        receipt_path=Path("final.json"),
    )

    assert payload["blocking_tasks"] == 2
    assert payload["blocking_task_count"] == 2
    assert payload["blocking_task_ids"] == ["TASK-092", "TASK-097"]
