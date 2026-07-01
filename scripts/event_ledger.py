#!/usr/bin/env python3
"""Append-only event ledger helpers for Tender Export OS v4.1."""

from __future__ import annotations

import datetime as dt
import json
import os
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVENTS_FILE = Path(os.environ.get("TENDER_OS_EVENTS_FILE", PROJECT_ROOT / "data" / "events.jsonl"))
EVENT_TYPE_REGISTRY = PROJECT_ROOT / "config" / "schemas" / "event_types.yaml"

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


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _payload_key_paths(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.append(path)
            paths.extend(_payload_key_paths(child, path))
        return paths
    if isinstance(value, list):
        paths = []
        for index, child in enumerate(value):
            paths.extend(_payload_key_paths(child, f"{prefix}[{index}]"))
        return paths
    return []


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",")]
    return value.strip("\"'")


def _split_inline_items(value: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    for char in value:
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
        if char == "," and depth == 0:
            items.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        items.append("".join(current).strip())
    return items


def _parse_inline_map(value: str) -> dict[str, Any]:
    text = value.strip()
    if not (text.startswith("{") and text.endswith("}")):
        return {}
    body = text[1:-1].strip()
    if not body:
        return {}
    result: dict[str, Any] = {}
    for item in _split_inline_items(body):
        key, _, raw_value = item.partition(":")
        if key.strip():
            result[key.strip()] = _parse_scalar(raw_value)
    return result


def parse_event_type_registry_minimal(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {"defaults": {}, "events": {}}
    section = ""
    pending_default_list: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw.startswith(" ") and stripped.endswith(":"):
            section = stripped[:-1]
            pending_default_list = None
            continue
        if section == "defaults":
            if stripped.startswith("- ") and pending_default_list:
                data["defaults"].setdefault(pending_default_list, []).append(_parse_scalar(stripped[2:]))
                continue
            key, _, raw_value = stripped.partition(":")
            if not key:
                continue
            if raw_value.strip():
                data["defaults"][key] = _parse_scalar(raw_value)
                pending_default_list = None
            else:
                data["defaults"][key] = []
                pending_default_list = key
        elif section == "events":
            key, _, raw_value = stripped.partition(":")
            if key:
                data["events"][key] = _parse_inline_map(raw_value)
    return data


@lru_cache(maxsize=1)
def load_event_type_registry() -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(EVENT_TYPE_REGISTRY.read_text(encoding="utf-8")) or {}
    except ModuleNotFoundError:
        return parse_event_type_registry_minimal(EVENT_TYPE_REGISTRY)


def effective_event_policy(event_type: str) -> dict[str, Any] | None:
    registry = load_event_type_registry()
    events = registry.get("events", {})
    if event_type not in events:
        return None
    policy = dict(registry.get("defaults", {}))
    policy.update(events.get(event_type) or {})
    return policy


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
    payload = event.get("payload")
    citations = event.get("citations")
    if not isinstance(payload, dict):
        errors.append("payload must be an object")
        payload = {}
    if not isinstance(citations, list):
        errors.append("citations must be a list")
        citations = []
    try:
        dt.datetime.fromisoformat(str(event.get("event_time", "")).replace("Z", "+00:00"))
    except ValueError:
        errors.append("event_time must be ISO-8601")

    event_type = str(event.get("event_type", ""))
    policy = effective_event_policy(event_type)
    if policy is None:
        errors.append(f"unknown event_type: {event_type!r}")
        return errors

    expected_object_type = str(policy.get("object_type", ""))
    if str(event.get("object_type", "")) != expected_object_type:
        errors.append(
            f"object_type must be {expected_object_type!r} for event_type {event_type!r}"
        )

    allowed_actors = [str(item) for item in _as_list(policy.get("actor_allowed"))]
    actor = str(event.get("actor", ""))
    if allowed_actors and "*" not in allowed_actors and actor not in allowed_actors:
        errors.append(f"actor {actor!r} is not allowed for event_type {event_type!r}")

    required_payload_fields = [str(item) for item in _as_list(policy.get("required_payload_fields"))]
    for field in required_payload_fields:
        if field not in payload or payload.get(field) in ("", None):
            errors.append(f"payload missing required field: {field}")

    allowed_payload_fields = [str(item) for item in _as_list(policy.get("allowed_payload_fields"))]
    if allowed_payload_fields and "*" not in allowed_payload_fields:
        extra_fields = sorted(set(payload) - set(allowed_payload_fields))
        if extra_fields:
            errors.append(f"payload has disallowed fields: {', '.join(extra_fields)}")

    forbidden_keys = {str(item).lower() for item in _as_list(policy.get("forbidden_payload_keys"))}
    forbidden_found = sorted(
        path for path in _payload_key_paths(payload) if path.split(".")[-1].lower() in forbidden_keys
    )
    if forbidden_found:
        errors.append(f"payload contains forbidden keys: {', '.join(forbidden_found)}")

    if policy.get("citation_required") and not normalize_citations(citations):
        errors.append(f"citations required for event_type {event_type!r}")
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
