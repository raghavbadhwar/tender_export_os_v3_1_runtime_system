#!/usr/bin/env python3
"""Detect retender, corrigendum, amendment, and date-extension signals."""

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
    DEFAULT_KEYWORDS,
    OUTPUT_DIR,
    cluster_hits,
    load_csv,
    load_source_records,
    load_yaml_config,
    now_utc,
    relative,
    source_record_to_case,
    text_blob,
    today_compact,
)


def classify_change(row: dict[str, Any], hits: list[str]) -> str:
    text = text_blob(row)
    if any("retender" in hit.lower() or "re-tender" in hit.lower() or "re tender" in hit.lower() for hit in hits):
        return "RETENDER"
    if "single bid" in text or "shortfall of bidders" in text:
        return "LOW_BIDDER_RECALL"
    if "date extension" in text or "extended bid date" in text or "technical bid extended" in text:
        return "DATE_EXTENSION"
    if "revised boq" in text or "boq revised" in text:
        return "REVISED_BOQ"
    if "amendment" in text:
        return "AMENDMENT"
    return "CORRIGENDUM"


def detect_retender_corrigenda_records(
    cases: list[dict[str, Any]],
    source_records: list[dict[str, Any]],
    keyword_config: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = list(cases)
    rows.extend(source_record_to_case(record, index) for index, record in enumerate(source_records))
    output = []
    for row in rows:
        hits = cluster_hits(row, keyword_config).get("retender_corrigenda", [])
        text = text_blob(row)
        has_structured_corrigendum = str(row.get("corrigenda_count", "")).strip() not in {"", "0"}
        if not hits and not has_structured_corrigendum:
            continue
        change_type = classify_change(row, hits)
        output.append(
            {
                "old_case_id": row.get("case_id", ""),
                "new_possible_case_or_source_url": row.get("source_url", ""),
                "buyer": row.get("buyer_name", ""),
                "old_deadline": row.get("old_deadline", "") or row.get("previous_deadline", ""),
                "new_deadline": row.get("deadline_date", ""),
                "change_type": change_type,
                "why_this_may_reduce_competition": reason_for_change(change_type, text),
                "what_to_recheck": [
                    "deadline",
                    "BOQ/specification changes",
                    "eligibility and OEM/manufacturer-only language",
                    "EMD/tender fee changes",
                    "supplier proof feasibility",
                ],
                "recommended_action": "Re-deep-read public documents and route internally; no upload, bid, payment, DSC, or external message without approval.",
                "matched_keywords": hits,
            }
        )
    return sorted(output, key=lambda item: (item["change_type"], item["old_case_id"]))


def reason_for_change(change_type: str, text: str) -> str:
    if change_type == "RETENDER":
        return "Retender/reissue signals can mean prior bidder pool was thin or requirements changed."
    if change_type == "LOW_BIDDER_RECALL":
        return "Single-bid/shortfall signal suggests competition may have been insufficient."
    if change_type == "DATE_EXTENSION":
        return "Date extension gives more time for evidence review and may be under-monitored by competitors."
    if change_type == "REVISED_BOQ":
        return "Revised BOQ can reset bidder assumptions and create a narrow recheck window."
    if "corrigendum" in text:
        return "Corrigendum-driven updates are often missed by simple keyword monitors."
    return "Amended procurement needs recheck and may be less crowded than fresh headline tenders."


def build_report(matches: list[dict[str, Any]], records_analyzed: int) -> dict[str, Any]:
    return {
        "run_id": f"RUN-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-RETENDER-{uuid.uuid4().hex[:6]}",
        "created_at": now_utc(),
        "records_analyzed": records_analyzed,
        "top_candidates_count": len(matches),
        "safety_boundary": "Internal-only watch. No portal bypass, bid, upload, payment, DSC, external message, or final commitment executed.",
        "matches": matches,
    }


def write_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"retender_corrigenda_watch_{today_compact()}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def maybe_append_event(report: dict[str, Any], path: Path, *, dry_run: bool, record_event: bool) -> None:
    if dry_run or not record_event:
        return
    append_event(
        "retender_corrigenda.watch_generated",
        "retender_corrigenda_watch",
        object_type="retender_corrigenda_watch",
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
    parser = argparse.ArgumentParser(description="Watch retender/corrigenda/date-extension signals")
    parser.add_argument("--dry-run", action="store_true", help="Write local report only; do not append events")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--record-event", action="store_true")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    cases = load_csv(DATA_DIR / "master_cases.csv", "master_cases.example.csv")
    source_records = load_source_records()
    matches = detect_retender_corrigenda_records(cases, source_records, load_yaml_config(DEFAULT_KEYWORDS))
    report = build_report(matches, len(cases) + len(source_records))
    path = write_report(report, Path(args.output_dir))
    maybe_append_event(report, path, dry_run=args.dry_run, record_event=args.record_event)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Retender/corrigenda watch report: {path}")
        print("No external action was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
