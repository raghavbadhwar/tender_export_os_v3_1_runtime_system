#!/usr/bin/env python3
"""Past-award and buyer recurrence intelligence helpers."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def analyze_past_awards(rows: list[dict], buyer: str, category: str) -> dict:
    buyer_rows = [row for row in rows if row.get("buyer_name", "").lower() == buyer.lower()]
    category_rows = [row for row in buyer_rows if category.lower() in row.get("category", row.get("product_or_service", "")).lower()]
    winners = Counter(row.get("winner", "") for row in category_rows if row.get("winner"))
    prices = [float(str(row.get("award_value_inr", "0")).replace(",", "") or 0) for row in category_rows if row.get("award_value_inr")]
    average = sum(prices) / len(prices) if prices else 0
    return {
        "buyer_repeat_score": min(100, len(buyer_rows) * 10 + len(category_rows) * 15),
        "past_tender_count": len(buyer_rows),
        "similar_category_awards": len(category_rows),
        "average_award_value": round(average, 2),
        "known_past_winners": [winner for winner, _ in winners.most_common(5)],
        "typical_l1_price": round(min(prices), 2) if prices else 0,
        "incumbent_risk": "high" if winners and winners.most_common(1)[0][1] >= 2 else "unknown",
        "possible_supplier_from_past_winner": winners.most_common(1)[0][0] if winners else "",
    }


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze past award intelligence")
    parser.add_argument("--input", required=True)
    parser.add_argument("--buyer", required=True)
    parser.add_argument("--category", required=True)
    args = parser.parse_args()
    path = Path(args.input)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    print(json.dumps(analyze_past_awards(load_csv(path), args.buyer, args.category), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
