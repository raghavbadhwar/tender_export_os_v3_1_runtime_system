import csv

import pytest

from scripts.event_ledger import append_event
from scripts.lib.pipeline_error import (
    append_error_event,
    make_pipeline_error,
    write_agent_run_failure,
)


def test_append_event_rejects_payload_missing_registry_required_field(tmp_path) -> None:
    with pytest.raises(ValueError, match="payload missing required field: status"):
        append_event(
            "case.created",
            "test",
            object_type="case",
            object_id="GOV-20990101-001",
            payload={},
            citations=["https://example.com/tender"],
            events_file=tmp_path / "events.jsonl",
        )


def test_append_event_rejects_wrong_registry_object_type(tmp_path) -> None:
    with pytest.raises(ValueError, match="object_type must be 'case'"):
        append_event(
            "case.created",
            "test",
            object_type="supplier",
            object_id="GOV-20990101-001",
            payload={"status": "WATCHLIST"},
            citations=["https://example.com/tender"],
            events_file=tmp_path / "events.jsonl",
        )


def test_append_event_rejects_unknown_event_type(tmp_path) -> None:
    with pytest.raises(ValueError, match="unknown event_type"):
        append_event(
            "case.unregistered",
            "test",
            object_type="case",
            object_id="GOV-20990101-001",
            payload={},
            citations=["https://example.com/tender"],
            events_file=tmp_path / "events.jsonl",
        )


def test_pipeline_error_helpers_write_event_and_failure_row(tmp_path) -> None:
    error = make_pipeline_error("safe_regression", "example blocker")
    event = append_error_event(error, actor="pytest", events_file=tmp_path / "events.jsonl")
    assert event["event_type"] == "pipeline.error"
    assert event["payload"]["reason"] == "example blocker"
    assert event["payload"]["blocker_status"] == "BLOCKED"
    assert error.exit_code() == 1

    run_log = write_agent_run_failure(
        error,
        agent_name="pytest",
        run_log_path=tmp_path / "agent_run_log.csv",
    )
    with run_log.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["status"] == "FAILURE"
    assert rows[0]["errors"] == "1"
