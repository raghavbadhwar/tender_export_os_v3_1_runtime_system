from __future__ import annotations

from scripts.record_production_readiness_signoff import record_signoff


def test_production_readiness_signoff_refuses_while_blockers_remain() -> None:
    result = record_signoff(approved_by="owner")

    assert result["status"] == "BLOCKED"
    assert result["signed"] is False
    assert "TASK-092" in result["blocking_tasks"]
