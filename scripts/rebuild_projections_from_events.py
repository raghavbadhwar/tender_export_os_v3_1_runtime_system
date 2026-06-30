#!/usr/bin/env python3
"""Rebuild CSV projections from data/events.jsonl."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path
from typing import Any

from event_ledger import EVENTS_FILE, load_events


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "projections"

PROJECTIONS = {
    "case": {
        "file": PROJECT_ROOT / "data" / "master_cases.csv",
        "id_field": "case_id",
        "snapshot_event": "case.snapshot_imported",
    },
    "approval": {
        "file": PROJECT_ROOT / "data" / "approvals_receipts.csv",
        "id_field": "approval_id",
        "snapshot_event": "approval.snapshot_imported",
    },
    "supplier": {
        "file": PROJECT_ROOT / "data" / "supplier_master.csv",
        "id_field": "supplier_id",
        "snapshot_event": "supplier.snapshot_imported",
    },
    "quote": {
        "file": PROJECT_ROOT / "data" / "quote_master.csv",
        "id_field": "quote_id",
        "snapshot_event": "quote.snapshot_imported",
    },
    "source_health": {
        "file": PROJECT_ROOT / "data" / "source_health.csv",
        "id_field": "source_name",
        "snapshot_event": "source_health.snapshot_imported",
    },
    "plugin_health": {
        "file": PROJECT_ROOT / "data" / "plugin_health.csv",
        "id_field": "plugin_or_tool",
        "snapshot_event": "plugin_health.snapshot_imported",
    },
    "buyer": {
        "file": PROJECT_ROOT / "data" / "buyer_master.csv",
        "id_field": "buyer_id",
        "snapshot_event": "buyer.snapshot_imported",
    },
    "rfq": {
        "file": PROJECT_ROOT / "data" / "rfq_master.csv",
        "id_field": "rfq_id",
        "snapshot_event": "rfq.snapshot_imported",
    },
    "demand_research": {
        "file": PROJECT_ROOT / "data" / "demand_research.csv",
        "id_field": "research_id",
        "snapshot_event": "demand_research.snapshot_imported",
    },
}


def load_headers(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return next(csv.reader(f), [])


def normalize_row(row: dict[str, Any], headers: list[str]) -> dict[str, str]:
    return {field: str(row.get(field, "") or "") for field in headers}


def apply_update(current: dict[str, str], payload: dict[str, Any], headers: list[str]) -> dict[str, str]:
    row = dict(current)
    updates = payload.get("updates") if isinstance(payload.get("updates"), dict) else payload
    for field, value in updates.items():
        if field in headers:
            row[field] = str(value if value is not None else "")
    return row


def project(events: list[dict]) -> dict[str, list[dict[str, str]]]:
    states: dict[str, dict[str, dict[str, str]]] = {name: {} for name in PROJECTIONS}
    headers = {name: load_headers(spec["file"]) for name, spec in PROJECTIONS.items()}

    for event in events:
        object_type = event.get("object_type", "")
        if object_type not in PROJECTIONS:
            continue
        spec = PROJECTIONS[object_type]
        id_field = spec["id_field"]
        payload = event.get("payload", {})
        object_id = event.get("object_id") or payload.get(id_field) or payload.get("row", {}).get(id_field)
        if not object_id:
            continue

        if event.get("event_type") == spec["snapshot_event"] and isinstance(payload.get("row"), dict):
            states[object_type][object_id] = normalize_row(payload["row"], headers[object_type])
        elif event.get("event_type") in {f"{object_type}.updated", f"{object_type}.created"}:
            existing = states[object_type].get(object_id, {field: "" for field in headers[object_type]})
            states[object_type][object_id] = apply_update(existing, payload, headers[object_type])
        elif event.get("event_type") == "case.status_changed" and object_type == "case":
            existing = states[object_type].get(object_id, {field: "" for field in headers[object_type]})
            updates = {
                "status": payload.get("new_status", ""),
                "updated_at": str(event.get("event_time", ""))[:10],
            }
            if payload.get("actor"):
                updates["created_by_agent"] = payload["actor"]
            states[object_type][object_id] = apply_update(existing, {"updates": updates}, headers[object_type])
        elif event.get("event_type") == "approval.owner_decision_recorded" and object_type == "approval":
            existing = states[object_type].get(object_id, {field: "" for field in headers[object_type]})
            states[object_type][object_id] = apply_update(existing, payload, headers[object_type])

    return {
        name: sorted(rows.values(), key=lambda row: row.get(PROJECTIONS[name]["id_field"], ""))
        for name, rows in states.items()
    }


def write_projection(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild CSV projections from the v4.1 event ledger")
    parser.add_argument("--events", default=str(EVENTS_FILE), help="Event ledger path")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Dry-run projection output directory")
    parser.add_argument("--write", action="store_true", help="Write rebuilt projections back to data/*.csv")
    args = parser.parse_args()

    events_path = Path(args.events)
    if not events_path.is_absolute():
        events_path = PROJECT_ROOT / events_path
    events = load_events(events_path)
    projected = project(events)

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    for name, rows in projected.items():
        spec = PROJECTIONS[name]
        headers = load_headers(spec["file"])
        target = spec["file"] if args.write else output_dir / spec["file"].name
        if args.write:
            backup = spec["file"].with_suffix(spec["file"].suffix + ".projection.bak")
            shutil.copy2(spec["file"], backup)
        write_projection(target, headers, rows)
        print(f"{name}: wrote {len(rows)} rows to {target}")

    if not args.write:
        print("Dry-run projection complete. Use --write only after reviewing output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
