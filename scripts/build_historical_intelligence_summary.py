#!/usr/bin/env python3
"""Build and validate deterministic historical-intelligence layer summary."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
EXAMPLES_DIR = DATA_DIR / "examples"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "historical_intelligence"

TABLES = {
    "historical_tender_notices": DATA_DIR / "historical_tender_notices.csv",
    "historical_awards": DATA_DIR / "historical_awards.csv",
    "historical_buyer_category_stats": DATA_DIR / "historical_buyer_category_stats.csv",
    "historical_competition_signals": DATA_DIR / "historical_competition_signals.csv",
    "historical_import_demand": DATA_DIR / "historical_import_demand.csv",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def rows_with_example_fallback(path: Path, use_examples_if_empty: bool) -> tuple[list[dict[str, str]], str]:
    rows = load_csv(path)
    if rows or not use_examples_if_empty:
        return rows, display_path(path)
    example = EXAMPLES_DIR / f"{path.stem}.example.csv"
    return load_csv(example), display_path(example)


def category_counts(rows: list[dict[str, str]]) -> Counter:
    return Counter(row.get("category_name", "") for row in rows if row.get("category_name"))


def build_summary(*, use_examples_if_empty: bool = True) -> dict[str, Any]:
    table_summaries = {}
    all_categories: Counter = Counter()
    evidence_counts: Counter = Counter()
    for name, path in TABLES.items():
        rows, source_path = rows_with_example_fallback(path, use_examples_if_empty)
        all_categories.update(category_counts(rows))
        evidence_counts.update(row.get("evidence_level", "") for row in rows if row.get("evidence_level"))
        table_summaries[name] = {
            "path": display_path(path),
            "source_used": source_path,
            "row_count": len(rows),
            "category_count": len(category_counts(rows)),
            "empty_live_table": not load_csv(path),
        }
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "table_count": len(TABLES),
        "tables": table_summaries,
        "top_categories": all_categories.most_common(10),
        "evidence_level_counts": dict(evidence_counts),
        "ready_for_ml": all(item["row_count"] > 0 for item in table_summaries.values()),
        "source_mode": "example_fallback_enabled" if use_examples_if_empty else "live_only",
        "safety_note": "Historical layer summary only. No ML training, external action, portal access, pricing, or compliance commitment executed.",
    }


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Historical Intelligence Summary",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Source mode: {summary['source_mode']}",
        f"- Ready for ML: {summary['ready_for_ml']}",
        "",
        summary["safety_note"],
        "",
        "| Table | Rows | Source used | Empty live table |",
        "|---|---:|---|---:|",
    ]
    for name, item in summary["tables"].items():
        lines.append(f"| {name} | {item['row_count']} | `{item['source_used']}` | {item['empty_live_table']} |")
    lines.extend(["", "## Top Categories", ""])
    if not summary["top_categories"]:
        lines.append("- None")
    for category, count in summary["top_categories"]:
        lines.append(f"- {category}: {count}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic historical-intelligence summary")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--live-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    summary = build_summary(use_examples_if_empty=not args.live_only)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"historical_intelligence_summary_{stamp}.json"
    md_path = output_dir / f"historical_intelligence_summary_{stamp}.md"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, summary)
    payload = {"ready_for_ml": summary["ready_for_ml"], "json": display_path(json_path), "markdown": display_path(md_path)}
    print(json.dumps(payload, indent=2) if args.json else f"Historical intelligence summary: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
