#!/usr/bin/env python3
"""Bridge privacy-safe Hermes lifecycle metadata into the TEOS event stream."""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
from typing import Any

try:
    from scripts.event_ledger import EVENTS_FILE, append_event
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import EVENTS_FILE, append_event


PROFILE_NAME = "tender-export-os"
EVENT_MAP = {
    "gateway:startup": ("hermes.gateway_started", "STARTED"),
    "agent:start": ("hermes.agent_started", "STARTED"),
    "agent:step": ("hermes.agent_step", "IN_PROGRESS"),
    "agent:end": ("hermes.agent_completed", "COMPLETED"),
}
SAFE_CONTEXT_KEYS = {"platform", "session_id", "iteration", "tool_names"}
CITATIONS = ["HERMES.md", "docs/FINAL_ARCHITECTURE.md"]


def _utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _safe_payload(context: dict[str, Any], status: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "profile": PROFILE_NAME,
        "status": status,
    }
    for key in SAFE_CONTEXT_KEYS:
        value = context.get(key)
        if value in (None, "", []):
            continue
        if key == "tool_names":
            payload[key] = [str(name) for name in value if str(name).strip()]
        elif key == "iteration":
            payload[key] = int(value)
        else:
            payload[key] = str(value)
    return payload


async def handle_event(
    event_type: str,
    context: dict[str, Any] | None = None,
    *,
    events_file: Path = EVENTS_FILE,
) -> dict[str, Any] | None:
    """Record one allowlisted Hermes lifecycle event; ignore all other hooks."""
    mapped = EVENT_MAP.get(event_type)
    if mapped is None:
        return None

    ledger_type, status = mapped
    safe_context = context if isinstance(context, dict) else {}
    payload = _safe_payload(safe_context, status)
    session_id = str(payload.get("session_id", "")).strip()
    object_id = session_id or f"gateway-{_utc_stamp()}-{os.getpid()}"
    discriminator = payload.get("iteration", "")
    idempotency_key = f"hermes:{ledger_type}:{object_id}:{discriminator}"
    return append_event(
        ledger_type,
        "Hermes Chief Operator",
        object_type="hermes_run",
        object_id=object_id,
        source="hermes_gateway_hook",
        payload=payload,
        citations=CITATIONS,
        correlation_id=session_id,
        idempotency_key=idempotency_key,
        events_file=events_file,
    )


async def handle(event_type: str, context: dict[str, Any]) -> None:
    """Hermes gateway hook entry point."""
    await handle_event(event_type, context)

