#!/usr/bin/env python3
"""Backtest V5 forecast candidates against current local registers.

Default mode is dry-run. Use --write to update data/forecast_backtests.csv.
The script never mutates source registers and performs no external action.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
FORECAST_PATH = DATA_DIR / "forecast_candidates.csv"
OUTPUT_PATH = DATA_DIR / "forecast_backtests.csv"

COLUMNS = [
    "backtest_id",
    "forecast_id",
    "forecast_date",
    "review_date",
    "case_or_research_id",
    "forecast_type",
    "predicted_action",
    "observed_outcome",
    "outcome_label",
    "score_delta",
    "false_positive_reason",
    "false_negative_reason",
    "learning_note",
    "config_change_recommended",
    "created_at",
]

ADVANCED_STATUSES = {"DEEP_READ", "SUPPLIER_SEARCH", "PRICING_READY", "ARTIFACT_PRODUCTION", "APPROVAL_REQUIRED", "APPROVED"}
WEAK_EVIDENCE = {"", "MISSING", "RAW_LEAD", "PARTIAL", "MARKETPLACE_MASKED", "PUBLIC_LISTING_ONLY", "LOW_EVIDENCE", "RESEARCH_ONLY_NOT_RFQ"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def slugify(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "unknown"


def parse_date(value: Any) -> dt.date | None:
    text = str(value or "").strip()
    if not text:
        return None
    if re.fullmatch(r"\d{8}", text):
        text = f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        return None


def safe_float(value: Any) -> float:
    try:
        return float(str(value or "").replace(",", ""))
    except ValueError:
        return 0.0


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in COLUMNS})


def horizon_days(value: str) -> int:
    text = str(value or "").lower()
    if "0-7" in text:
        return 7
    if "7-30" in text:
        return 30
    if "30-60" in text:
        return 60
    if "60-90" in text or "30-90" in text:
        return 90
    return 30


def stronger_evidence(row: dict[str, str], forecast_evidence: str) -> bool:
    current = str(row.get("evidence_level") or row.get("rfq_stage") or row.get("evidence_status") or "").upper()
    if current in {"DOCUMENTS_DOWNLOADED", "DEEP_READ_COMPLETE", "RFQ_VERIFIED", "READY_FOR_SUPPLIER_PROOF"}:
        return current != forecast_evidence.upper()
    return False


def label_forecast(forecast: dict[str, str], case: dict[str, str] | None, review_date: dt.date) -> tuple[str, str, str, str]:
    forecast_date = parse_date(forecast.get("forecast_date")) or review_date
    elapsed = (review_date - forecast_date).days
    proof_gap = forecast.get("proof_gap", "")
    evidence = str(forecast.get("evidence_level", "")).upper()
    if case:
        status = str(case.get("status", "")).upper()
        kill_reason = case.get("kill_reason", "")
        if status in ADVANCED_STATUSES and stronger_evidence(case, evidence):
            return "HIT", f"Case advanced to {status} with stronger evidence.", "", ""
        if status == "REJECTED" and kill_reason:
            return "KILLED_CORRECTLY", f"Case rejected with kill reason: {kill_reason}", "", ""
        current_evidence = str(case.get("evidence_level") or "").upper()
        if evidence in WEAK_EVIDENCE or current_evidence in WEAK_EVIDENCE or "proof" in proof_gap.lower():
            return "BLOCKED_BY_PROOF", "Case remains constrained by missing RFQ/document/supplier proof.", "", ""
        if elapsed < horizon_days(forecast.get("horizon", "")):
            return "NOT_ENOUGH_TIME", f"Only {elapsed} day(s) elapsed within forecast horizon.", "", ""
        return "MISS", "No progress, proof gain, or justified kill after the forecast window.", "No observed progress after horizon.", ""

    if elapsed < horizon_days(forecast.get("horizon", "")):
        return "NOT_ENOUGH_TIME", f"Only {elapsed} day(s) elapsed; no source-register mutation expected.", "", ""
    if evidence in WEAK_EVIDENCE or "proof" in proof_gap.lower():
        return "BLOCKED_BY_PROOF", "Research or low-competition lead still lacks buyer-specific proof.", "", "No verified case emerged from the forecast lane."
    return "MISS", "No matching case or source-register progress found.", "No matching operational case found.", ""


def build_rows(forecasts: list[dict[str, str]], cases: list[dict[str, str]], review_date: dt.date) -> list[dict[str, str]]:
    case_by_id = {row.get("case_id", ""): row for row in cases}
    rows: list[dict[str, str]] = []
    for forecast in forecasts:
        forecast_id = forecast.get("forecast_id", "")
        forecast_digest = hashlib.sha1(forecast_id.encode("utf-8")).hexdigest()[:8]
        case_id = forecast.get("case_or_research_id", "")
        case = case_by_id.get(case_id)
        outcome, observed, false_positive, false_negative = label_forecast(forecast, case, review_date)
        forecast_date = parse_date(forecast.get("forecast_date")) or review_date
        rows.append(
            {
                "backtest_id": f"FBT-{review_date.strftime('%Y%m%d')}-{slugify(forecast_id)[:72]}-{forecast_digest}",
                "forecast_id": forecast_id,
                "forecast_date": forecast_date.isoformat(),
                "review_date": review_date.isoformat(),
                "case_or_research_id": case_id,
                "forecast_type": forecast.get("forecast_type", ""),
                "predicted_action": forecast.get("next_safe_action", ""),
                "observed_outcome": observed,
                "outcome_label": outcome,
                "score_delta": "0",
                "false_positive_reason": false_positive,
                "false_negative_reason": false_negative,
                "learning_note": "Keep row-level review; do not calculate precision/recall until enough mature forecasts exist.",
                "config_change_recommended": "FALSE",
                "created_at": review_date.isoformat(),
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backtest V5 demand forecast candidates")
    parser.add_argument("--forecast-csv", default=str(FORECAST_PATH), help="Forecast candidates CSV")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output backtest CSV")
    parser.add_argument("--review-date", default=dt.date.today().isoformat(), help="Review date YYYY-MM-DD")
    parser.add_argument("--write", action="store_true", help="Write forecast_backtests.csv")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args(argv)

    forecast_path = Path(args.forecast_csv)
    if not forecast_path.is_absolute():
        forecast_path = PROJECT_ROOT / forecast_path
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    review_date = parse_date(args.review_date) or dt.date.today()
    rows = build_rows(load_csv(forecast_path), load_csv(DATA_DIR / "master_cases.csv"), review_date)
    if args.write:
        write_csv(output, rows)
    summary = {
        "ok": True,
        "mode": "write" if args.write else "dry-run",
        "forecast_csv": rel(forecast_path),
        "output": rel(output),
        "rows": len(rows),
        "label_counts": {label: sum(1 for row in rows if row["outcome_label"] == label) for label in sorted({row["outcome_label"] for row in rows})},
        "safety_boundary": "Internal-only backtest. Source registers were not mutated.",
    }
    if args.json:
        print(json.dumps(summary | {"preview": rows[:10]}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
