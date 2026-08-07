#!/usr/bin/env python3
"""Export and verify a privacy-safe deterministic event-ledger checkpoint."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.event_ledger import EVENTS_FILE, load_events
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import EVENTS_FILE, load_events  # type: ignore

CHECKPOINT_SCHEMA = "ledger_checkpoint.v1"
TIMESTAMP_POLICY = "max_event_time_utc_from_validated_stream"
GENESIS = b"tender-os-ledger-checkpoint.v1"


def _canonical_event(event: dict[str, Any]) -> bytes:
    return json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _terminal_hash(events: list[dict[str, Any]]) -> str:
    previous = hashlib.sha256(GENESIS).digest()
    for event in events:
        previous = hashlib.sha256(previous + b"\n" + _canonical_event(event)).digest()
    return previous.hex()


def _max_event_time(events: list[dict[str, Any]]) -> str | None:
    if not events:
        return None
    times = [dt.datetime.fromisoformat(str(event["event_time"]).replace("Z", "+00:00")).astimezone(dt.timezone.utc) for event in events]
    return max(times).replace(microsecond=0).isoformat()


def generate_checkpoint(events_file: Path) -> dict[str, Any]:
    raw = events_file.read_bytes() if events_file.exists() else b""
    events = load_events(events_file)
    return {
        "schema_version": CHECKPOINT_SCHEMA,
        "event_count": len(events),
        "terminal_hash": _terminal_hash(events),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "timestamp_policy": TIMESTAMP_POLICY,
        "event_time_max_utc": _max_event_time(events),
    }


def compare_checkpoint(actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    for field in ("schema_version", "event_count", "terminal_hash", "source_sha256", "timestamp_policy", "event_time_max_utc"):
        if actual.get(field) != expected.get(field):
            mismatches.append(field)
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events-file", type=Path, default=EVENTS_FILE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-checkpoint", type=Path)
    args = parser.parse_args()
    try:
        checkpoint = generate_checkpoint(args.events_file)
        if args.expected_checkpoint:
            expected = json.loads(args.expected_checkpoint.read_text(encoding="utf-8"))
            mismatches = compare_checkpoint(checkpoint, expected)
            checkpoint["verification"] = {"status": "PASS" if not mismatches else "BLOCKED", "mismatches": mismatches}
            if mismatches:
                checkpoint["tamper_detected"] = True
        else:
            mismatches = []
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        checkpoint = {
            "schema_version": CHECKPOINT_SCHEMA,
            "status": "BLOCKED",
            "error": type(exc).__name__,
            "tamper_detected": True,
        }
        mismatches = ["ledger_unreadable"]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(checkpoint, indent=2, sort_keys=True))
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
