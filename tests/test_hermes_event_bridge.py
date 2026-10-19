import asyncio
import json

from scripts.hermes_event_bridge import handle_event


def test_agent_hook_records_only_allowlisted_metadata(tmp_path) -> None:
    events_file = tmp_path / "events.jsonl"
    context = {
        "platform": "telegram",
        "user_id": "sensitive-user",
        "session_id": "session-123",
        "message": "secret inbound text",
        "response": "secret outbound text",
        "iteration": 4,
        "tool_names": ["terminal", "browser"],
        "tools": [{"name": "terminal", "args": {"token": "secret"}}],
    }

    event = asyncio.run(handle_event("agent:step", context, events_file=events_file))

    assert event["event_type"] == "hermes.agent_step"
    assert event["object_type"] == "hermes_run"
    assert event["object_id"] == "session-123"
    assert event["payload"] == {
        "platform": "telegram",
        "profile": "tender-export-os",
        "session_id": "session-123",
        "iteration": 4,
        "tool_names": ["terminal", "browser"],
        "status": "IN_PROGRESS",
    }
    serialized = events_file.read_text(encoding="utf-8")
    for secret in ("sensitive-user", "secret inbound text", "secret outbound text", "token", "args"):
        assert secret not in serialized


def test_gateway_hook_handles_empty_context_without_private_content(tmp_path) -> None:
    events_file = tmp_path / "events.jsonl"

    event = asyncio.run(handle_event("gateway:startup", {}, events_file=events_file))

    assert event["event_type"] == "hermes.gateway_started"
    assert event["payload"]["profile"] == "tender-export-os"
    assert event["payload"]["status"] == "STARTED"
    assert event["object_id"].startswith("gateway-")
    assert json.loads(events_file.read_text(encoding="utf-8"))["event_id"] == event["event_id"]


def test_unknown_hook_event_is_ignored(tmp_path) -> None:
    event = asyncio.run(handle_event("command:unknown", {}, events_file=tmp_path / "events.jsonl"))
    assert event is None
