#!/usr/bin/env python3
"""Build the V5 category demand history projection.

Default mode is dry-run. Use --write to update data/category_demand_history.csv.
The script reads local registers and reports only; it performs no external action.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
LOW_COMP_DIR = PROJECT_ROOT / "outputs" / "low_competition_radar"
OUTPUT_PATH = DATA_DIR / "category_demand_history.csv"

COLUMNS = [
    "category_history_id",
    "workflow_type",
    "category_code",
    "category_name",
    "country_or_state",
    "source_names",
    "total_signal_count",
    "active_case_count",
    "research_lane_count",
    "verified_rfq_count",
    "low_competition_count",
    "supplier_ready_count",
    "last_seen_date",
    "trend_direction",
    "demand_score",
    "low_competition_fit_score",
    "supplier_readiness_score",
    "confidence",
    "recommended_next_action",
    "created_at",
    "updated_at",
]

ACTIVE_STATUSES = {
    "NEW",
    "WATCHLIST",
    "DEEP_READ",
    "SUPPLIER_SEARCH",
    "PRICING_READY",
    "ARTIFACT_PRODUCTION",
    "APPROVAL_REQUIRED",
    "APPROVED",
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


def fmt_number(value: float | int) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}".rstrip("0").rstrip(".")


def parse_date(value: Any) -> dt.date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        return None


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


def latest_low_comp_json() -> Path | None:
    files = sorted(LOW_COMP_DIR.glob("low_competition_order_radar_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load_low_comp_sections(path: Path | None) -> dict[str, list[dict[str, Any]]]:
    if not path or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    sections = data.get("sections", {})
    return {key: value for key, value in sections.items() if isinstance(value, list)}


def category_code(category_name: str, workflow: str) -> str:
    prefix = "EXP" if workflow == "EXPORT" else "GOV" if workflow == "GOV" else "MIX"
    return f"{prefix}-{slugify(category_name).upper()[:40]}"


def normalize_category(value: Any) -> str:
    return str(value or "").strip() or "Unknown category"


def add_signal(bucket: dict[str, Any], source: str, seen_date: dt.date | None) -> None:
    if source:
        bucket["sources"].add(source)
    if seen_date and (bucket["last_seen"] is None or seen_date > bucket["last_seen"]):
        bucket["last_seen"] = seen_date


def key_for(workflow: str, category: str, country_or_state: str) -> tuple[str, str, str]:
    return (workflow or "MIXED", normalize_category(category), str(country_or_state or "").strip())


def build_rows(
    cases: list[dict[str, str]],
    demand_rows: list[dict[str, str]],
    rfq_rows: list[dict[str, str]],
    low_sections: dict[str, list[dict[str, Any]]],
    run_date: dt.date,
) -> list[dict[str, str]]:
    buckets: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "sources": set(),
            "last_seen": None,
            "active_case_count": 0,
            "research_lane_count": 0,
            "verified_rfq_count": 0,
            "low_competition_count": 0,
            "supplier_ready_count": 0,
            "score_total": 0.0,
            "low_score_total": 0.0,
            "supplier_score_total": 0.0,
        }
    )

    case_by_id = {row.get("case_id", ""): row for row in cases}
    for row in cases:
        status = str(row.get("status", "")).strip().upper()
        if status not in ACTIVE_STATUSES:
            continue
        workflow = str(row.get("workflow_type", "")).strip().upper() or "GOV"
        location = row.get("buyer_country") or row.get("state") or row.get("location") or ""
        key = key_for(workflow, row.get("product_or_service") or row.get("opportunity_title"), location)
        bucket = buckets[key]
        bucket["active_case_count"] += 1
        bucket["score_total"] += safe_float(row.get("score_gov") or row.get("score_export") or 50)
        add_signal(bucket, row.get("source_name", ""), parse_date(row.get("updated_at") or row.get("created_at")))

    for row in demand_rows:
        key = key_for("EXPORT", row.get("category_name"), row.get("country"))
        bucket = buckets[key]
        bucket["research_lane_count"] += 1
        bucket["score_total"] += safe_float(row.get("market_fit_score") or 50)
        add_signal(bucket, row.get("source_name", ""), parse_date(row.get("updated_at") or row.get("created_at")))

    for row in rfq_rows:
        if str(row.get("evidence_status", "")).upper() != "RFQ_VERIFIED" and str(row.get("rfq_stage", "")).upper() != "RFQ_VERIFIED":
            continue
        case = case_by_id.get(row.get("case_id", ""), {})
        workflow = case.get("workflow_type") or "EXPORT"
        location = row.get("buyer_country") or case.get("buyer_country") or case.get("state") or ""
        key = key_for(workflow, row.get("product_or_service") or case.get("product_or_service"), location)
        bucket = buckets[key]
        bucket["verified_rfq_count"] += 1
        bucket["score_total"] += safe_float(row.get("rfq_score") or 75)
        add_signal(bucket, row.get("source_name", ""), parse_date(row.get("updated_at") or row.get("created_at")))

    counted_low_comp: set[str] = set()
    for section_name, items in low_sections.items():
        if section_name == "supplier_ready_categories":
            for item in items:
                category = normalize_category(item.get("label") or item.get("category"))
                key = key_for("GOV", category, "")
                bucket = buckets[key]
                bucket["supplier_ready_count"] += 1 if safe_float(item.get("supplier_readiness_score")) >= 60 else 0
                bucket["supplier_score_total"] += safe_float(item.get("supplier_readiness_score"))
                add_signal(bucket, "supplier_ready_categories", run_date)
            continue
        for item in items:
            if not isinstance(item, dict) or "case_id" not in item:
                continue
            unique = item.get("case_id") or item.get("source_url") or item.get("title")
            if unique in counted_low_comp:
                continue
            counted_low_comp.add(str(unique))
            workflow = "EXPORT" if str(item.get("case_id", "")).startswith("EXP-") else "GOV"
            category = item.get("category_label") or item.get("category") or item.get("title")
            key = key_for(workflow, category, "")
            bucket = buckets[key]
            bucket["low_competition_count"] += 1
            bucket["low_score_total"] += safe_float(item.get("low_competition_score"))
            add_signal(bucket, item.get("source", ""), parse_date(item.get("deadline")) or run_date)

    rows: list[dict[str, str]] = []
    for (workflow, category, country_or_state), bucket in buckets.items():
        total = bucket["active_case_count"] + bucket["research_lane_count"] + bucket["verified_rfq_count"] + bucket["low_competition_count"]
        if total <= 0:
            continue
        sources = sorted(bucket["sources"])
        independent_sources = len(sources)
        if total >= 3 and independent_sources >= 2:
            trend = "RISING"
        elif total >= 2:
            trend = "STABLE"
        else:
            trend = "UNKNOWN"
        if total >= 4 and independent_sources >= 3:
            conf = "HIGH"
        elif total >= 2:
            conf = "MEDIUM"
        else:
            conf = "LOW"
        low_score = bucket["low_score_total"] / bucket["low_competition_count"] if bucket["low_competition_count"] else 0
        supplier_score = bucket["supplier_score_total"] / bucket["supplier_ready_count"] if bucket["supplier_ready_count"] else 0
        demand_score = min(100, (bucket["score_total"] / total) * 0.55 + min(30, total * 6) + min(15, independent_sources * 5))
        if bucket["verified_rfq_count"]:
            action = "Run proof-aware deep-read and supplier-proof checks; external action still requires approval."
        elif bucket["low_competition_count"]:
            action = "Capture tender/RFQ documents and source detail before bid-ready treatment."
        elif bucket["research_lane_count"]:
            action = "Search for buyer-specific RFQ/source proof; keep as research-only until verified."
        else:
            action = "Monitor for repeat listings and proof-bearing documents."
        rows.append(
            {
                "category_history_id": f"CDH-{workflow}-{slugify(category)}-{slugify(country_or_state)}",
                "workflow_type": workflow if workflow in {"GOV", "EXPORT"} else "MIXED",
                "category_code": category_code(category, workflow),
                "category_name": category,
                "country_or_state": country_or_state,
                "source_names": "; ".join(sources),
                "total_signal_count": str(total),
                "active_case_count": str(bucket["active_case_count"]),
                "research_lane_count": str(bucket["research_lane_count"]),
                "verified_rfq_count": str(bucket["verified_rfq_count"]),
                "low_competition_count": str(bucket["low_competition_count"]),
                "supplier_ready_count": str(bucket["supplier_ready_count"]),
                "last_seen_date": bucket["last_seen"].isoformat() if bucket["last_seen"] else "",
                "trend_direction": trend,
                "demand_score": fmt_number(demand_score),
                "low_competition_fit_score": fmt_number(low_score),
                "supplier_readiness_score": fmt_number(supplier_score),
                "confidence": conf,
                "recommended_next_action": action,
                "created_at": run_date.isoformat(),
                "updated_at": run_date.isoformat(),
            }
        )
    return sorted(rows, key=lambda row: (float(row["demand_score"]), int(row["total_signal_count"])), reverse=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build category demand history projection")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output CSV path")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Run date YYYY-MM-DD")
    parser.add_argument("--write", action="store_true", help="Write projection CSV")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args(argv)

    run_date = parse_date(args.date) or dt.date.today()
    low_path = latest_low_comp_json()
    rows = build_rows(
        load_csv(DATA_DIR / "master_cases.csv"),
        load_csv(DATA_DIR / "demand_research.csv"),
        load_csv(DATA_DIR / "rfq_master.csv"),
        load_low_comp_sections(low_path),
        run_date,
    )
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    if args.write:
        write_csv(output, rows)
    summary = {
        "ok": True,
        "mode": "write" if args.write else "dry-run",
        "output": rel(output),
        "rows": len(rows),
        "latest_low_competition_radar": rel(low_path) if low_path else "",
        "safety_boundary": "Internal-only category demand projection. No external action executed.",
    }
    if args.json:
        print(json.dumps(summary | {"preview": rows[:10]}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
