import csv
from concurrent.futures import ThreadPoolExecutor

import pytest

from scripts.event_ledger import append_event, load_events
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


def test_append_event_rejects_blank_source(tmp_path) -> None:
    with pytest.raises(ValueError, match="source must be a non-empty string"):
        append_event(
            "case.created",
            "test",
            object_type="case",
            object_id="GOV-20990101-001",
            source="",
            payload={"status": "WATCHLIST"},
            citations=["https://example.com/tender"],
            events_file=tmp_path / "events.jsonl",
        )


def test_append_event_assigns_stream_positions_and_dedupes_idempotency_key(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"

    first = append_event(
        "case.created",
        "test",
        object_type="case",
        object_id="GOV-20990101-001",
        payload={"status": "WATCHLIST"},
        citations=["https://example.com/tender"],
        idempotency_key="case:GOV-20990101-001:create",
        events_file=events_path,
    )
    duplicate = append_event(
        "case.created",
        "test",
        object_type="case",
        object_id="GOV-20990101-001",
        payload={"status": "WATCHLIST"},
        citations=["https://example.com/tender"],
        idempotency_key="case:GOV-20990101-001:create",
        events_file=events_path,
    )
    second = append_event(
        "case.updated",
        "test",
        object_type="case",
        object_id="GOV-20990101-001",
        payload={"updates": {"status": "DEEP_READ"}},
        citations=["https://example.com/tender"],
        correlation_id="RUN-TEST-001",
        causation_id=first["event_id"],
        events_file=events_path,
    )

    assert duplicate["event_id"] == first["event_id"]
    assert [event["stream_position"] for event in load_events(events_path)] == [1, 2]
    assert second["correlation_id"] == "RUN-TEST-001"
    assert second["causation_id"] == first["event_id"]


def test_append_event_is_concurrency_safe(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"

    def write(index: int) -> dict:
        return append_event(
            "case.updated",
            "test",
            object_type="case",
            object_id=f"GOV-20990101-{index:03d}",
            payload={"updates": {"status": "WATCHLIST"}},
            citations=["https://example.com/tender"],
            idempotency_key=f"case:GOV-20990101-{index:03d}:update",
            events_file=events_path,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(write, range(1, 21)))

    events = load_events(events_path)
    assert len(events) == 20
    assert sorted(event["stream_position"] for event in events) == list(range(1, 21))


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
