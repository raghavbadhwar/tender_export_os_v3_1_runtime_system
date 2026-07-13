from __future__ import annotations

from scripts.verify_needs_input_dispatch import validate_needs_input_canary


def show(status: str, *, started_at=None, events=None, runs=None) -> dict:
    return {
        "task": {
            "id": "t_canary",
            "status": status,
            "started_at": started_at,
            "created_by": "verify_needs_input_dispatch",
        },
        "events": events or [],
        "runs": runs or [],
    }


def test_needs_input_canary_remains_blocked_and_never_runs() -> None:
    before = show(
        "blocked",
        events=[{"kind": "blocked", "payload": {"kind": "needs_input"}}],
    )
    after = show(
        "blocked",
        events=[{"kind": "blocked", "payload": {"kind": "needs_input"}}],
    )

    result = validate_needs_input_canary(before, after, [])

    assert result["ok"] is True
    assert result["status_before"] == "blocked"
    assert result["status_after"] == "blocked"
    assert result["run_count"] == 0
    assert result["needs_input_event_present"] is True


def test_needs_input_canary_rejects_auto_promotion_or_worker_run() -> None:
    before = show(
        "blocked",
        events=[{"kind": "blocked", "payload": {"kind": "needs_input"}}],
    )
    after = show("ready", started_at=123, runs=[{"outcome": "completed"}])

    result = validate_needs_input_canary(before, after, [{"outcome": "completed"}])

    assert result["ok"] is False
    assert "status after dispatcher is 'ready', not blocked" in result["errors"]
    assert "canary has worker runs" in result["errors"]
    assert "canary started a worker" in result["errors"]
