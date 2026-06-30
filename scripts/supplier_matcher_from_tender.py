#!/usr/bin/env python3
"""Create supplier-match candidates from a deep tender result without outreach."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event  # noqa: E402
from scripts.source_runtime.credential_policy import sanitize_payload  # noqa: E402
from scripts.source_runtime.evidence_store import safe_name  # noqa: E402

SUPPLIER_MASTER = PROJECT_ROOT / "data" / "supplier_master.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "supplier_matches"


def keywords(value: str) -> set[str]:
    return {word.lower() for word in re.findall(r"[A-Za-z0-9]{4,}", value or "")}


def score_supplier(row: dict[str, str], tender_terms: set[str]) -> tuple[int, list[str]]:
    text = " ".join(row.values()).lower()
    matched = sorted(term for term in tender_terms if term in text)
    base = min(60, len(matched) * 15)
    if row.get("blacklisted", "").upper() == "TRUE":
        return 0, ["BLACKLISTED"]
    risk_flags = []
    if row.get("watchlisted", "").upper() == "TRUE":
        risk_flags.append("WATCHLISTED")
    try:
        base += min(30, int(float(row.get("total_supplier_score", "0") or 0) / 4))
    except ValueError:
        pass
    if not row.get("gstin"):
        risk_flags.append("GST_NOT_LISTED")
    return min(100, base), risk_flags


def load_result(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "shallow" in data:
        return data
    for run in data.get("results", []):
        for result in run.get("deep_results", []):
            return result
    raise ValueError("No DeepSourceOpportunity result found")


def match_suppliers(result: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    extracted = result.get("extracted", {})
    terms = keywords(" ".join([extracted.get("product_or_service", ""), extracted.get("title", ""), json.dumps(extracted.get("boq_items", []))]))
    matches: list[dict[str, Any]] = []
    if SUPPLIER_MASTER.exists():
        with SUPPLIER_MASTER.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                score, risks = score_supplier(row, terms)
                if score <= 0:
                    continue
                matches.append(
                    {
                        "supplier_name": row.get("supplier_name", ""),
                        "source": row.get("source_platform") or row.get("source_type", "supplier_master"),
                        "location": ", ".join(part for part in [row.get("city", ""), row.get("state", ""), row.get("country", "")] if part),
                        "product_fit": score,
                        "contact_available": bool(row.get("phone") or row.get("email") or row.get("website")),
                        "quote_needed": True,
                        "gst_available": bool(row.get("gstin")),
                        "certification_available": bool(row.get("iso_certs") or row.get("other_certs")),
                        "estimated_price_range": row.get("last_quote_price", ""),
                        "minimum_order": " ".join(part for part in [row.get("min_order_qty", ""), row.get("min_order_unit", "")] if part),
                        "lead_time": row.get("lead_time_days", ""),
                        "reliability_score": row.get("total_supplier_score", ""),
                        "risk_flags": risks,
                    }
                )
    if not matches:
        product = extracted.get("product_or_service") or extracted.get("title") or "unknown product"
        for source in ["GeM sellers where visible", "IndiaMART manual/browser-visible", "TradeIndia manual/browser-visible", "Past awardees", "Google Maps/local clusters"]:
            matches.append(
                {
                    "supplier_name": f"Manual search needed: {product}",
                    "source": source,
                    "location": "",
                    "product_fit": 30,
                    "contact_available": False,
                    "quote_needed": True,
                    "gst_available": False,
                    "certification_available": False,
                    "estimated_price_range": "",
                    "minimum_order": "",
                    "lead_time": "",
                    "reliability_score": "",
                    "risk_flags": ["MANUAL_VERIFICATION_REQUIRED"],
                }
            )
    return sorted(matches, key=lambda item: int(item.get("product_fit", 0)), reverse=True)[:limit]


def write_report(result: dict[str, Any], matches: list[dict[str, Any]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ref = safe_name(result.get("shallow", {}).get("external_reference", "") or result.get("extracted", {}).get("title", "") or "candidate")
    path = OUTPUT_DIR / f"supplier_match_{ref}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    payload = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_candidate": result.get("shallow", {}),
        "supplier_candidates": matches,
        "approval_boundary": "No supplier outreach, quote request, PO, delivery commitment, price commitment, or payment executed.",
    }
    path.write_text(json.dumps(sanitize_payload(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Match suppliers from a deep tender result")
    parser.add_argument("--input", required=True, help="Deep source result JSON or source run JSON")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--record-event", action="store_true")
    args = parser.parse_args()
    result = load_result(Path(args.input))
    matches = match_suppliers(result, args.limit)
    path = write_report(result, matches)
    if args.record_event:
        append_event(
            "supplier.match_candidates_created",
            "supplier_matcher_from_tender",
            object_type="supplier",
            object_id=path.name,
            source=result.get("shallow", {}).get("source_name", "deep_source_runtime"),
            payload={"candidate_count": len(matches), "report": str(path.relative_to(PROJECT_ROOT))},
            citations=[str(path.relative_to(PROJECT_ROOT)), result.get("evidence_dir", "")],
        )
    print(f"Wrote supplier match report: {path}")
    print("No supplier outreach or commitment was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
