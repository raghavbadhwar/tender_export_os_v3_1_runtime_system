from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.event_ledger import build_event
from scripts.route_event_to_kanban import (
    load_rules,
    read_event_records,
    route_events,
)


def event(event_type: str, *, case_id: str = "GOV-ROUTE-001", payload: dict | None = None) -> dict:
    object_type = {
        "tender.deadline_changed": "case",
        "source.adapter_degraded": "source_adapter",
        "supplier.quote_received": "quote",
        "buyer.reply_received": "buyer_reply",
        "forecast.matured": "forecast_observation",
    }.get(event_type, "case")
    return build_event(
        event_type,
        "fixture",
        case_id=case_id,
        object_type=object_type,
        object_id=f"object-{event_type}",
        source="fixture",
        payload=payload or {},
        citations=["tests/fixtures/event.json"],
        idempotency_key=f"fixture:{event_type}:{case_id}",
    )


def test_deadline_event_creates_internal_dry_run_card_without_mutation() -> None:
    result = route_events(
        [event("tender.deadline_changed", payload={"previous_deadline": "2026-07-10", "new_deadline": "2026-07-20"})],
        config=load_rules(),
        write=False,
        canonical_case_ids={"GOV-ROUTE-001"},
    )

    assert result["status"] == "PASS"
    assert result["dry_run"] is True
    assert result["kanban_mutated"] is False
    assert result["card_count"] == 1
    card = result["cards"][0]
    assert card["route_via"] == "teos-orchestrator"
    assert card["external_actions_allowed"] is False
    assert card["model_runs_executed_by_router"] is False
    assert "untrusted evidence data" in result["commands"][0][result["commands"][0].index("--body") + 1]


def test_case_scoped_event_absent_from_canonical_case_register_is_ignored() -> None:
    fixture_event = event(
        "tender.deadline_changed",
        case_id="GOV-ROUTE-FIXTURE-001",
        payload={"previous_deadline": "2026-07-10", "new_deadline": "2026-07-20"},
    )

    result = route_events(
        [fixture_event],
        config=load_rules(),
        write=False,
        canonical_case_ids={"GOV-ROUTE-001"},
    )

    assert result["card_count"] == 0
    assert result["ignored"] == [
        {
            "event_id": fixture_event["event_id"],
            "event_type": "tender.deadline_changed",
            "reason": "case_not_in_canonical_register",
        }
    ]


def test_substantive_reply_rule_rejects_unmatched_reply_without_task() -> None:
    result = route_events(
        [event("buyer.reply_received", payload={"communication_id": "COMM-1", "classification": "NOT_INTERESTED"})],
        config=load_rules(),
        write=False,
    )

    assert result["card_count"] == 0
    assert result["ignored"] == [
        {
            "event_id": result["ignored"][0]["event_id"],
            "event_type": "buyer.reply_received",
            "reason": "payload_did_not_match_rule",
        }
    ]


def test_system_scoped_source_health_event_is_routable() -> None:
    result = route_events(
        [event("source.adapter_degraded", case_id="", payload={"source_name": "fixture", "consecutive_failures": 3, "threshold": 2, "receipt_path": "receipts/source.json"})],
        config=load_rules(),
        write=False,
    )

    assert result["card_count"] == 1
    assert result["cards"][0]["case_id"] == ""
    assert result["cards"][0]["assignee"] == "teos-orchestrator"


def test_write_routes_once_and_records_receipt(tmp_path: Path) -> None:
    source = event("forecast.matured", case_id="", payload={"forecast_id": "F-1", "outcome_id": "O-1"})
    events_file = tmp_path / "events.jsonl"
    calls: list[list[str]] = []

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout='{"id":"TASK-ROUTE-1"}', stderr="")

    result = route_events([source], config=load_rules(), write=True, events_file=events_file, runner=runner)

    assert result["status"] == "PASS"
    assert result["kanban_mutated"] is True
    assert result["results"][0]["task_id"] == "TASK-ROUTE-1"
    assert len(calls) == 1
    receipt = json.loads(events_file.read_text(encoding="utf-8").splitlines()[0])
    assert receipt["event_type"] == "kanban.event_routed"
    assert receipt["payload"]["status"] == "CREATED"
    assert receipt["payload"]["event_id"] == source["event_id"]


def test_invalid_and_unmapped_rows_are_dead_lettered(tmp_path: Path) -> None:
    path = tmp_path / "fixture.jsonl"
    path.write_text(
        "not-json\n"
        + json.dumps({"event_id": "bad", "event_type": "unknown.event", "payload": {}})
        + "\n",
        encoding="utf-8",
    )

    events, dead_letters = read_event_records(path)

    assert events == []
    assert len(dead_letters) == 2
    assert "invalid JSON" in dead_letters[0]["reason"]
    assert "unknown event_type" in dead_letters[1]["reason"]
