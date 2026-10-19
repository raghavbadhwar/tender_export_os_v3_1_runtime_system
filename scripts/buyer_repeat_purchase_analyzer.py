#!/usr/bin/env python3
"""Analyze buyers that repeatedly buy fulfilment-ready categories."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event  # noqa: E402
from scripts.low_competition_order_radar import (  # noqa: E402
    DATA_DIR,
    DEFAULT_CATEGORIES,
    OUTPUT_DIR,
    load_csv,
    load_source_records,
    load_yaml_config,
    match_low_competition_category,
    normalize_text,
    now_utc,
    relative,
    safe_float,
    source_record_to_case,
    today_compact,
)


def analyze_repeat_buyers(
    cases: list[dict[str, Any]],
    buyer_master: list[dict[str, Any]],
    source_records: list[dict[str, Any]],
    categories_config: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = list(cases)
    rows.extend(source_record_to_case(record, index) for index, record in enumerate(source_records))
    buyers_by_name = {normalize_text(row.get("buyer_name", "")): row for row in buyer_master if row.get("buyer_name")}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buyer = normalize_text(row.get("buyer_name", ""))
        if buyer:
            grouped[buyer].append(row)

    output = []
    for normalized_buyer, buyer_cases in grouped.items():
        buyer_name = buyer_cases[0].get("buyer_name", "")
        category_counter: Counter[str] = Counter()
        values = []
        winners = []
        l1_values = []
        for case in buyer_cases:
            category_id, category = match_low_competition_category(case, categories_config)
            category_counter[category.get("label", category_id or case.get("product_or_service", "uncategorized"))] += 1
            value = safe_float(case.get("estimated_value_inr"))
            if value:
                values.append(value)
            if case.get("known_past_winners"):
                winners.append(case.get("known_past_winners"))
            if case.get("typical_l1_price"):
                l1_values.append(case.get("typical_l1_price"))
        master = buyers_by_name.get(normalized_buyer, {})
        best_category, best_count = category_counter.most_common(1)[0] if category_counter else ("uncategorized", 0)
        repeat_score = min(100, 25 + len(buyer_cases) * 15 + best_count * 10 + (15 if master else 0))
        output.append(
            {
                "buyer_name": buyer_name,
                "buyer_type": master.get("buyer_type") or buyer_cases[0].get("buyer_type", ""),
                "state/city": buyer_cases[0].get("state") or buyer_cases[0].get("location") or buyer_cases[0].get("delivery_location", ""),
                "categories_bought": sorted(category_counter.keys()),
                "past_tender_count": len(buyer_cases),
                "similar_category_awards": best_count,
                "average_award_value": round(sum(values) / len(values), 2) if values else "",
                "known_past_winners": sorted(set(winners)),
                "typical_L1_price": l1_values[0] if l1_values else "",
                "buyer_repeat_score": repeat_score,
                "best_category_to_watch": best_category,
                "next_watch_keywords": watch_keywords(best_category),
            }
        )
    return sorted(output, key=lambda row: row["buyer_repeat_score"], reverse=True)


def watch_keywords(category_label: str) -> list[str]:
    text = normalize_text(category_label)
    if "water" in text or "ro" in text:
        return ["RO AMC", "filter replacement", "water cooler", "date extension"]
    if "stationery" in text or "printing" in text:
        return ["stationery", "printing", "toner", "conference kit", "rate contract"]
    if "digit" in text or "scanning" in text:
        return ["scanning", "record room", "digitisation", "data entry", "indexing"]
    if "cleaning" in text or "housekeeping" in text:
        return ["cleaning material", "sanitation", "housekeeping supplies", "waste bin"]
    return ["retender", "corrigendum", "date extension", "rate contract"]


def build_report(rows: list[dict[str, Any]], records_analyzed: int) -> dict[str, Any]:
    return {
        "run_id": f"RUN-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-BUYER-REPEAT-{uuid.uuid4().hex[:6]}",
        "created_at": now_utc(),
        "records_analyzed": records_analyzed,
        "top_candidates_count": sum(1 for row in rows if row["buyer_repeat_score"] >= 55),
        "safety_boundary": "Internal buyer-repeat analysis only. No buyer outreach or external action executed.",
        "buyers": rows,
    }


def write_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"buyer_repeat_purchase_analysis_{today_compact()}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def maybe_append_event(report: dict[str, Any], path: Path, *, dry_run: bool, record_event: bool) -> None:
    if dry_run or not record_event:
        return
    append_event(
        "buyer.repeat_purchase_analyzed",
        "buyer_repeat_purchase_analyzer",
        object_type="buyer_repeat_purchase",
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
    parser = argparse.ArgumentParser(description="Analyze repeat buyers in local registers/source runs")
    parser.add_argument("--dry-run", action="store_true", help="Write local report only; do not append events")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--record-event", action="store_true")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    cases = load_csv(DATA_DIR / "master_cases.csv", "master_cases.example.csv")
    source_records = load_source_records()
    rows = analyze_repeat_buyers(
        cases,
        load_csv(DATA_DIR / "buyer_master.csv", "buyer_master.example.csv"),
        source_records,
        load_yaml_config(DEFAULT_CATEGORIES),
    )
    report = build_report(rows, len(cases) + len(source_records))
    path = write_report(report, Path(args.output_dir))
    maybe_append_event(report, path, dry_run=args.dry_run, record_event=args.record_event)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Buyer repeat purchase analysis: {path}")
        print("No external action was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
