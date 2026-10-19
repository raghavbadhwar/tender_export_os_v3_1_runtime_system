from __future__ import annotations

from scripts.audit_upgrade_plan_status import parse_task_rows, status_kind


def test_parse_task_rows_and_status_kinds() -> None:
    text = """
| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Complete thing | ✅ | 2026-07-13 |
| TASK-002 | Waiting gate | 🟡 Blocked on owner | 2026-07-13 |
| TASK-003 | Broken thing | ❌ | 2026-07-13 |
| TASK-004 | Unknown thing | maybe | 2026-07-13 |
"""

    rows = parse_task_rows(text)

    assert [row["task_id"] for row in rows] == ["TASK-001", "TASK-002", "TASK-003", "TASK-004"]
    assert [status_kind(row["completed"]) for row in rows] == [
        "complete",
        "blocked_or_in_progress",
        "failed",
        "unknown",
    ]
