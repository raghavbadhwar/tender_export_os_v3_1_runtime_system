import datetime as dt
import json
from pathlib import Path

from scripts.kanban_blocked_task_drain import build_blocked_task_drain_plan, load_tasks_from_json


def test_blocked_task_drain_escalates_stale_blocked_task() -> None:
    now = dt.datetime(2026, 7, 1, 12, 0, tzinfo=dt.timezone.utc)
    tasks = [
        {
            "id": "task-1",
            "title": "Need owner approval",
            "status": "blocked",
            "assignee": "pricing-compliance",
            "updated_at": "2026-06-29T10:00:00+00:00",
            "blocked_reason": "owner approval missing",
        }
    ]

    plan = build_blocked_task_drain_plan(tasks, now=now, stale_hours=24)

    assert plan["mode"] == "dry_run_only"
    assert plan["kanban_mutated"] is False
    assert plan["summary"]["stale_blocked_count"] == 1
    action = plan["actions"][0]
    assert action["recommended_action"] == "ESCALATE_OWNER_APPROVAL"
    assert action["task_id"] == "task-1"


def test_blocked_task_drain_reassigns_source_and_archives_done_like_blockers() -> None:
    now = dt.datetime(2026, 7, 1, 12, 0, tzinfo=dt.timezone.utc)
    tasks = [
        {"id": "source", "title": "Portal broken", "status": "blocked", "assignee": "gov-tender-radar", "updated_at": "2026-06-29T10:00:00+00:00", "blocked_reason": "source adapter timeout"},
        {"id": "obsolete", "title": "Old rejected thing", "status": "blocked", "assignee": "hermes-chief-operator", "updated_at": "2026-06-29T10:00:00+00:00", "blocked_reason": "case rejected"},
    ]

    plan = build_blocked_task_drain_plan(tasks, now=now, stale_hours=24)
    actions = {item["task_id"]: item for item in plan["actions"]}

    assert actions["source"]["recommended_action"] == "REASSIGN_SOURCE_HEALTH"
    assert actions["source"]["suggested_assignee"] == "source-health"
    assert actions["obsolete"]["recommended_action"] == "ARCHIVE_OR_CLOSE_REVIEW"


def test_load_tasks_from_json_accepts_hermes_shapes(tmp_path: Path) -> None:
    payloads = [
        [{"id": "a"}],
        {"tasks": [{"id": "b"}]},
        {"items": [{"id": "c"}]},
    ]
    for index, payload in enumerate(payloads):
        path = tmp_path / f"tasks_{index}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert load_tasks_from_json(path)[0]["id"] in {"a", "b", "c"}
