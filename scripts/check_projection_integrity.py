#!/usr/bin/env python3
"""Rebuild event projections and compare them with live CSV projections."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import EVENTS_FILE, load_events  # noqa: E402
from scripts.rebuild_projections_from_events import PROJECTIONS, load_headers, project, write_projection  # noqa: E402

DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "projections" / "integrity"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def load_live_rows(path: Path, id_field: str) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", newline="", encoding="utf-8") as f:
        return {
            str(row.get(id_field, "") or ""): {key: str(value or "") for key, value in row.items() if key is not None}
            for row in csv.DictReader(f)
            if row.get(id_field)
        }


def count_blank_primary_keys(path: Path, id_field: str) -> int:
    if not path.exists():
        return 0
    with path.open("r", newline="", encoding="utf-8") as f:
        return sum(1 for row in csv.DictReader(f) if not str(row.get(id_field, "") or "").strip())


def row_changes(projected: dict[str, str], live: dict[str, str], headers: list[str]) -> dict[str, dict[str, str]]:
    changes: dict[str, dict[str, str]] = {}
    for field in headers:
        projected_value = str(projected.get(field, "") or "")
        live_value = str(live.get(field, "") or "")
        if projected_value != live_value:
            changes[field] = {"projected": projected_value, "live": live_value}
    return changes


def compare_projection(name: str, projected_rows: list[dict[str, str]]) -> dict[str, Any]:
    spec = PROJECTIONS[name]
    id_field = spec["id_field"]
    live = load_live_rows(spec["file"], id_field)
    blank_live_primary_keys = count_blank_primary_keys(spec["file"], id_field)
    blank_projected_primary_keys = sum(1 for row in projected_rows if not str(row.get(id_field, "") or "").strip())
    projected = {str(row.get(id_field, "") or ""): row for row in projected_rows if row.get(id_field)}
    headers = load_headers(spec["file"])

    missing_from_live = sorted(set(projected) - set(live))
    missing_from_projection = sorted(set(live) - set(projected))
    changed = []
    for object_id in sorted(set(projected) & set(live)):
        changes = row_changes(projected[object_id], live[object_id], headers)
        if changes:
            changed.append(
                {
                    "id": object_id,
                    "changed_field_count": len(changes),
                    "changed_fields": sorted(changes),
                    "sample_changes": dict(list(changes.items())[:10]),
                }
            )

    return {
        "projection": name,
        "file": display_path(spec["file"]),
        "id_field": id_field,
        "projected_rows": len(projected),
        "live_rows": len(live),
        "missing_from_live": missing_from_live,
        "missing_from_projection": missing_from_projection,
        "changed_rows": changed,
        "blank_live_primary_keys": blank_live_primary_keys,
        "blank_projected_primary_keys": blank_projected_primary_keys,
        "drift_count": (
            len(missing_from_live)
            + len(missing_from_projection)
            + len(changed)
            + blank_live_primary_keys
            + blank_projected_primary_keys
        ),
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Projection Integrity Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Events file: `{report['events_file']}`",
        f"- Status: **{report['status']}**",
        f"- Drift count: {report['drift_count']}",
        "",
        "This is read-only unless the caller separately runs the projection rebuild with `--write`.",
        "",
        "## Projections",
        "",
    ]
    for item in report["projections"]:
        lines.extend(
            [
                f"### {item['projection']}",
                f"- File: `{item['file']}`",
                f"- Projected rows: {item['projected_rows']}",
                f"- Live rows: {item['live_rows']}",
                f"- Missing from live: {len(item['missing_from_live'])}",
                f"- Missing from projection: {len(item['missing_from_projection'])}",
                f"- Changed rows: {len(item['changed_rows'])}",
                f"- Blank live primary keys: {item['blank_live_primary_keys']}",
                f"- Blank projected primary keys: {item['blank_projected_primary_keys']}",
                "",
            ]
        )
        for label in ("missing_from_live", "missing_from_projection"):
            if item[label]:
                lines.append(f"{label}: `{', '.join(item[label][:20])}`")
                lines.append("")
        if item["changed_rows"]:
            sample = ", ".join(row["id"] for row in item["changed_rows"][:20])
            lines.append(f"changed row sample: `{sample}`")
            lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_report(events_path: Path, output_dir: Path, *, write_rebuilt_csvs: bool = True) -> dict[str, Any]:
    events = load_events(events_path)
    projected = project(events)
    output_dir.mkdir(parents=True, exist_ok=True)
    if write_rebuilt_csvs:
        for name, rows in projected.items():
            spec = PROJECTIONS[name]
            write_projection(output_dir / spec["file"].name, load_headers(spec["file"]), rows)
    comparisons = [compare_projection(name, rows) for name, rows in projected.items()]
    drift_count = sum(item["drift_count"] for item in comparisons)
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "events_file": display_path(events_path),
        "output_dir": display_path(output_dir),
        "status": "PASS" if drift_count == 0 else "DRIFT",
        "drift_count": drift_count,
        "projections": comparisons,
        "safety_note": "Read-only integrity check. CSV projections are compared but data/*.csv is not mutated.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare event-ledger projections with live CSV projection files")
    parser.add_argument("--events", default=str(EVENTS_FILE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--no-rebuilt-csvs", action="store_true", help="Only write JSON/Markdown report")
    parser.add_argument("--fail-on-drift", action="store_true")
    args = parser.parse_args()

    events_path = Path(args.events)
    if not events_path.is_absolute():
        events_path = PROJECT_ROOT / events_path
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    report = build_report(events_path, output_dir, write_rebuilt_csvs=not args.no_rebuilt_csvs)
    json_path = output_dir / "projection_integrity.json"
    md_path = output_dir / "projection_integrity.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, report)

    print(json.dumps({
        "status": report["status"],
        "drift_count": report["drift_count"],
        "json": display_path(json_path),
        "markdown": display_path(md_path),
    }, indent=2))
    return 1 if args.fail_on_drift and report["drift_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
