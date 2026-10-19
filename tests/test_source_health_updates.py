from __future__ import annotations

import csv
from pathlib import Path

from scripts.source_runtime import source_health


def write_health_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_name", "health_status", "last_checked_date", "notes"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "source_name": "CPPP — Central Public Procurement Portal",
                "health_status": "Needs Login",
                "last_checked_date": "2026-06-30",
                "notes": "Old",
            }
        )


def test_update_source_health_uses_canonical_name_and_same_projection_values(tmp_path, monkeypatch) -> None:
    health_csv = tmp_path / "source_health.csv"
    write_health_csv(health_csv)
    captured: list[tuple[str, dict]] = []

    monkeypatch.setattr(source_health, "SOURCE_HEALTH_CSV", health_csv)
    monkeypatch.setattr(source_health, "today", lambda: "2026-07-12")
    monkeypatch.setattr(
        source_health,
        "append_source_health_event",
        lambda name, updates, citations=None: captured.append((name, updates)),
    )

    canonical, materialized = source_health.update_source_health(
        "CPPP/eProcure",
        {"health_status": "Working", "notes": "Verified", "records_found": 1},
        record_event=True,
    )

    with health_csv.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))

    assert canonical == "CPPP — Central Public Procurement Portal"
    assert materialized["last_checked_date"] == "2026-07-12"
    assert row["health_status"] == materialized["health_status"] == "Working"
    assert row["last_checked_date"] == materialized["last_checked_date"]
    assert row["notes"] == materialized["notes"] == "Verified"
    assert captured == [(canonical, materialized)]
