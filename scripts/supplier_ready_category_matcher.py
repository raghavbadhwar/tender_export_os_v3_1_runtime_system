#!/usr/bin/env python3
"""Match low-competition categories to already mapped suppliers."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event  # noqa: E402
from scripts.low_competition_order_radar import (  # noqa: E402
    DATA_DIR,
    DEFAULT_CATEGORIES,
    OUTPUT_DIR,
    build_supplier_readiness_by_category,
    load_csv,
    load_yaml_config,
    now_utc,
    relative,
    today_compact,
)


def match_supplier_ready_categories(
    suppliers: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    categories_config: dict[str, Any],
    quote_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    del cases  # current readiness is supplier/quote based; cases are kept in the public CLI contract.
    readiness = build_supplier_readiness_by_category(suppliers, quote_rows or [], categories_config)
    return sorted(readiness.values(), key=lambda row: row["supplier_readiness_score"], reverse=True)


def build_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": f"RUN-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-SUPPLIER-READY-{uuid.uuid4().hex[:6]}",
        "created_at": now_utc(),
        "records_analyzed": len(rows),
        "top_candidates_count": sum(1 for row in rows if row["supplier_readiness_score"] >= 60),
        "safety_boundary": "Internal supplier-readiness analysis only. Marketplace listing price is not quote proof; no supplier outreach executed.",
        "categories": rows,
    }


def write_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"supplier_ready_categories_{today_compact()}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def maybe_append_event(report: dict[str, Any], path: Path, *, dry_run: bool, record_event: bool) -> None:
    if dry_run or not record_event:
        return
    append_event(
        "supplier_ready.categories_matched",
        "supplier_ready_category_matcher",
        object_type="supplier_ready_category",
        object_id=report["run_id"],
        source="local_runtime",
        payload={
            "run_id": report["run_id"],
            "report_path": relative(path),
            "records_analyzed": report["records_analyzed"],
            "top_candidates_count": report["top_candidates_count"],
            "created_at": report["created_at"],
        },
        citations=[relative(path)],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Score supplier-ready low-competition categories")
    parser.add_argument("--dry-run", action="store_true", help="Write local report only; do not append events")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--record-event", action="store_true")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    rows = match_supplier_ready_categories(
        load_csv(DATA_DIR / "supplier_master.csv", "supplier_master.example.csv"),
        load_csv(DATA_DIR / "master_cases.csv", "master_cases.example.csv"),
        load_yaml_config(DEFAULT_CATEGORIES),
        quote_rows=load_csv(DATA_DIR / "quote_master.csv", "quote_master.example.csv"),
    )
    report = build_report(rows)
    path = write_report(report, Path(args.output_dir))
    maybe_append_event(report, path, dry_run=args.dry_run, record_event=args.record_event)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Supplier-ready category report: {path}")
        print("No external action was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
