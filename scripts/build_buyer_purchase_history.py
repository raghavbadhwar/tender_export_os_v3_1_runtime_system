#!/usr/bin/env python3
"""Build the V5 buyer repeat-purchase history projection.

Default mode is dry-run. Use --write to update data/buyer_purchase_history.csv.
The script reads local registers only and performs no external action.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "buyer_purchase_history.csv"

SAFETY_BOUNDARY = (
    "Internal-only buyer repeat-purchase projection. No buyer/supplier contact, "
    "portal login, bid/RFQ submission, payment, DSC use, final price, delivery, "
    "HSN/ITC-HS, origin, tax, legal, or compliance commitment executed."
)

COLUMNS = [
    "history_id",
    "buyer_name",
    "buyer_type",
    "department",
    "country_or_state",
    "workflow_type",
    "category_code",
    "category_name",
    "source_names",
    "past_case_count",
    "last_seen_date",
    "first_seen_date",
    "avg_estimated_value",
    "median_estimated_value",
    "avg_emd",
    "repeat_interval_days",
    "next_likely_window_start",
    "next_likely_window_end",
    "buyer_repeat_score",
    "evidence_level",
    "confidence",
    "notes",
    "created_at",
    "updated_at",
]

EVIDENCE_SCORE = {
    "RFQ_VERIFIED": 90,
    "DEEP_READ_COMPLETE": 78,
    "DOCUMENTS_DOWNLOADED": 75,
    "DOCUMENTS_DISCOVERED": 65,
    "SOURCE_DETAIL_CAPTURED": 60,
    "PUBLIC_LISTING_ONLY": 35,
    "MISSING": 10,
    "RAW_LEAD": 10,
    "": 0,
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def slugify(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "unknown"


def safe_float(value: Any) -> float:
    text = str(value or "").strip().replace(",", "").replace("₹", "").replace("$", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        return float(match.group(0)) if match else 0.0


def fmt_number(value: float | int | str) -> str:
    if value == "":
        return ""
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def parse_date(value: Any) -> dt.date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        return None


def date_text(value: dt.date | None) -> str:
    return value.isoformat() if value else ""


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


def input_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    production = DATA_DIR / "master_cases.csv"
    if production.exists():
        return production
    projection = PROJECT_ROOT / "outputs" / "projections" / "master_cases.csv"
    if projection.exists():
        return projection
    return DATA_DIR / "examples" / "master_cases.example.csv"


def best_evidence(rows: list[dict[str, str]]) -> str:
    best_label = ""
    best_score = -1
    for row in rows:
        for field in ("evidence_level", "rfq_stage", "evidence_status", "status"):
            label = str(row.get(field, "") or "").strip().upper()
            score = EVIDENCE_SCORE.get(label, -1)
            if score > best_score:
                best_label = label
                best_score = score
    return best_label


def workflow_type(rows: list[dict[str, str]]) -> str:
    values = {str(row.get("workflow_type", "")).strip().upper() for row in rows if row.get("workflow_type")}
    if len(values) > 1:
        return "MIXED"
    return next(iter(values), "GOV")


def category_code(category_name: str, workflow: str) -> str:
    prefix = "EXP" if workflow == "EXPORT" else "GOV" if workflow == "GOV" else "MIX"
    return f"{prefix}-{slugify(category_name).upper()[:40]}"


def observation_date(row: dict[str, str]) -> dt.date | None:
    """Return one observation date per case, never several lifecycle dates."""
    for field in ("created_at", "updated_at", "last_corrigenda_date", "deadline_date"):
        parsed = parse_date(row.get(field))
        if parsed:
            return parsed
    return None


def seen_dates(rows: list[dict[str, str]]) -> list[dt.date]:
    return sorted({date for row in rows if (date := observation_date(row)) is not None})


def distinct_case_count(rows: list[dict[str, str]]) -> int:
    keys = {
        str(row.get("case_id") or "").strip()
        or f"anonymous:{index}:{row.get('source_url', '')}:{row.get('opportunity_title', '')}"
        for index, row in enumerate(rows)
    }
    return len(keys)


def repeat_interval_days(dates: list[dt.date]) -> int | None:
    if len(dates) < 2:
        return None
    gaps = [(right - left).days for left, right in zip(dates, dates[1:]) if (right - left).days >= 0]
    if not gaps:
        return None
    return round(sum(gaps) / len(gaps))


def confidence(past_case_count: int, dates: list[dt.date]) -> str:
    if past_case_count >= 4 and len(dates) >= 2:
        return "HIGH"
    if past_case_count >= 2:
        return "MEDIUM"
    return "LOW"


def build_rows(cases: list[dict[str, str]], run_date: dt.date) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in cases:
        buyer = str(row.get("buyer_name", "") or "").strip()
        category = str(row.get("product_or_service", "") or row.get("opportunity_title", "") or "").strip()
        if not buyer or not category:
            continue
        grouped[(buyer.lower(), category.lower())].append(row)

    output: list[dict[str, str]] = []
    for (_, _), rows in grouped.items():
        first = rows[0]
        buyer = first.get("buyer_name", "")
        category = first.get("product_or_service") or first.get("opportunity_title") or "Unknown category"
        workflow = workflow_type(rows)
        case_count = distinct_case_count(rows)
        dates = seen_dates(rows)
        first_seen = dates[0] if dates else None
        last_seen = dates[-1] if dates else None
        values = [
            safe_float(row.get("estimated_value_inr") or row.get("estimated_value_usd"))
            for row in rows
            if safe_float(row.get("estimated_value_inr") or row.get("estimated_value_usd"))
        ]
        emds = [safe_float(row.get("emd_amount_inr")) for row in rows if safe_float(row.get("emd_amount_inr"))]
        interval = repeat_interval_days(dates)
        category_repeat_bonus = 20 if case_count >= 2 else 0
        recent_seen_bonus = 0
        if last_seen and (run_date - last_seen).days <= 60:
            recent_seen_bonus = 15
        repeat_score = min(100, case_count * 20 + category_repeat_bonus + recent_seen_bonus)
        window_start = last_seen + dt.timedelta(days=interval) if case_count >= 2 and last_seen and interval else None
        window_end = window_start + dt.timedelta(days=max(14, interval or 30)) if window_start else None
        country_or_state = (
            first.get("buyer_country")
            or first.get("state")
            or first.get("location")
            or first.get("delivery_location")
            or ""
        )
        row = {
            "history_id": f"BPH-{slugify(buyer)}-{slugify(category)}",
            "buyer_name": buyer,
            "buyer_type": first.get("buyer_type", ""),
            "department": first.get("department", ""),
            "country_or_state": country_or_state,
            "workflow_type": workflow,
            "category_code": category_code(category, workflow),
            "category_name": category,
            "source_names": "; ".join(sorted({r.get("source_name", "") for r in rows if r.get("source_name")})),
            "past_case_count": str(case_count),
            "last_seen_date": date_text(last_seen),
            "first_seen_date": date_text(first_seen),
            "avg_estimated_value": fmt_number(sum(values) / len(values)) if values else "",
            "median_estimated_value": fmt_number(median(values)) if values else "",
            "avg_emd": fmt_number(sum(emds) / len(emds)) if emds else "",
            "repeat_interval_days": str(interval) if interval is not None and case_count > 1 else "",
            "next_likely_window_start": date_text(window_start),
            "next_likely_window_end": date_text(window_end),
            "buyer_repeat_score": fmt_number(repeat_score),
            "evidence_level": best_evidence(rows),
            "confidence": confidence(case_count, dates),
            "notes": "Generated from local case registers; forecast only, not proof of future demand.",
            "created_at": run_date.isoformat(),
            "updated_at": run_date.isoformat(),
        }
        output.append(row)
    return sorted(output, key=lambda row: (float(row["buyer_repeat_score"]), row["buyer_name"]), reverse=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build buyer repeat-purchase history projection")
    parser.add_argument("--input-csv", help="Explicit master_cases-style CSV input")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output CSV path")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Run date YYYY-MM-DD")
    parser.add_argument("--write", action="store_true", help="Write projection CSV")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args(argv)

    run_date = parse_date(args.date) or dt.date.today()
    source = input_path(args.input_csv)
    rows = build_rows(load_csv(source), run_date)
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    if args.write:
        write_csv(output, rows)

    summary = {
        "ok": True,
        "mode": "write" if args.write else "dry-run",
        "source": rel(source),
        "output": rel(output),
        "rows": len(rows),
        "safety_boundary": SAFETY_BOUNDARY,
    }
    if args.json:
        print(json.dumps(summary | {"preview": rows[:10]}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
