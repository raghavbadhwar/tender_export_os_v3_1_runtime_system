#!/usr/bin/env python3
"""Derive approval-execution monitor state from canonical receipt-ingestion events."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from event_ledger import load_events
except ModuleNotFoundError:  # pragma: no cover - package import path used by pytest
    from scripts.event_ledger import load_events


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"
PENDING_APPROVED_EXECUTION = "PENDING_APPROVED_EXECUTION"
EXECUTED_VERIFIED = "EXECUTED_VERIFIED"
SAFETY_HELD_NOT_SENT = "SAFETY_HELD_NOT_SENT"


def _clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _receipt_paths(events: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            _clean(event.get("payload", {}).get("receipt_path"))
            for event in events
            if isinstance(event.get("payload"), dict)
            and _clean(event["payload"].get("receipt_path"))
        }
    )


def _receipt_ids(events: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            _clean(event.get("payload", {}).get("receipt_id"))
            for event in events
            if isinstance(event.get("payload"), dict)
            and _clean(event["payload"].get("receipt_id"))
        }
    )


def execution_events_for_approval(
    approval: dict[str, Any],
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return canonical receipt-ingestion events matching one exact approval/case scope."""
    approval_id = _clean(approval.get("approval_id"))
    case_id = _clean(approval.get("case_id"))
    if not approval_id or not case_id:
        return []
    matches: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") != "execution.receipt_ingested":
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        if _clean(payload.get("approval_id")) != approval_id:
            continue
        if _clean(payload.get("case_id")) != case_id:
            continue
        matches.append(event)
    return matches


def disposition_for_approval(
    approval: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Classify one approved scope without mutating the approval register.

    Receipt state is authoritative only after a canonical
    ``execution.receipt_ingested`` event with verification_status=VERIFIED. The
    underlying approval CSV retains the owner-decision fact; callers receive a
    derived projection in ``external_effect`` instead.
    """
    raw_effect = _clean(approval.get("external_effect"))
    matches = execution_events_for_approval(approval, events)
    verified = [
        event
        for event in matches
        if _clean(event.get("payload", {}).get("verification_status")).upper() == "VERIFIED"
    ]
    sent = [
        event
        for event in verified
        if _clean(event.get("payload", {}).get("execution_status")) == EXECUTED_VERIFIED
        and event.get("payload", {}).get("external_action_sent") is True
    ]
    held = [
        event
        for event in verified
        if _clean(event.get("payload", {}).get("execution_status")) == SAFETY_HELD_NOT_SENT
        and event.get("payload", {}).get("external_action_sent") is False
    ]

    if sent:
        status = EXECUTED_VERIFIED
        matched = sent
        next_action = "Execution receipt verified. Track replies or delivery outcomes only; do not resend or escalate without a new owner command."
    elif held:
        status = SAFETY_HELD_NOT_SENT
        matched = held
        next_action = "Safety hold verified: no external action was sent. Preserve the hold; any new route or send requires fresh scoped approval."
    elif raw_effect.upper() == PENDING_APPROVED_EXECUTION:
        status = PENDING_APPROVED_EXECUTION
        matched = []
        notes = _clean(approval.get("notes")).lower()
        next_action = (
            "Keep held; resolve proof/contact/scope blockers and create a fresh approval if execution method changes."
            if any(marker in notes for marker in ("safety_held", "raw_lead", "blocked_missing", "blocked by", "blocked_"))
            else "Approved action is awaiting a verified execution receipt."
        )
    else:
        status = raw_effect
        matched = []
        next_action = "No execution disposition is derived for this approval scope."

    return {
        "approval_id": _clean(approval.get("approval_id")),
        "case_id": _clean(approval.get("case_id")),
        "approval_external_effect": raw_effect,
        "external_effect": status,
        "execution_receipt_count": len(matched),
        "execution_receipt_ids": _receipt_ids(matched),
        "execution_receipt_paths": _receipt_paths(matched),
        "next_action": next_action,
    }


def dispositions_by_approval(
    approvals: list[dict[str, Any]],
    *,
    events_path: Path = EVENTS_PATH,
) -> dict[str, dict[str, Any]]:
    events = load_events(events_path)
    return {
        _clean(approval.get("approval_id")): disposition_for_approval(approval, events)
        for approval in approvals
        if _clean(approval.get("approval_id"))
    }


def is_pending_execution(disposition: dict[str, Any]) -> bool:
    return _clean(disposition.get("external_effect")) == PENDING_APPROVED_EXECUTION
