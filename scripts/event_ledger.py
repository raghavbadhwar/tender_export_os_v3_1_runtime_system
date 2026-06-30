#!/usr/bin/env python3
"""Append-only event ledger helpers for Tender Export OS v4.1."""

from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVENTS_FILE = PROJECT_ROOT / "data" / "events.jsonl"

REQUIRED_EVENT_FIELDS = {
    "event_id",
    "event_time",
    "event_type",
    "actor",
    "case_id",
    "object_type",
    "object_id",
    "source",
    "payload",
    "citations",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def new_event_id() -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"EVT-{stamp}-{uuid.uuid4().hex[:10]}"


def normalize_citations(citations: list[str] | None) -> list[str]:
    return [str(item) for item in (citations or []) if str(item).strip()]


def build_event(
    event_type: str,
    actor: str,
    *,
    case_id: str = "",
    object_type: str = "",
    object_id: str = "",
    source: str = "local_runtime",
    payload: dict[str, Any] | None = None,
    citations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": new_event_id(),
        "event_time": now_iso(),
        "event_type": event_type,
        "actor": actor,
        "case_id": case_id or "",
        "object_type": object_type or "",
        "object_id": object_id or "",
        "source": source,
        "payload": payload or {},
        "citations": normalize_citations(citations),
    }


def validate_event(event: dict[str, Any]) -> list[str]:
    errors = []
    missing = sorted(REQUIRED_EVENT_FIELDS - set(event))
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
    if not isinstance(event.get("payload"), dict):
        errors.append("payload must be an object")
    if not isinstance(event.get("citations"), list):
        errors.append("citations must be a list")
    try:
        dt.datetime.fromisoformat(str(event.get("event_time", "")).replace("Z", "+00:00"))
    except ValueError:
        errors.append("event_time must be ISO-8601")
    return errors


def append_event(
    event_type: str,
    actor: str,
    *,
    case_id: str = "",
    object_type: str = "",
    object_id: str = "",
    source: str = "local_runtime",
    payload: dict[str, Any] | None = None,
    citations: list[str] | None = None,
    events_file: Path = EVENTS_FILE,
) -> dict[str, Any]:
    event = build_event(
        event_type,
        actor,
        case_id=case_id,
        object_type=object_type,
        object_id=object_id,
        source=source,
        payload=payload,
        citations=citations,
    )
    errors = validate_event(event)
    if errors:
        raise ValueError(f"Invalid event: {'; '.join(errors)}")
    events_file.parent.mkdir(parents=True, exist_ok=True)
    with events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def load_events(events_file: Path = EVENTS_FILE) -> list[dict[str, Any]]:
    if not events_file.exists():
        return []
    events = []
    with events_file.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            event = json.loads(line)
            errors = validate_event(event)
            if errors:
                raise ValueError(f"{events_file}:{line_number}: {'; '.join(errors)}")
            events.append(event)
    return events


def relative(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))
