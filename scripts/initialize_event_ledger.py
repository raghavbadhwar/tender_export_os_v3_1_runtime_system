#!/usr/bin/env python3
"""Seed data/events.jsonl from the current local registers."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from event_ledger import EVENTS_FILE, build_event, validate_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REGISTER_SPECS = [
    ("case", "case_id", "data/master_cases.csv", "case.snapshot_imported"),
    ("approval", "approval_id", "data/approvals_receipts.csv", "approval.snapshot_imported"),
    ("supplier", "supplier_id", "data/supplier_master.csv", "supplier.snapshot_imported"),
    ("quote", "quote_id", "data/quote_master.csv", "quote.snapshot_imported"),
    ("source_health", "source_name", "data/source_health.csv", "source_health.snapshot_imported"),
    ("plugin_health", "plugin_or_tool", "data/plugin_health.csv", "plugin_health.snapshot_imported"),
    ("buyer", "buyer_id", "data/buyer_master.csv", "buyer.snapshot_imported"),
    ("rfq", "rfq_id", "data/rfq_master.csv", "rfq.snapshot_imported"),
    ("demand_research", "research_id", "data/demand_research.csv", "demand_research.snapshot_imported"),
]


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_events(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            errors = validate_event(event)
            if errors:
                raise ValueError(f"{event.get('event_id')}: {'; '.join(errors)}")
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the v4.1 event ledger from current CSV registers")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing events.jsonl")
    parser.add_argument("--output", default=str(EVENTS_FILE), help="Event ledger output path")
    args = parser.parse_args()

    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    if output.exists() and not args.overwrite:
        print(f"Refusing to overwrite existing ledger: {output}")
        print("Use --overwrite only after reviewing current data/events.jsonl.")
        return 2

    events: list[dict] = [
        build_event(
            "system.snapshot_started",
            "initialize_event_ledger",
            object_type="system",
            object_id="tender-export-os",
            payload={"source": "current local CSV registers"},
            citations=["data/*.csv"],
        )
    ]

    for object_type, id_field, rel_path, event_type in REGISTER_SPECS:
        rows = load_csv(PROJECT_ROOT / rel_path)
        for row in rows:
            object_id = row.get(id_field, "")
            case_id = row.get("case_id", "") if "case_id" in row else ""
            events.append(
                build_event(
                    event_type,
                    "initialize_event_ledger",
                    case_id=case_id,
                    object_type=object_type,
                    object_id=object_id,
                    payload={"row": row},
                    citations=[rel_path],
                )
            )

    events.append(
        build_event(
            "system.snapshot_completed",
            "initialize_event_ledger",
            object_type="system",
            object_id="tender-export-os",
            payload={"events_created": len(events) + 1},
            citations=["data/*.csv"],
        )
    )

    write_events(output, events)
    print(f"Wrote {len(events)} events to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
