#!/usr/bin/env python3
"""Generate V5 Demand Forecasting + Low-Competition Engine report.

Read-only/internal report generator. It never sends messages, logs into portals,
submits bids/RFQs, pays money, uses DSC, commits final price, or makes final
HSN/ITC-HS/origin/legal/compliance claims.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "demand_forecasting"
LOW_COMP_DIR = PROJECT_ROOT / "outputs" / "low_competition_radar"
FORECAST_CANDIDATES_PATH = DATA_DIR / "forecast_candidates.csv"

SAFETY_BOUNDARY = (
    "Internal-only decision support. No buyer/supplier contact, portal login, "
    "bid/RFQ submission, payment, DSC use, final price, delivery, HSN/ITC-HS, "
    "origin, tax, legal, or compliance commitment executed."
)

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
TERMINAL_STATUSES = {"REJECTED", "WON", "LOST", "ARCHIVED", "SUBMITTED"}

WESTERN_MARKETS = {"UK", "USA", "CANADA", "GERMANY", "AUSTRALIA", "SWITZERLAND", "FRANCE", "NETHERLANDS"}
FAST_CASH_MARKETS = {"UAE", "OMAN", "SAUDI ARABIA", "QATAR", "KENYA", "TANZANIA", "SOUTH AFRICA", "SINGAPORE"}

PROOF_LEVEL_SCORE = {
    "RFQ_VERIFIED": 90,
    "READY_FOR_SUPPLIER_PROOF": 82,
    "DEEP_READ_COMPLETE": 78,
    "DOCUMENTS_DOWNLOADED": 75,
    "DOWNLOADED_DOCUMENTS": 75,
    "DOCUMENTS_DISCOVERED": 65,
    "SOURCE_DETAIL_CAPTURED": 60,
    "PUBLIC_LISTING_ONLY": 35,
    "BUYER_VISIBLE": 30,
    "PARTIAL": 25,
    "MARKETPLACE_MASKED": 20,
    "RAW_LEAD": 15,
    "MISSING": 10,
    "": 15,
}

FORECAST_CANDIDATE_COLUMNS = [
    "forecast_id",
    "run_id",
    "forecast_date",
    "horizon",
    "forecast_type",
    "case_or_research_id",
    "workflow_type",
    "buyer_or_market",
    "category_name",
    "product_or_service",
    "source_name",
    "source_url",
    "forecast_score",
    "confidence",
    "repeat_probability",
    "low_competition_score",
    "supplier_readiness_score",
    "evidence_level",
    "proof_gap",
    "next_safe_action",
    "approval_required_before_external_action",
    "kill_or_watch_reason",
    "created_at",
]

WEAK_EVIDENCE_LEVELS = {"", "PUBLIC_LISTING_ONLY", "RAW_LEAD", "MISSING", "PARTIAL", "MARKETPLACE_MASKED", "LOW_EVIDENCE", "RESEARCH_ONLY_NOT_RFQ", "UNKNOWN"}
EXTERNAL_ACTION_WORDS = {"send", "contact", "quote", "submit", "upload", "pay", "dsc", "commit", "invoice", "purchase order"}


def today_compact() -> str:
    return dt.date.today().strftime("%Y%m%d")


def now_ist_like() -> str:
    # Avoid external timezone dependency; current host time is sufficient for report metadata.
    return dt.datetime.now().replace(microsecond=0).isoformat()


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip().replace(",", "").replace("₹", "").replace("$", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        return float(match.group(0)) if match else default


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def slugify(value: Any) -> str:
    text = norm(value).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "unknown"


def date_for_csv(date_str: str) -> str:
    text = str(date_str or "").strip()
    if re.fullmatch(r"\d{8}", text):
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text[:10]


def as_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "yes", "y", "1", "approved", "done"}


def norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def norm_upper(value: Any) -> str:
    return norm(value).upper()


def is_fixture_like(row: dict[str, Any]) -> bool:
    case_id = norm_upper(row.get("case_id") or row.get("research_id"))
    blob = norm_upper(
        " ".join(
            str(row.get(key, ""))
            for key in ["buyer", "buyer_name", "title", "opportunity_title", "source", "source_name", "category_label", "category_name"]
        )
    )
    return case_id.startswith("MOCK-") or "FIXTURE" in blob


def internal_safe_action(action: Any, evidence_level: Any = "", proof_gap: Any = "") -> str:
    text = norm(action)
    evidence = norm_upper(evidence_level)
    gap = norm(proof_gap).lower()
    lower = text.lower()
    if evidence in WEAK_EVIDENCE_LEVELS or "proof" in gap or "document" in gap or any(word in lower for word in EXTERNAL_ACTION_WORDS):
        return "Capture/download or save local public tender/RFQ/source proof, then run deep-read/fast-kill before any external action."
    return text or "Review proof gaps internally before any external action."


def bool_text(value: Any) -> str:
    return "TRUE" if as_bool(value) else "FALSE"


def confidence(score: float, evidence_score: float = 0.0, source_count: int = 1) -> str:
    if score >= 80 and (evidence_score >= 60 or source_count >= 3):
        return "HIGH"
    if score >= 60:
        return "MEDIUM"
    return "LOW"


def forecast_horizon(days_to_deadline: float | None, research_only: bool = False) -> str:
    if research_only:
        return "30-90 days"
    if days_to_deadline is None:
        return "unknown"
    if days_to_deadline < 0:
        return "expired"
    if days_to_deadline <= 7:
        return "0-7 days"
    if days_to_deadline <= 30:
        return "7-30 days"
    if days_to_deadline <= 60:
        return "30-60 days"
    return "60-90 days"


def deadline_score(row: dict[str, Any]) -> tuple[float, str]:
    raw = str(row.get("days_to_deadline", "")).strip()
    if not raw:
        return 35.0, "deadline not captured"
    days = safe_float(raw, default=9999)
    if days < 0:
        return 0.0, "deadline passed"
    if days <= 2:
        return 25.0, "too close for safe preparation"
    if days <= 7:
        return 62.0, "urgent but possible only if proof already exists"
    if days <= 30:
        return 92.0, "good action window"
    if days <= 60:
        return 76.0, "medium action window"
    return 58.0, "longer horizon"


def evidence_score_from_case(row: dict[str, Any]) -> tuple[float, str]:
    candidates = [
        row.get("evidence_level", ""),
        row.get("rfq_stage", ""),
        row.get("evidence_status", ""),
        row.get("execution_sub_status", ""),
        row.get("status", ""),
    ]
    best = 0.0
    label = ""
    for value in candidates:
        key = norm_upper(value)
        if key in PROOF_LEVEL_SCORE and PROOF_LEVEL_SCORE[key] > best:
            best = PROOF_LEVEL_SCORE[key]
            label = key
    if as_bool(row.get("deep_read_done")):
        best = max(best, 70.0)
        label = label or "DEEP_READ_DONE"
    if row.get("source_url"):
        best = max(best, 35.0)
        label = label or "SOURCE_LINK"
    return best or 15.0, label or "LOW_EVIDENCE"


def supplier_readiness_score(row: dict[str, Any]) -> tuple[float, str]:
    status = norm_upper(row.get("status"))
    if as_bool(row.get("pricing_done")) or status in {"PRICING_READY", "ARTIFACT_PRODUCTION", "APPROVAL_REQUIRED"}:
        return 90.0, "pricing path started"
    if as_bool(row.get("supplier_search_done")) or status == "SUPPLIER_SEARCH":
        return 75.0, "supplier search/proof started"
    notes = norm_upper(row.get("notes"))
    if "SUPPLIER" in notes or "QUOTE" in notes:
        return 55.0, "supplier/quote mentioned but not proven"
    return 25.0, "supplier path not proven"


def repeat_pattern_score(row: dict[str, Any]) -> tuple[float, str]:
    buyer_repeat = safe_float(row.get("buyer_repeat_score"), 0.0)
    past_count = safe_float(row.get("past_tender_count"), 0.0)
    awards = safe_float(row.get("similar_category_awards"), 0.0)
    computed = clamp(max(buyer_repeat, min(100.0, past_count * 15.0 + awards * 20.0)))
    if computed >= 70:
        reason = "strong repeat buyer/category evidence"
    elif computed >= 35:
        reason = "some repeat signal"
    else:
        reason = "repeat signal not yet proven"
    return computed, reason


def source_reliability_from_row(row: dict[str, Any]) -> tuple[float, str]:
    source = norm_upper(row.get("source_name"))
    url = norm(row.get("source_url"))
    if "GEM" in source or "CPPP" in source or "UNDP" in source or "UNGM" in source:
        return 85.0, "institutional/public source"
    if url:
        return 60.0, "public source link exists"
    return 25.0, "source proof weak or missing"


def low_comp_signal_from_case(row: dict[str, Any]) -> tuple[float, str]:
    blob = " ".join(
        norm_upper(row.get(key))
        for key in [
            "opportunity_title",
            "product_or_service",
            "notes",
            "corrigenda_status",
            "corrigenda_summary",
            "payment_terms",
        ]
    )
    positives = {
        "RETENDER": 90,
        "RE-TENDER": 90,
        "CORRIGENDUM": 80,
        "DATE EXTENSION": 80,
        "SINGLE BID": 85,
        "SHORTFALL": 85,
        "AMC": 75,
        "ANNUAL MAINTENANCE": 75,
        "REPAIR": 70,
        "REPLACEMENT": 70,
        "REFILL": 68,
        "STATIONERY": 65,
        "CONSUMABLE": 65,
        "LINEN": 62,
        "TONER": 62,
        "CARTRIDGE": 62,
        "SCANNING": 65,
        "DIGIT": 65,
        "HOUSEKEEPING": 62,
    }
    best = 30.0
    hit = "no explicit low-competition signal"
    for keyword, value in positives.items():
        if keyword in blob and value > best:
            best = float(value)
            hit = keyword.lower()
    crowded = ["LAPTOP", "CCTV", "SOLAR", "MANPOWER", "CIVIL WORK", "SECURITY GUARD"]
    if any(keyword in blob for keyword in crowded):
        return max(0.0, best - 30.0), "crowded keyword penalty"
    return best, hit


def active_case_forecasts(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in cases:
        if is_fixture_like(row):
            continue
        status = norm_upper(row.get("status"))
        if status in TERMINAL_STATUSES:
            continue
        if status and status not in ACTIVE_STATUSES:
            # Preserve unknown active statuses but down-rank later.
            pass
        repeat_score, repeat_reason = repeat_pattern_score(row)
        source_score, source_reason = source_reliability_from_row(row)
        evidence_score, evidence_label = evidence_score_from_case(row)
        supplier_score, supplier_reason = supplier_readiness_score(row)
        deadline_component, deadline_reason = deadline_score(row)
        low_score, low_reason = low_comp_signal_from_case(row)
        forecast_score = clamp(
            repeat_score * 0.30
            + source_score * 0.20
            + evidence_score * 0.15
            + low_score * 0.15
            + supplier_score * 0.10
            + deadline_component * 0.10
        )
        days_raw = str(row.get("days_to_deadline", "")).strip()
        days = safe_float(days_raw) if days_raw else None
        proof_gap = []
        if evidence_score < 60:
            proof_gap.append("document/RFQ proof")
        if supplier_score < 70:
            proof_gap.append("supplier-specific proof")
        if not row.get("estimated_value_inr") and not row.get("estimated_value_usd"):
            proof_gap.append("value/quantity economics")
        if status in {"WATCHLIST", "NEW"}:
            next_action = "deep-read/fast-kill after document or RFQ proof is captured"
        elif status == "DEEP_READ":
            next_action = "finish deep-read and extract proof gaps"
        elif status == "SUPPLIER_SEARCH":
            next_action = "collect supplier-specific quote/certificate proof before pricing"
        else:
            next_action = "run critic-auditor gate before any external action"
        proof_gap_text = "; ".join(proof_gap) if proof_gap else "none obvious in current registers"
        next_action = internal_safe_action(next_action, evidence_label, proof_gap_text)
        rows.append(
            {
                "type": "active_case_forecast",
                "case_id": row.get("case_id", ""),
                "workflow_type": row.get("workflow_type", ""),
                "buyer": row.get("buyer_name", ""),
                "country_or_location": row.get("buyer_country") or row.get("location") or row.get("state") or "",
                "product_or_category": row.get("product_or_service", ""),
                "source": row.get("source_name", ""),
                "source_url": row.get("source_url", ""),
                "status": row.get("status", ""),
                "deadline": row.get("deadline_date", ""),
                "horizon": forecast_horizon(days),
                "forecast_score": round(forecast_score, 1),
                "confidence": confidence(forecast_score, evidence_score),
                "low_competition_signal": low_reason,
                "low_competition_signal_score": round(low_score, 1),
                "repeat_probability": round(repeat_score, 1),
                "supplier_readiness_score": round(supplier_score, 1),
                "repeat_signal": repeat_reason,
                "source_signal": source_reason,
                "evidence_label": evidence_label,
                "supplier_signal": supplier_reason,
                "deadline_signal": deadline_reason,
                "proof_gap": proof_gap_text,
                "next_safe_action": next_action,
                "approval_required_before_external_action": True,
            }
        )
    return sorted(rows, key=lambda item: item["forecast_score"], reverse=True)


def demand_research_forecasts(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if is_fixture_like(row):
            continue
        category = norm(row.get("category_name")) or "Unknown category"
        country = norm(row.get("country")) or "Unknown market"
        grouped[(category, country)].append(row)

    forecasts: list[dict[str, Any]] = []
    for (category, country), members in grouped.items():
        fit = sum(safe_float(row.get("market_fit_score")) for row in members) / max(1, len(members))
        reliability = sum(safe_float(row.get("source_reliability_score")) for row in members) / max(1, len(members))
        density = sum(safe_float(row.get("evidence_density_score")) for row in members) / max(1, len(members))
        tier_bonus = 0.0
        if any(row.get("source_tier") == "TIER_1_INSTITUTIONAL" for row in members):
            tier_bonus += 6.0
        if any(row.get("source_tier") == "TIER_5_STRATEGIC_ACCOUNT" for row in members):
            tier_bonus += 3.0
        score = clamp(fit * 0.45 + reliability * 0.25 + density * 0.20 + min(10, len(members) * 2) + tier_bonus)
        country_upper = norm_upper(country)
        if country_upper in WESTERN_MARKETS and "HANDICRAFT" in norm_upper(category):
            wedge = "Western Premium Proof Lane - primary wedge"
        elif country_upper in WESTERN_MARKETS and "SPICE" in norm_upper(category):
            wedge = "Western Premium Proof Lane - second wedge with food-safety docs"
        elif country_upper in FAST_CASH_MARKETS:
            wedge = "fast-cash export market lane"
        else:
            wedge = "research lane"
        best = sorted(
            members,
            key=lambda row: safe_float(row.get("market_fit_score"))
            + safe_float(row.get("source_reliability_score"))
            + safe_float(row.get("evidence_density_score")),
            reverse=True,
        )[0]
        proof_gap = "buyer-specific RFQ/source detail; supplier proof; pricing/compliance proof"
        forecasts.append(
            {
                "type": "demand_research_forecast",
                "case_id": best.get("research_id", ""),
                "workflow_type": "EXPORT_RESEARCH",
                "buyer": best.get("buyer_type", ""),
                "country_or_location": country,
                "product_or_category": category,
                "source": best.get("source_name", ""),
                "source_url": best.get("source_url", ""),
                "status": "RESEARCH_LANE",
                "deadline": "",
                "horizon": forecast_horizon(None, research_only=True),
                "forecast_score": round(score, 1),
                "confidence": confidence(score, density, len(members)),
                "low_competition_signal": wedge,
                "low_competition_signal_score": 0,
                "repeat_probability": 0,
                "supplier_readiness_score": 0,
                "repeat_signal": f"{len(members)} source/research row(s)",
                "source_signal": best.get("source_tier", ""),
                "evidence_label": "RESEARCH_ONLY_NOT_RFQ",
                "supplier_signal": "supplier proof not yet attached to research lane",
                "deadline_signal": "no case deadline until buyer-specific RFQ/tender exists",
                "proof_gap": proof_gap,
                "next_safe_action": internal_safe_action(best.get("recommended_next_action") or "scan for buyer-specific RFQ proof", "RESEARCH_ONLY_NOT_RFQ", proof_gap),
                "approval_required_before_external_action": True,
            }
        )
    return sorted(forecasts, key=lambda item: item["forecast_score"], reverse=True)


def latest_low_comp_json() -> Path | None:
    files = sorted(LOW_COMP_DIR.glob("low_competition_order_radar_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return files[0] if files else None


def low_competition_candidates(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    sections = data.get("sections", {})
    candidates = []
    for section_name in [
        "best_easy_to_capture_orders",
        "retenders_corrigenda_date_extensions",
        "repeat_buyers",
        "supplier_ready_categories",
        "low_emd_opportunities",
        "badly_titled_under_seen_opportunities",
    ]:
        for item in sections.get(section_name, []) or []:
            case_id = norm_upper(item.get("case_id"))
            if is_fixture_like(item):
                continue
            score = safe_float(item.get("low_competition_score"), 0.0)
            if not case_id and score <= 0:
                continue
            evidence = norm_upper(item.get("evidence_level"))
            proof_gap = "; ".join(item.get("missing_info") or []) or "confirm documents/RFQ/source proof"
            proof_gap = proof_gap.replace("manually uploaded", "saved locally").replace("manually upload", "save locally")
            not_bid_ready = evidence == "PUBLIC_LISTING_ONLY" or not item.get("bid_ready", False)
            next_action = internal_safe_action(
                item.get("recommended_next_action", "capture documents/source proof before bid-ready treatment"),
                evidence,
                proof_gap,
            )
            candidates.append(
                {
                    "type": "low_competition_candidate",
                    "case_id": item.get("case_id", ""),
                    "workflow_type": "LOW_COMP_RADAR",
                    "buyer": item.get("buyer", ""),
                    "country_or_location": "",
                    "product_or_category": item.get("category_label") or item.get("category") or item.get("title", ""),
                    "source": item.get("source", ""),
                    "source_url": item.get("source_url", ""),
                    "status": item.get("classification", ""),
                    "deadline": item.get("deadline", ""),
                    "horizon": "active order",
                    "forecast_score": round(score, 1),
                    "confidence": confidence(score, PROOF_LEVEL_SCORE.get(evidence, 35)),
                    "low_competition_signal": section_name.replace("_", " "),
                    "low_competition_signal_score": round(score, 1),
                    "repeat_probability": round(safe_float(item.get("repeat_buyer_score")), 1),
                    "supplier_readiness_score": round(safe_float(item.get("supplier_readiness_score")), 1),
                    "repeat_signal": f"repeat buyer score {item.get('repeat_buyer_score', 0)}",
                    "source_signal": item.get("source", ""),
                    "evidence_label": evidence or "UNKNOWN",
                    "supplier_signal": f"supplier readiness {item.get('supplier_readiness_score', 0)}",
                    "deadline_signal": item.get("deadline") or "deadline not captured",
                    "proof_gap": proof_gap,
                    "next_safe_action": next_action,
                    "approval_required_before_external_action": True,
                    "bid_ready": not not_bid_ready,
                    "why_this_is_easier": item.get("why_this_is_easier", []),
                    "risk_flags": item.get("risk_flags", []),
                }
            )
    unique: dict[str, dict[str, Any]] = {}
    for item in candidates:
        key = item["case_id"] or item["source_url"] or item["product_or_category"]
        if key not in unique or item["forecast_score"] > unique[key]["forecast_score"]:
            unique[key] = item
    return sorted(unique.values(), key=lambda item: item["forecast_score"], reverse=True)


def choose_recommended_actions(low_comp: list[dict[str, Any]], case_forecasts: list[dict[str, Any]], research: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in low_comp:
        if len(actions) >= 2:
            break
        if item.get("evidence_label") == "PUBLIC_LISTING_ONLY" or "document" in item.get("proof_gap", "").lower():
            action = "Capture/download or save local tender/RFQ documents, then deep-read/fast-kill."
        else:
            action = item.get("next_safe_action")
        actions.append({"source": "low competition", "case_or_lane": item.get("case_id"), "action": action, "reason": item.get("low_competition_signal")})
    if len(actions) < 3:
        for item in case_forecasts:
            if item.get("case_id") not in {action.get("case_or_lane") for action in actions}:
                actions.append({"source": "demand forecast", "case_or_lane": item.get("case_id"), "action": item.get("next_safe_action"), "reason": item.get("proof_gap")})
                break
    if len(actions) < 3 and research:
        item = research[0]
        actions.append({"source": "research forecast", "case_or_lane": item.get("case_id"), "action": item.get("next_safe_action"), "reason": item.get("product_or_category")})
    return actions[:3]


def buyer_repeat_predictions(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                "type": "buyer_repeat_prediction",
                "case_id": row.get("history_id", ""),
                "workflow_type": row.get("workflow_type", ""),
                "buyer": row.get("buyer_name", ""),
                "country_or_location": row.get("country_or_state", ""),
                "product_or_category": row.get("category_name", ""),
                "source": row.get("source_names", ""),
                "source_url": "",
                "status": "BUYER_REPEAT",
                "deadline": row.get("next_likely_window_start", ""),
                "horizon": f"{row.get('next_likely_window_start', '')} to {row.get('next_likely_window_end', '')}".strip(),
                "forecast_score": safe_float(row.get("buyer_repeat_score")),
                "confidence": row.get("confidence", "LOW"),
                "low_competition_signal": "repeat buyer/category prediction",
                "low_competition_signal_score": 0,
                "repeat_probability": safe_float(row.get("buyer_repeat_score")),
                "supplier_readiness_score": 0,
                "evidence_label": row.get("evidence_level", ""),
                "proof_gap": "future demand forecast only; specific tender/RFQ proof still required",
                "next_safe_action": "Monitor buyer/category window and capture source proof when a listing appears.",
                "approval_required_before_external_action": True,
            }
        )
    return sorted(output, key=lambda item: item["forecast_score"], reverse=True)


def category_demand_predictions(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                "type": "category_demand_prediction",
                "case_id": row.get("category_history_id", ""),
                "workflow_type": row.get("workflow_type", ""),
                "buyer": row.get("country_or_state", ""),
                "country_or_location": row.get("country_or_state", ""),
                "product_or_category": row.get("category_name", ""),
                "source": row.get("source_names", ""),
                "source_url": "",
                "status": row.get("trend_direction", ""),
                "deadline": row.get("last_seen_date", ""),
                "horizon": "category watch",
                "forecast_score": safe_float(row.get("demand_score")),
                "confidence": row.get("confidence", "LOW"),
                "low_competition_signal": row.get("trend_direction", ""),
                "low_competition_signal_score": safe_float(row.get("low_competition_fit_score")),
                "repeat_probability": 0,
                "supplier_readiness_score": safe_float(row.get("supplier_readiness_score")),
                "evidence_label": "CATEGORY_HISTORY",
                "proof_gap": "category forecast only; specific buyer/RFQ/document proof still required",
                "next_safe_action": row.get("recommended_next_action", ""),
                "approval_required_before_external_action": True,
            }
        )
    return sorted(output, key=lambda item: item["forecast_score"], reverse=True)


def killed_or_not_ready_rows(cases: list[dict[str, str]], forecasts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        if norm_upper(case.get("status")) == "REJECTED":
            rows.append(
                {
                    "case_id": case.get("case_id", ""),
                    "workflow_type": case.get("workflow_type", ""),
                    "forecast_score": "",
                    "confidence": "",
                    "product_or_category": case.get("product_or_service", ""),
                    "buyer": case.get("buyer_name", ""),
                    "evidence_label": case.get("evidence_level", ""),
                    "proof_gap": case.get("kill_reason", "rejected"),
                    "next_safe_action": "Keep rejected unless owner asks for changes or new proof arrives.",
                }
            )
    for row in forecasts:
        proof_gap = norm(row.get("proof_gap", ""))
        evidence = norm_upper(row.get("evidence_label", ""))
        if evidence in WEAK_EVIDENCE_LEVELS or ("proof" in proof_gap.lower() and "none obvious" not in proof_gap.lower()):
            rows.append(row)
    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row.get("case_id") or row.get("product_or_category")
        if key and key not in unique:
            unique[key] = row
    return list(unique.values())


def proof_gap_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "document_or_rfq_proof": 0,
        "supplier_specific_proof": 0,
        "buyer_specific_source_detail": 0,
        "economics_or_quantity": 0,
    }
    for row in rows:
        gap = norm(row.get("proof_gap")).lower()
        if "document" in gap or "rfq" in gap:
            summary["document_or_rfq_proof"] += 1
        if "supplier" in gap:
            summary["supplier_specific_proof"] += 1
        if "buyer-specific" in gap or "source detail" in gap:
            summary["buyer_specific_source_detail"] += 1
        if "value" in gap or "quantity" in gap or "economics" in gap:
            summary["economics_or_quantity"] += 1
    return summary


def compact_forecast_type(row_type: str) -> str:
    return {
        "active_case_forecast": "ACTIVE_CASE",
        "demand_research_forecast": "RESEARCH_LANE",
        "low_competition_candidate": "LOW_COMPETITION",
        "buyer_repeat_prediction": "BUYER_REPEAT",
        "category_demand_prediction": "CATEGORY_DEMAND",
    }.get(row_type, "ACTIVE_CASE")


def forecast_candidate_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_items = (
        list(payload.get("active_case_forecasts", []))
        + list(payload.get("research_forecasts", []))
        + list(payload.get("low_competition_candidates", []))
        + list(payload.get("buyer_repeat_predictions", []))
        + list(payload.get("category_demand_predictions", []))
    )
    forecast_date = date_for_csv(payload["date"])
    seen: set[tuple[str, str, str]] = set()
    for item in all_items:
        forecast_type = compact_forecast_type(item.get("type", ""))
        case_id = norm(item.get("case_id")) or slugify(item.get("product_or_category"))
        key = (payload["run_id"], case_id, forecast_type)
        if key in seen:
            continue
        seen.add(key)
        proof_gap = item.get("proof_gap", "")
        evidence = item.get("evidence_label", "")
        next_action = internal_safe_action(item.get("next_safe_action", ""), evidence, proof_gap)
        rows.append(
            {
                "forecast_id": f"FC-{payload['date']}-{forecast_type}-{slugify(case_id)[:80]}",
                "run_id": payload["run_id"],
                "forecast_date": forecast_date,
                "horizon": item.get("horizon", ""),
                "forecast_type": forecast_type,
                "case_or_research_id": case_id,
                "workflow_type": item.get("workflow_type", ""),
                "buyer_or_market": item.get("buyer") or item.get("country_or_location") or "",
                "category_name": item.get("product_or_category", ""),
                "product_or_service": item.get("product_or_category", ""),
                "source_name": item.get("source", ""),
                "source_url": item.get("source_url", ""),
                "forecast_score": item.get("forecast_score", ""),
                "confidence": item.get("confidence", "LOW"),
                "repeat_probability": item.get("repeat_probability", 0),
                "low_competition_score": item.get("low_competition_signal_score", 0),
                "supplier_readiness_score": item.get("supplier_readiness_score", 0),
                "evidence_level": evidence,
                "proof_gap": proof_gap,
                "next_safe_action": next_action,
                "approval_required_before_external_action": "TRUE",
                "kill_or_watch_reason": item.get("status", "") or proof_gap,
                "created_at": forecast_date,
            }
        )
    return rows


def write_forecast_candidates(path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = forecast_candidate_rows(payload)
    write_csv(path, rows, FORECAST_CANDIDATE_COLUMNS)
    return rows


def table_md(rows: list[dict[str, Any]], limit: int = 10) -> list[str]:
    lines = [
        "| Rank | Case/Lane | Type | Score | Confidence | Product/Category | Buyer/Market | Evidence | Proof gap | Next safe action |",
        "|---:|---|---|---:|---|---|---|---|---|---|",
    ]
    for rank, row in enumerate(rows[:limit], start=1):
        lines.append(
            "| {rank} | `{case}` | {typ} | {score} | {conf} | {product} | {buyer} | {evidence} | {gap} | {action} |".format(
                rank=rank,
                case=md_escape(row.get("case_id") or "research"),
                typ=md_escape(row.get("workflow_type", "")),
                score=row.get("forecast_score", ""),
                conf=md_escape(row.get("confidence", "")),
                product=md_escape(row.get("product_or_category", "")),
                buyer=md_escape(row.get("buyer") or row.get("country_or_location") or ""),
                evidence=md_escape(row.get("evidence_label", "")),
                gap=md_escape(row.get("proof_gap", "")),
                action=md_escape(row.get("next_safe_action", "")),
            )
        )
    return lines


def md_escape(value: Any) -> str:
    return str(value or "").replace("|", " /").replace("\n", " ")


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    best_action = payload["recommended_actions"][0] if payload["recommended_actions"] else {}
    lines: list[str] = [
        f"# V5 Demand Forecast + Low-Competition Brief — {payload['date']}",
        "",
        f"Safety: {SAFETY_BOUNDARY}",
        "",
        "## Founder snapshot",
        "Today's V5 engine found:",
        f"- {payload['summary']['active_cases_forecasted']} active forecasts",
        f"- {payload['summary']['low_competition_candidates']} low-competition candidates",
        f"- {payload['summary']['research_lanes_forecasted']} demand research lanes",
        f"- {payload['summary']['proof_required_candidates']} candidates requiring document/RFQ/source proof before action",
        f"- {payload['summary']['raw_lead_or_missing_buyer_proof_cases']} cases blocked by RAW_LEAD or missing buyer proof",
        f"- Latest low-competition radar: {payload['summary']['latest_low_competition_radar'] or 'not found'}",
        "",
        "Best internal move today: "
        + (
            f"{md_escape(best_action.get('case_or_lane'))} - {md_escape(best_action.get('action'))}"
            if best_action
            else "No safe internal action could be generated from current data."
        ),
        "",
        "## Recommended internal actions",
    ]
    for index, action in enumerate(payload["recommended_actions"], start=1):
        lines.append(f"{index}. **{md_escape(action['case_or_lane'])}** — {md_escape(action['action'])}  ")
        lines.append(f"   Reason: {md_escape(action['reason'])}")
    if not payload["recommended_actions"]:
        lines.append("No recommended action could be generated from current data.")

    lines.extend(["", "## Top active demand forecasts"])
    if payload["active_case_forecasts"]:
        lines.extend(table_md(payload["active_case_forecasts"], limit=10))
    else:
        lines.append("No active cases available for forecasting.")

    lines.extend(["", "## Top low-competition candidates"])
    if payload["low_competition_candidates"]:
        lines.extend(table_md(payload["low_competition_candidates"], limit=10))
    else:
        lines.append("No low-competition radar output found.")

    lines.extend(["", "## Top repeat-buyer/category predictions"])
    combined_predictions = sorted(
        payload["buyer_repeat_predictions"][:10] + payload["category_demand_predictions"][:10],
        key=lambda row: safe_float(row.get("forecast_score")),
        reverse=True,
    )
    if combined_predictions:
        lines.extend(table_md(combined_predictions, limit=10))
    else:
        lines.append("No buyer-repeat or category-demand projection rows found. Run the projection builders with --write.")

    lines.extend(["", "## Top export research lanes"])
    if payload["research_forecasts"]:
        lines.extend(table_md(payload["research_forecasts"], limit=10))
    else:
        lines.append("No demand research lanes found.")

    lines.extend(["", "## Killed/not-ready reasons"])
    if payload["killed_or_not_ready"]:
        lines.extend(table_md(payload["killed_or_not_ready"], limit=12))
    else:
        lines.append("No killed or not-ready rows found.")

    lines.extend(
        [
            "",
            "## Proof gaps",
            f"- Document/RFQ proof: {payload['proof_gap_summary']['document_or_rfq_proof']}",
            f"- Supplier-specific proof: {payload['proof_gap_summary']['supplier_specific_proof']}",
            f"- Buyer-specific source detail: {payload['proof_gap_summary']['buyer_specific_source_detail']}",
            f"- Value/quantity economics: {payload['proof_gap_summary']['economics_or_quantity']}",
        ]
    )

    lines.extend(["", "## Backtest/learning notes"])
    if payload["backtest_notes"]:
        for row in payload["backtest_notes"][:8]:
            lines.append(
                f"- `{md_escape(row.get('forecast_id'))}`: {md_escape(row.get('outcome_label'))} - {md_escape(row.get('learning_note') or row.get('observed_outcome'))}"
            )
    else:
        lines.append("No mature backtest rows yet. Run `python3 scripts/backtest_v5_demand_forecasts.py --write` after forecast candidates exist.")

    lines.extend(
        [
            "",
            "## Guardrails",
            "- Forecasts do not create bid-ready cases.",
            "- Public listing-only items remain leads until documents/RFQ/source detail are captured.",
            "- Supplier-specific quote proof is required before pricing-ready treatment.",
            "- Owner approval is required before any external supplier/buyer/portal/payment/DSC/final-price/compliance action.",
            "",
            "Recommended action: deep-read/prove the highest-scoring low-competition case whose proof gap is smallest.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    def rows_html(rows: list[dict[str, Any]], limit: int = 10) -> str:
        if not rows:
            return '<p class="muted">No rows.</p>'
        body = []
        for rank, row in enumerate(rows[:limit], start=1):
            body.append(
                f"<tr><td>{rank}</td><td>{esc(row.get('case_id'))}</td><td>{esc(row.get('workflow_type'))}</td>"
                f"<td>{esc(row.get('forecast_score'))}</td><td>{esc(row.get('confidence'))}</td>"
                f"<td>{esc(row.get('product_or_category'))}</td><td>{esc(row.get('buyer') or row.get('country_or_location'))}</td>"
                f"<td>{esc(row.get('evidence_label'))}</td><td>{esc(row.get('proof_gap'))}</td>"
                f"<td>{esc(row.get('next_safe_action'))}</td></tr>"
            )
        return "<table><thead><tr><th>#</th><th>Case/Lane</th><th>Type</th><th>Score</th><th>Confidence</th><th>Product/Category</th><th>Buyer/Market</th><th>Evidence</th><th>Proof gap</th><th>Next action</th></tr></thead><tbody>" + "\n".join(body) + "</tbody></table>"

    def proof_gap_html() -> str:
        summary = payload["proof_gap_summary"]
        return (
            "<ul>"
            f"<li>Document/RFQ proof: {esc(summary['document_or_rfq_proof'])}</li>"
            f"<li>Supplier-specific proof: {esc(summary['supplier_specific_proof'])}</li>"
            f"<li>Buyer-specific source detail: {esc(summary['buyer_specific_source_detail'])}</li>"
            f"<li>Value/quantity economics: {esc(summary['economics_or_quantity'])}</li>"
            "</ul>"
        )

    def backtest_html() -> str:
        rows = payload["backtest_notes"][:8]
        if not rows:
            return '<p class="muted">No mature backtest rows yet.</p>'
        return "<ul>" + "".join(
            f"<li><strong>{esc(row.get('forecast_id'))}</strong>: {esc(row.get('outcome_label'))} - {esc(row.get('learning_note') or row.get('observed_outcome'))}</li>"
            for row in rows
        ) + "</ul>"

    actions = "".join(
        f"<li><strong>{esc(action.get('case_or_lane'))}</strong> — {esc(action.get('action'))}<br><span class='muted'>Reason: {esc(action.get('reason'))}</span></li>"
        for action in payload["recommended_actions"]
    ) or "<li>No recommended action could be generated from current data.</li>"
    best_action = payload["recommended_actions"][0] if payload["recommended_actions"] else {}
    best_move = (
        f"{esc(best_action.get('case_or_lane'))} - {esc(best_action.get('action'))}"
        if best_action
        else "No safe internal action could be generated from current data."
    )
    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>V5 Demand Forecast {esc(payload['date'])}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
main {{ max-width: 1240px; margin: 0 auto; padding: 30px 20px; }}
h1 {{ margin-bottom: 4px; }}
.kicker, .muted {{ color: #64748b; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap: 12px; margin: 20px 0; }}
.card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; }}
table {{ border-collapse: collapse; width: 100%; background: white; border: 1px solid #e2e8f0; margin-bottom: 22px; }}
th, td {{ border-bottom: 1px solid #e2e8f0; padding: 8px 9px; text-align: left; vertical-align: top; font-size: 13px; }}
th {{ background: #eef2f7; }}
</style></head><body><main>
<p class="kicker">Internal-only decision support</p>
<h1>V5 Demand Forecast + Low-Competition Brief</h1>
<p class="muted">{esc(payload['date'])} · {esc(SAFETY_BOUNDARY)}</p>
<h2>Founder snapshot</h2>
<section class="summary">
  <div class="card"><strong>{payload['summary']['active_cases_forecasted']}</strong><br>active cases forecasted</div>
  <div class="card"><strong>{payload['summary']['research_lanes_forecasted']}</strong><br>demand research lanes</div>
  <div class="card"><strong>{payload['summary']['low_competition_candidates']}</strong><br>low-competition candidates</div>
  <div class="card"><strong>{payload['summary']['proof_required_candidates']}</strong><br>proof required before action</div>
  <div class="card"><strong>{payload['summary']['raw_lead_or_missing_buyer_proof_cases']}</strong><br>RAW_LEAD/missing buyer proof blockers</div>
</section>
<p><strong>Best internal move today:</strong> {best_move}</p>
<h2>Recommended internal actions</h2><ol>{actions}</ol>
<h2>Top active demand forecasts</h2>{rows_html(payload['active_case_forecasts'])}
<h2>Top low-competition candidates</h2>{rows_html(payload['low_competition_candidates'])}
<h2>Top repeat-buyer/category predictions</h2>{rows_html(sorted(payload['buyer_repeat_predictions'][:10] + payload['category_demand_predictions'][:10], key=lambda row: safe_float(row.get('forecast_score')), reverse=True))}
<h2>Top export research lanes</h2>{rows_html(payload['research_forecasts'])}
<h2>Killed/not-ready reasons</h2>{rows_html(payload['killed_or_not_ready'], limit=12)}
<h2>Proof gaps</h2>{proof_gap_html()}
<h2>Backtest/learning notes</h2>{backtest_html()}
<h2>Guardrails</h2>
<ul><li>Forecasts do not create bid-ready cases.</li><li>Public listing-only items remain leads until documents/RFQ/source detail are captured.</li><li>Supplier-specific quote proof is required before pricing-ready treatment.</li><li>Owner approval is required before any external action.</li></ul>
</main></body></html>"""
    path.write_text(html_doc, encoding="utf-8")


