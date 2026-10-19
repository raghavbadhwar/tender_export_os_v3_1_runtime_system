#!/usr/bin/env python3
"""Score suppliers from data/supplier_master.csv using v4 supplier factors."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPLIER_FILE = PROJECT_ROOT / "data" / "supplier_master.csv"


SCORE_FIELDS = [
    "identity_score",
    "product_fit_score",
    "capacity_score",
    "certificate_score",
    "quote_clarity_score",
    "response_speed_score",
    "export_tender_exp_score",
    "price_competitiveness_score",
    "payment_terms_score",
    "delivery_timeline_score",
    "on_time_history_score",
    "defect_history_score",
    "communication_score",
]


def load_suppliers() -> list[dict]:
    with SUPPLIER_FILE.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def score_supplier(row: dict) -> float:
    total = sum(safe_float(row.get(field, "")) for field in SCORE_FIELDS)
    if row.get("blacklisted", "").upper() == "TRUE":
        return 0.0
    if row.get("watchlisted", "").upper() == "TRUE":
        total *= 0.8
    return round(total, 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score suppliers")
    parser.add_argument("--supplier-id", help="Optional supplier_id filter")
    parser.add_argument("--top", type=int, default=10, help="Rows to print")
    args = parser.parse_args()

    suppliers = load_suppliers()
    if args.supplier_id:
        suppliers = [s for s in suppliers if s.get("supplier_id") == args.supplier_id]

    scored = []
    for supplier in suppliers:
        scored.append((score_supplier(supplier), supplier))
    scored.sort(key=lambda item: item[0], reverse=True)

    print("supplier_id,total_score,supplier_name,blacklisted,watchlisted,source_platform,products_supplied")
    for total, supplier in scored[: args.top]:
        print(
            f"{supplier.get('supplier_id')},{total},{supplier.get('supplier_name')},"
            f"{supplier.get('blacklisted')},{supplier.get('watchlisted')},"
            f"{supplier.get('source_platform')},{supplier.get('products_supplied')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
