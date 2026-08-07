from __future__ import annotations

import datetime as dt

from scripts.plan_kanban_recovery import build_recovery_plan


NOW = dt.datetime(2026, 7, 12, 12, 0, tzinfo=dt.timezone.utc)


def task(
    task_id: str,
    *,
    case_id: str = "GOV-1",
    stage: str = "intake",
    status: str = "running",
    assignee: str = "gov-tender-intelligence",
    worker_pid: int | None = 101,
    age_seconds: int = 60,
    failures: int = 0,
    external_effect: bool = False,
) -> dict:
    started = NOW - dt.timedelta(seconds=age_seconds)
    return {
        "id": task_id,
        "status": status,
        "assignee": assignee,
        "created_at": started.timestamp(),
        "started_at": started.timestamp(),
        "last_heartbeat_at": started.timestamp(),
        "worker_pid": worker_pid,
        "consecutive_failures": failures,
        "body": (
            "TEOS_TYPED_HANDOFF_V1\n"
            f'{{"approval_required":false,"case_id":"{case_id}","deadline":"",'
            '"input_artifacts":[],"next_profile":"tender-export-os",'
            '"required_output_schema":"x","source_event_ids":[],'
            f'"stage":"{stage}","stop_conditions":[],"workflow_type":"GOV"}}\n'
            f"external_effect: {str(external_effect).lower()}"
        ),
    }


def test_recovery_reclaims_only_dead_or_stale_workers() -> None:
    live = task("live", worker_pid=101, age_seconds=60)
    dead = task("dead", worker_pid=202, age_seconds=60, stage="fast_kill")
    stale = task("stale", worker_pid=303, age_seconds=20000, stage="deep_read")

    report = build_recovery_plan(
        [live, dead, stale],
        known_profiles={"gov-tender-intelligence"},
        known_case_ids={"GOV-1"},
        now=NOW,
        stale_timeout_seconds=14400,
        failure_limit=2,
        pid_is_alive=lambda pid: pid in {101, 303},
    )
    actions = {row["task_id"]: row["action"] for row in report["actions"]}

    assert "live" not in actions
    assert actions["dead"] == "RECLAIM_DEAD_WORKER"
    assert actions["stale"] == "RECLAIM_STALE_WORKER"


def test_recovery_blocks_failures_external_effects_orphans_unknowns_and_duplicates() -> None:
    tasks = [
        task("failed", status="ready", failures=2, stage="fast_kill", worker_pid=None),
        task("external", status="ready", failures=1, stage="execution", worker_pid=None, external_effect=True),
        task("orphan", case_id="GOV-MISSING", status="ready", worker_pid=None),
        task("unknown", assignee="legacy-alias", status="ready", stage="supplier", worker_pid=None),
        task("dup-old", status="ready", stage="pricing", worker_pid=None, age_seconds=100),
        task("dup-new", status="ready", stage="pricing", worker_pid=None, age_seconds=10),
    ]

    report = build_recovery_plan(
        tasks,
        known_profiles={"gov-tender-intelligence"},
        known_case_ids={"GOV-1"},
        now=NOW,
        stale_timeout_seconds=14400,
        failure_limit=2,
        pid_is_alive=lambda _pid: False,
    )
    by_task = {row["task_id"]: row for row in report["actions"]}

    assert by_task["failed"]["action"] == "AUTO_BLOCK_FAILURE_LIMIT"
    assert by_task["external"]["action"] == "BLOCK_EXTERNAL_EFFECT_RETRY"
    assert by_task["external"]["requires_new_owner_command"] is True
    assert by_task["orphan"]["action"] == "BLOCK_ORPHAN"
    assert by_task["unknown"]["action"] == "BLOCK_UNKNOWN_ASSIGNEE"
    assert by_task["dup-new"]["action"] == "BLOCK_DUPLICATE"
    assert by_task["dup-new"]["keep_task_id"] == "dup-old"
