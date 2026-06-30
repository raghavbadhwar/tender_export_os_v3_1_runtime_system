#!/usr/bin/env python3
"""Validate v4.1 register schemas and the append-only event ledger."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = PROJECT_ROOT / "config" / "schemas"
EVENT_SCHEMA = SCHEMA_DIR / "event.schema.json"
URL_RE = re.compile(r"^(https?://|www\.)", re.IGNORECASE)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def parse_date(value: str) -> bool:
    if not value:
        return True
    try:
        dt.date.fromisoformat(value[:10])
        return True
    except ValueError:
        return False


def parse_datetime(value: str) -> bool:
    if not value:
        return True
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def parse_number(value: str) -> bool:
    if value == "" or value is None:
        return True
    try:
        float(str(value).replace(",", ""))
        return True
    except ValueError:
        return False


def validate_csv_schema(schema_path: Path) -> list[str]:
    errors: list[str] = []
    schema = load_json(schema_path)
    if "file" not in schema:
        return []
    csv_path = PROJECT_ROOT / schema["file"]
    if not csv_path.exists():
        return [f"{schema['file']}: file missing"]

    headers, rows = load_csv(csv_path)
    required_columns = schema.get("required_columns", [])
    missing_columns = [column for column in required_columns if column not in headers]
    if missing_columns:
        errors.append(f"{schema['file']}: missing columns {missing_columns}")

    primary_key = schema.get("primary_key")
    seen_keys: set[str] = set()
    for index, row in enumerate(rows, start=2):
        if None in row:
            errors.append(f"{schema['file']}:{index}: extra cells {row[None]}")
        if primary_key:
            value = row.get(primary_key, "")
            if not value:
                errors.append(f"{schema['file']}:{index}: missing primary key {primary_key}")
            elif value in seen_keys:
                errors.append(f"{schema['file']}:{index}: duplicate primary key {value}")
            seen_keys.add(value)

        for field in schema.get("required_fields", []):
            if not row.get(field, ""):
                errors.append(f"{schema['file']}:{index}: required field {field} is blank")

        for field, allowed in schema.get("enums", {}).items():
            value = row.get(field, "")
            if value not in allowed:
                errors.append(f"{schema['file']}:{index}: {field}={value!r} not in {allowed}")

        for field in schema.get("date_fields", []):
            value = row.get(field, "")
            if value and not parse_date(value):
                errors.append(f"{schema['file']}:{index}: {field}={value!r} is not an ISO date")

        for field in schema.get("datetime_fields", []):
            value = row.get(field, "")
            if value and not parse_datetime(value):
                errors.append(f"{schema['file']}:{index}: {field}={value!r} is not an ISO datetime")

        for field in schema.get("numeric_fields", []):
            value = row.get(field, "")
            if value and not parse_number(value):
                errors.append(f"{schema['file']}:{index}: {field}={value!r} is not numeric")

        for field in schema.get("url_fields", []):
            value = row.get(field, "")
            if value and not URL_RE.match(value):
                errors.append(f"{schema['file']}:{index}: {field}={value!r} is not a URL")

    return errors


def validate_events() -> list[str]:
    schema = load_json(EVENT_SCHEMA)
    path = PROJECT_ROOT / schema["file"]
    errors: list[str] = []
    if not path.exists():
        return [f"{schema['file']}: file missing; run scripts/initialize_event_ledger.py --overwrite"]

    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for index, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{schema['file']}:{index}: invalid JSON: {exc}")
                continue
            for field in schema["required_fields"]:
                if field not in event:
                    errors.append(f"{schema['file']}:{index}: missing field {field}")
            event_id = event.get("event_id", "")
            if not event_id:
                errors.append(f"{schema['file']}:{index}: missing event_id")
            elif event_id in seen:
                errors.append(f"{schema['file']}:{index}: duplicate event_id {event_id}")
            seen.add(event_id)
            if event.get("event_type") not in schema["event_types"]:
                errors.append(f"{schema['file']}:{index}: unknown event_type {event.get('event_type')!r}")
            if event.get("object_type") not in schema["object_types"]:
                errors.append(f"{schema['file']}:{index}: unknown object_type {event.get('object_type')!r}")
            if not parse_datetime(str(event.get("event_time", ""))):
                errors.append(f"{schema['file']}:{index}: event_time is not ISO datetime")
            if not isinstance(event.get("payload"), dict):
                errors.append(f"{schema['file']}:{index}: payload must be object")
            if not isinstance(event.get("citations"), list):
                errors.append(f"{schema['file']}:{index}: citations must be list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate v4.1 CSV schemas and event ledger")
    parser.add_argument("--csv-only", action="store_true", help="Skip event ledger validation")
    args = parser.parse_args()

    schema_paths = sorted(path for path in SCHEMA_DIR.glob("*.schema.json") if path.name != "event.schema.json")
    errors: list[str] = []
    for schema_path in schema_paths:
        errors.extend(validate_csv_schema(schema_path))
    if not args.csv_only:
        errors.extend(validate_events())

    if errors:
        print("Schema validation failed:")
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print(f"Schema validation passed: {len(schema_paths)} CSV schemas" + ("" if args.csv_only else " + event ledger"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
