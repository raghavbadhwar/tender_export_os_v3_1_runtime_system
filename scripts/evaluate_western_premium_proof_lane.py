#!/usr/bin/env python3
"""Evaluate Western Premium Proof Lane guardrails."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.quote_proof import strict_quote_proofs
except ModuleNotFoundError:  # pragma: no cover
    from quote_proof import strict_quote_proofs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_PATH = PROJECT_ROOT / "config" / "western_premium_proof_lane.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "western_premium_proof_lane"

TARGET_MARKETS = {"UK", "UNITED KINGDOM", "USA", "UNITED STATES", "CANADA", "GERMANY"}
TARGET_TERMS = {"HANDICRAFT", "HANDMADE", "ARTISAN", "TEXTILE", "DECOR", "DÉCOR", "GIFT", "BRASS", "HOME DECOR"}
SPICE_TERMS = {"SPICE", "SPICES", "TURMERIC", "PEPPER", "CHILLI", "CHILI", "CARDAMOM", "CUMIN", "CONDIMENT"}
FOOD_SAFETY_TERMS = {"FSSAI", "APEDA", "HACCP", "ISO 22000", "ORGANIC"}
FRAGILE_BULKY_TERMS = {"FRAGILE", "GLASS", "CERAMIC", "POTTERY", "STONE", "MARBLE", "FURNITURE", "BULKY", "LARGE", "BRASS", "DECOR", "DÉCOR"}
MIN_LANDED_MARGIN_PCT = 35.0


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


def norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def norm_upper(value: Any) -> str:
    return norm(value).upper()


def contains_any(text: str, terms: set[str]) -> bool:
    upper = norm_upper(text)
    return any(term in upper for term in terms)


def rfq_for_case(case_id: str, rfqs: list[dict[str, str]]) -> dict[str, str]:
    for rfq in rfqs:
        if rfq.get("case_id") == case_id:
            return rfq
    return {}


def suppliers_for_quotes(quotes: list[dict[str, str]], suppliers: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {row.get("supplier_id", ""): row for row in suppliers if row.get("supplier_id")}
    by_name = {norm_upper(row.get("supplier_name")): row for row in suppliers if row.get("supplier_name")}
    resolved = []
    for quote in quotes:
        supplier = by_id.get(quote.get("supplier_id", "")) or by_name.get(norm_upper(quote.get("supplier_name")))
        if supplier:
            resolved.append(supplier)
    return resolved


def certificate_blob(case: dict[str, str], suppliers: list[dict[str, str]]) -> str:
    parts = [
        case.get("mandatory_certs", ""),
        case.get("notes", ""),
    ]
    for supplier in suppliers:
        parts.extend([supplier.get("iso_certs", ""), supplier.get("other_certs", ""), supplier.get("notes", "")])
    return " ".join(parts)


def extract_margin_pct(case: dict[str, str]) -> float | None:
    text = " ".join(str(case.get(key, "")) for key in ("notes", "l1_sensitivity_summary", "typical_l1_price"))
    match = re.search(r"(?:landed_)?margin(?:_pct)?\s*[:=]\s*(\d+(?:\.\d+)?)", text, flags=re.I)
    return float(match.group(1)) if match else None


def is_lane_candidate(case: dict[str, str]) -> bool:
    market = norm_upper(case.get("buyer_country") or case.get("location") or case.get("state"))
    product = " ".join([case.get("product_or_service", ""), case.get("opportunity_title", ""), case.get("notes", "")])
    return market in TARGET_MARKETS and (contains_any(product, TARGET_TERMS) or contains_any(product, SPICE_TERMS))


def evaluate_case(
    case: dict[str, str],
    *,
    rfqs: list[dict[str, str]],
    quotes: list[dict[str, str]],
    suppliers: list[dict[str, str]],
) -> dict[str, Any]:
    case_id = case.get("case_id", "")
    rfq = rfq_for_case(case_id, rfqs)
    strict_quotes = strict_quote_proofs(case_id, quotes)
    quote_suppliers = suppliers_for_quotes(strict_quotes, suppliers)
    product_blob = " ".join([case.get("product_or_service", ""), case.get("opportunity_title", ""), case.get("notes", "")])
    cert_blob = certificate_blob(case, quote_suppliers)
    blockers: list[str] = []
    warnings: list[str] = []
    lane_stage = "PROOF_READY_FOR_INTERNAL_REVIEW"

    buyer_specific = rfq and rfq.get("evidence_status") == "RFQ_VERIFIED" and rfq.get("rfq_stage") in {"RFQ_VERIFIED", "READY_FOR_SUPPLIER_PROOF"}
    if not buyer_specific:
        blockers.append("no buyer-specific RFQ/source proof; keep as research lane only")
        lane_stage = "RESEARCH_LANE_ONLY"

    if not case.get("hsn_itchs_candidate") or not case.get("export_policy"):
        blockers.append("missing HS/HTS/ITC-HS tariff/export policy draft check; no quote")
        lane_stage = "BLOCKED_BEFORE_QUOTE" if lane_stage != "RESEARCH_LANE_ONLY" else lane_stage

    if contains_any(product_blob, SPICE_TERMS) and not contains_any(cert_blob, FOOD_SAFETY_TERMS):
        blockers.append("spices require food-safety docs before premium lane quote")
        lane_stage = "BLOCKED_BEFORE_QUOTE" if lane_stage != "RESEARCH_LANE_ONLY" else lane_stage

    if not strict_quotes:
        blockers.append("missing strict supplier-specific quote proof")
        lane_stage = "BLOCKED_BEFORE_BUYER_COMMITMENT" if lane_stage == "PROOF_READY_FOR_INTERNAL_REVIEW" else lane_stage

    packing_proof = any(quote.get("packaging_details") for quote in strict_quotes)
    provenance_or_cert = contains_any(cert_blob, {"CERT", "PROVENANCE", "ARTISAN", "HANDMADE", "GI", "ISO", "FSSAI", "APEDA"})
    if not packing_proof or not provenance_or_cert:
        blockers.append("missing supplier certificate/provenance/packing proof; no buyer commitment")
        lane_stage = "BLOCKED_BEFORE_BUYER_COMMITMENT" if lane_stage == "PROOF_READY_FOR_INTERNAL_REVIEW" else lane_stage

    if contains_any(product_blob, FRAGILE_BULKY_TERMS):
        freight_or_breakage = any(
            quote.get("packaging_details") and (quote.get("fob_price_usd") or quote.get("cif_price_usd") or quote.get("incoterms") or quote.get("delivery_terms"))
            for quote in strict_quotes
        )
        if not freight_or_breakage:
            blockers.append("fragile/bulky products require freight, packaging, and breakage proof")
            lane_stage = "BLOCKED_BEFORE_BUYER_COMMITMENT" if lane_stage == "PROOF_READY_FOR_INTERNAL_REVIEW" else lane_stage

    margin = extract_margin_pct(case)
    if margin is None:
        blockers.append(f"missing landed_margin_pct proof; minimum floor is {MIN_LANDED_MARGIN_PCT:g}%")
        lane_stage = "BLOCKED_BEFORE_QUOTE" if lane_stage == "PROOF_READY_FOR_INTERNAL_REVIEW" else lane_stage
    elif margin < MIN_LANDED_MARGIN_PCT:
        blockers.append(f"landed margin {margin:g}% below premium floor {MIN_LANDED_MARGIN_PCT:g}%")
        lane_stage = "BLOCKED_BEFORE_QUOTE" if lane_stage == "PROOF_READY_FOR_INTERNAL_REVIEW" else lane_stage

    if not is_lane_candidate(case):
        warnings.append("case is outside configured Western premium proof lane target markets/categories")

    return {
        "case_id": case_id,
        "workflow_type": case.get("workflow_type", ""),
        "buyer_country": case.get("buyer_country", ""),
        "product_or_service": case.get("product_or_service", ""),
        "lane_candidate": is_lane_candidate(case),
        "lane_stage": lane_stage,
        "strict_quote_proof_count": len(strict_quotes),
        "landed_margin_pct": margin,
        "blockers": sorted(dict.fromkeys(blockers)),
        "warnings": sorted(dict.fromkeys(warnings)),
        "external_actions_allowed": False,
    }


def build_report(cases: list[dict[str, str]], rfqs: list[dict[str, str]], quotes: list[dict[str, str]], suppliers: list[dict[str, str]], *, case_id: str = "", include_all: bool = False) -> dict[str, Any]:
    selected = [
        case for case in cases
        if (case_id and case.get("case_id") == case_id) or (include_all and is_lane_candidate(case))
    ]
    reviews = [evaluate_case(case, rfqs=rfqs, quotes=quotes, suppliers=suppliers) for case in selected]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "config": display_path(CONFIG_PATH),
        "minimum_landed_margin_pct": MIN_LANDED_MARGIN_PCT,
        "case_count": len(reviews),
        "blocked_or_research_count": sum(1 for row in reviews if row["lane_stage"] != "PROOF_READY_FOR_INTERNAL_REVIEW"),
        "reviews": reviews,
        "status": "PASS" if all(row["lane_stage"] == "PROOF_READY_FOR_INTERNAL_REVIEW" for row in reviews) else "BLOCKED",
        "safety_note": "Internal Western premium proof lane only. No external action or final commercial/compliance claim executed.",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Western Premium Proof Lane",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Status: **{report['status']}**",
        f"- Minimum landed margin: {report['minimum_landed_margin_pct']}%",
        "",
        report["safety_note"],
        "",
    ]
    for review in report["reviews"]:
        lines.extend([
            f"## {review['case_id']} — {review['lane_stage']}",
            f"- Product: {review['product_or_service']}",
            f"- Buyer country: {review['buyer_country']}",
            f"- Strict quote proofs: {review['strict_quote_proof_count']}",
            "",
        ])
        for blocker in review["blockers"]:
            lines.append(f"- BLOCKER: {blocker}")
        for warning in review["warnings"]:
            lines.append(f"- WARN: {warning}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Western premium proof lane guardrails")
    parser.add_argument("--case-id")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.case_id and not args.all:
        print("Provide --case-id or --all.")
        return 2

    report = build_report(
        load_csv(DATA_DIR / "master_cases.csv"),
        load_csv(DATA_DIR / "rfq_master.csv"),
        load_csv(DATA_DIR / "quote_master.csv"),
        load_csv(DATA_DIR / "supplier_master.csv"),
        case_id=args.case_id or "",
        include_all=args.all,
    )
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"western_premium_proof_lane_{stamp}.json"
    md_path = output_dir / f"western_premium_proof_lane_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, report)
    payload = {"status": report["status"], "json": display_path(json_path), "markdown": display_path(md_path)}
    print(json.dumps(payload, indent=2) if args.json else f"Western premium proof lane {report['status']}: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