def build_payload(date_str: str) -> dict[str, Any]:
    cases = load_csv(DATA_DIR / "master_cases.csv")
    demand_rows = load_csv(DATA_DIR / "demand_research.csv")
    buyer_history = load_csv(DATA_DIR / "buyer_purchase_history.csv")
    category_history = load_csv(DATA_DIR / "category_demand_history.csv")
    backtests = load_csv(DATA_DIR / "forecast_backtests.csv")
    low_path = latest_low_comp_json()
    active = active_case_forecasts(cases)
    research = demand_research_forecasts(demand_rows)
    low_comp = low_competition_candidates(low_path)
    buyer_predictions = buyer_repeat_predictions(buyer_history)
    category_predictions = category_demand_predictions(category_history)
    forecast_rows = active + research + low_comp + buyer_predictions + category_predictions
    not_ready = killed_or_not_ready_rows(cases, forecast_rows)
    gaps = proof_gap_summary(forecast_rows)
    raw_or_missing = sum(
        1
        for row in forecast_rows
        if norm_upper(row.get("evidence_label")) in {"RAW_LEAD", "MISSING", "RESEARCH_ONLY_NOT_RFQ", "PUBLIC_LISTING_ONLY", "LOW_EVIDENCE", "UNKNOWN"}
    )
    payload = {
        "run_id": f"RUN-{date_str}-V5-DEMAND-LOWCOMP",
        "created_at": now_ist_like(),
        "date": date_str,
        "safety_boundary": SAFETY_BOUNDARY,
        "summary": {
            "active_cases_forecasted": len(active),
            "research_lanes_forecasted": len(research),
            "low_competition_candidates": len(low_comp),
            "buyer_repeat_predictions": len(buyer_predictions),
            "category_demand_predictions": len(category_predictions),
            "proof_required_candidates": sum(1 for row in forecast_rows if "proof" in norm(row.get("proof_gap")).lower() or norm_upper(row.get("evidence_label")) in WEAK_EVIDENCE_LEVELS),
            "raw_lead_or_missing_buyer_proof_cases": raw_or_missing,
            "latest_low_competition_radar": str(low_path.relative_to(PROJECT_ROOT)) if low_path else "",
        },
        "recommended_actions": choose_recommended_actions(low_comp, active, research),
        "active_case_forecasts": active[:25],
        "research_forecasts": research[:25],
        "low_competition_candidates": low_comp[:25],
        "buyer_repeat_predictions": buyer_predictions[:25],
        "category_demand_predictions": category_predictions[:25],
        "killed_or_not_ready": not_ready[:25],
        "proof_gap_summary": gaps,
        "backtest_notes": backtests[-25:],
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate V5 demand forecast + low-competition report")
    parser.add_argument("--date", default=today_compact(), help="Report date in YYYYMMDD format")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--write-candidates", action="store_true", help="Write data/forecast_candidates.csv projection")
    parser.add_argument("--candidates-output", default=str(FORECAST_CANDIDATES_PATH), help="Forecast candidates CSV path")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_payload(args.date)
    json_path = output_dir / f"v5_demand_forecast_low_competition_{args.date}.json"
    md_path = output_dir / f"v5_demand_forecast_low_competition_{args.date}.md"
    html_path = output_dir / f"v5_demand_forecast_low_competition_{args.date}.html"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, payload)
    write_html(html_path, payload)
    candidates_path = Path(args.candidates_output)
    if not candidates_path.is_absolute():
        candidates_path = PROJECT_ROOT / candidates_path
    candidate_rows = write_forecast_candidates(candidates_path, payload) if args.write_candidates else []

    print(json.dumps({
        "ok": True,
        "markdown": str(md_path.relative_to(PROJECT_ROOT)),
        "html": str(html_path.relative_to(PROJECT_ROOT)),
        "json": str(json_path.relative_to(PROJECT_ROOT)),
        "forecast_candidates": str(candidates_path.relative_to(PROJECT_ROOT)) if args.write_candidates else "",
        "forecast_candidates_written": len(candidate_rows),
        "summary": payload["summary"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
