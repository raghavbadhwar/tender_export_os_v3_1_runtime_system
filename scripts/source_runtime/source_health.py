"""Source-health event and CSV helpers."""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Any

from .credential_policy import sanitize_payload

try:
    from scripts.event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover
    from event_ledger import append_event  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_HEALTH_CSV = PROJECT_ROOT / "data" / "source_health.csv"
ALLOWED_STATUSES = {
    "Working",
    "Needs Login",
    "Paywalled",
    "Low Relevance",
    "Broken",
    "Manual Check Required",
    "Blocked by CAPTCHA",
    "Restricted / Do Not Scrape",
    "Access Blocked",
    "URL Changed",
}


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def normalize_status(status: str) -> str:
    return status if status in ALLOWED_STATUSES else "Manual Check Required"


def source_name_matches(row_name: str, source_name: str) -> bool:
    row_value = row_name.lower()
    source_value = source_name.lower()
    if row_value == source_value:
        return True
    source_token = source_value.split(" ")[0].split("/")[0]
    return bool(source_token and source_token in row_value)


def append_source_health_event(source_name: str, updates: dict[str, Any], citations: list[str] | None = None) -> None:
    append_event(
        "source_health.updated",
        "deep_source_runtime",
        object_type="source_health",
        object_id=source_name,
        source="source_runtime",
        payload={"updates": sanitize_payload(updates)},
        citations=citations or [],
    )


def upsert_source_health_csv(source_name: str, updates: dict[str, Any]) -> None:
    if not SOURCE_HEALTH_CSV.exists():
        return
    with SOURCE_HEALTH_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    found = False
    for row in rows:
        if source_name_matches(row.get("source_name", ""), source_name):
            found = True
            for key, value in updates.items():
                if key in headers:
                    row[key] = str(value)
            if "last_checked_date" in headers:
                row["last_checked_date"] = today()
            if "health_status" in headers and "health_status" in updates:
                row["health_status"] = normalize_status(str(updates["health_status"]))
            break
    if not found:
        row = {header: "" for header in headers}
        if "source_name" in headers:
            row["source_name"] = source_name
        for key, value in updates.items():
            if key in headers:
                row[key] = str(value)
        if "last_checked_date" in headers:
            row["last_checked_date"] = today()
        rows.append(row)
    with SOURCE_HEALTH_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
