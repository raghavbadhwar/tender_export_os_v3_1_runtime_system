#!/usr/bin/env python3
"""Generate the internal Low-Competition Order Radar report.

This is a read-only/local-output capability. It never logs into portals, bypasses
access controls, sends messages, uploads documents, pays EMD, uses DSC, or commits
price/delivery/compliance positions.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event  # noqa: E402
from scripts.supplier_matcher_from_tender import is_quote_proof  # noqa: E402


DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "low_competition_radar"
TEMPLATE_FILE = PROJECT_ROOT / "templates" / "low_competition_order_report.html"

DEFAULT_KEYWORDS = CONFIG_DIR / "low_competition_keywords.yaml"
DEFAULT_CATEGORIES = CONFIG_DIR / "low_competition_categories.yaml"
DEFAULT_SCORING = CONFIG_DIR / "low_competition_scoring.yaml"

REPORT_SECTIONS = [
    ("executive_summary", "Executive summary"),
    ("best_easy_to_capture_orders", "Best easy-to-capture orders"),
    ("retenders_corrigenda_date_extensions", "Retenders / corrigenda / date extensions"),
    ("repeat_buyers", "Repeat buyers"),
    ("supplier_ready_categories", "Supplier-ready categories"),
    ("low_emd_opportunities", "Low EMD opportunities"),
    ("clear_boq_opportunities", "Clear BOQ opportunities"),
    ("badly_titled_under_seen_opportunities", "Badly titled / under-seen opportunities"),
    ("local_simple_delivery_opportunities", "Local/simple delivery opportunities"),
    ("avoid_list", "Avoid list"),
    ("next_owner_action", "Next owner action"),
]

PUBLIC_LISTING_ONLY = "PUBLIC_LISTING_ONLY"
DOCUMENT_EVIDENCE_LEVELS = {
    "DOWNLOADED_DOCUMENTS",
    "DOCUMENTS_DOWNLOADED",
    "MANUAL_UPLOAD",
    "MANUALLY_UPLOADED",
    "FULL_TENDER_DOCUMENTS",
    "EXTRACTED_DOCUMENT",
    "RFQ_VERIFIED",
}
BLOCKED_EVIDENCE_LEVELS = {
    "BLOCKED_LOGIN",
    "BLOCKED_CAPTCHA",
    "PAYWALLED",
    "LOGIN_REQUIRED",
    "DOCS_UNAVAILABLE",
}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def today_compact() -> str:
    return dt.date.today().strftime("%Y%m%d")


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def parse_scalar(value: str) -> Any:
    text = value.strip().strip("\"'")
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    if text.startswith("[") and text.endswith("]"):
        body = text[1:-1].strip()
        if not body:
            return []
        return [parse_scalar(item.strip()) for item in body.split(",")]
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def _strip_comment(line: str) -> str:
    in_quote = False
    quote = ""
    for index, char in enumerate(line):
        if char in {"'", '"'}:
            if not in_quote:
                in_quote = True
                quote = char
            elif quote == char:
                in_quote = False
        if char == "#" and not in_quote:
            return line[:index]
    return line


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the small YAML subset used by this repo's config files."""

    raw_lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = _strip_comment(raw).rstrip()
        if stripped.strip():
            raw_lines.append((len(stripped) - len(stripped.lstrip(" ")), stripped.strip()))

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    for index, (indent, line) in enumerate(raw_lines):
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"{path}:{index + 1}: list item without list parent")
            parent.append(parse_scalar(line[2:]))
            continue

        key, sep, raw_value = line.partition(":")
        if not sep:
            raise ValueError(f"{path}:{index + 1}: expected key: value")
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value:
            value: Any = parse_scalar(raw_value)
        else:
            next_line = raw_lines[index + 1] if index + 1 < len(raw_lines) else None
            value = [] if next_line and next_line[0] > indent and next_line[1].startswith("- ") else {}
        if isinstance(parent, dict):
            parent[key] = value
        else:
            parent.append({key: value})
        if isinstance(value, (dict, list)):
            stack.append((indent, value))
    return root


def load_yaml_config(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ModuleNotFoundError:
        return parse_simple_yaml(path)


def load_csv(path: Path, example_name: str | None = None) -> list[dict[str, str]]:
    actual = path
    if not actual.exists() and example_name:
        actual = DATA_DIR / "examples" / example_name
    if not actual.exists():
        return []
    with actual.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "yes", "y", "1", "required", "mandatory"}


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def text_blob(row: dict[str, Any], fields: list[str] | None = None) -> str:
    keys = fields or [
        "case_id",
        "source_name",
        "opportunity_title",
        "buyer_name",
        "product_or_service",
        "delivery_location",
        "location",
        "state",
        "notes",
        "corrigenda_status",
        "corrigenda_summary",
        "experience_details",
        "mandatory_certs",
    ]
    return normalize_text(" ".join(str(row.get(key, "")) for key in keys))


def keyword_hits(text: str, keywords: list[str]) -> list[str]:
    lower = normalize_text(text)
    hits = []
    for keyword in keywords:
        term = normalize_text(keyword)
        if not term:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lower):
            hits.append(keyword)
    return hits


def cluster_hits(row: dict[str, Any], keyword_config: dict[str, Any]) -> dict[str, list[str]]:
    clusters = keyword_config.get("clusters", {})
    blob = text_blob(row)
    return {
        name: keyword_hits(blob, [str(item) for item in config.get("keywords", [])])
        for name, config in clusters.items()
        if isinstance(config, dict)
    }


def load_source_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for pattern in ["outputs/source_runs/**/*.json", "outputs/evidence/**/*.json"]:
        for path in PROJECT_ROOT.glob(pattern):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            records.extend(_extract_json_records(payload, path))
    return records


def _extract_json_records(payload: Any, path: Path) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows: list[dict[str, Any]] = []
        for item in payload:
            rows.extend(_extract_json_records(item, path))
        return rows
    if not isinstance(payload, dict):
        return []
    rows: list[dict[str, Any]] = []
    for key in ["opportunities", "candidates", "cases", "records", "results"]:
        if isinstance(payload.get(key), list):
            for item in payload[key]:
                rows.extend(_extract_json_records(item, path))
    for key in ["shallow", "extracted", "source_candidate"]:
        if isinstance(payload.get(key), dict):
            merged = dict(payload.get(key) or {})
            if isinstance(payload.get("extracted"), dict):
                merged.update(payload["extracted"])
            merged.setdefault("_source_artifact", relative(path))
            rows.append(merged)
            break
    if not rows and any(key in payload for key in ["title", "opportunity_title", "source_url", "buyer_name"]):
        row = dict(payload)
        row.setdefault("_source_artifact", relative(path))
        rows.append(row)
    return rows


def source_record_to_case(record: dict[str, Any], index: int) -> dict[str, str]:
    title = record.get("opportunity_title") or record.get("title") or record.get("name") or "Untitled source record"
    source_url = record.get("source_url") or record.get("url") or record.get("detail_url") or ""
    case_id = record.get("case_id") or record.get("external_reference") or f"SRC-{index + 1:04d}"
    return {
        "case_id": str(case_id),
        "workflow_type": str(record.get("workflow_type") or "GOV"),
        "source_name": str(record.get("source_name") or record.get("source") or "source_run"),
        "source_url": str(source_url),
        "opportunity_title": str(title),
        "buyer_name": str(record.get("buyer_name") or record.get("buyer") or ""),
        "buyer_type": str(record.get("buyer_type") or ""),
        "product_or_service": str(record.get("product_or_service") or record.get("item") or title),
        "estimated_value_inr": str(record.get("estimated_value_inr") or record.get("estimated_value") or ""),
        "deadline_date": str(record.get("deadline_date") or record.get("deadline") or ""),
        "emd_amount_inr": str(record.get("emd_amount_inr") or record.get("emd") or ""),
        "oem_required": str(record.get("oem_required") or ""),
        "past_experience_required": str(record.get("past_experience_required") or ""),
        "turnover_required_inr": str(record.get("turnover_required_inr") or ""),
        "delivery_location": str(record.get("delivery_location") or record.get("location") or ""),
        "status": str(record.get("status") or "NEW"),
        "deep_read_done": str(record.get("deep_read_done") or "FALSE"),
        "evidence_level": str(record.get("evidence_level") or PUBLIC_LISTING_ONLY),
        "corrigenda_status": str(record.get("corrigenda_status") or ""),
        "corrigenda_summary": str(record.get("corrigenda_summary") or record.get("summary") or ""),
        "corrigenda_count": str(record.get("corrigenda_count") or ""),
        "notes": str(record.get("notes") or record.get("_source_artifact") or ""),
    }


def match_low_competition_category(row: dict[str, Any], categories_config: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    categories = categories_config.get("categories", {})
    blob = text_blob(row)
    best_category = ""
    best_score = 0
    for category_id, config in categories.items():
        keywords = [str(item) for item in config.get("keywords", [])]
        hits = keyword_hits(blob, keywords)
        if len(hits) > best_score:
            best_category = str(category_id)
            best_score = len(hits)
    if not best_category and categories:
        return "", {}
    return best_category, categories.get(best_category, {}) if best_category else {}


def quote_proof_count_for_supplier(supplier: dict[str, Any], quote_rows: list[dict[str, Any]]) -> int:
    count = 0
    explicit_count = int(safe_float(supplier.get("quote_proof_count"), 0))
    if explicit_count > 0 and supplier.get("last_quote_proof_path") and not as_bool(supplier.get("is_indicative_price_only")):
        count += explicit_count
    supplier_id = supplier.get("supplier_id", "")
    supplier_name = normalize_text(supplier.get("supplier_name", ""))
    for quote in quote_rows:
        same_supplier = quote.get("supplier_id") == supplier_id or normalize_text(quote.get("supplier_name", "")) == supplier_name
        if same_supplier and is_quote_proof(
            {
                "quote_proof_type": quote.get("quote_proof_type", ""),
                "quote_proof_path": quote.get("quote_proof_path", ""),
                "indicative_price_only": as_bool(quote.get("indicative_price_only")) or bool(str(quote.get("marketplace_listing_price", "")).strip()),
                "not_a_quote_warning": not as_bool(quote.get("supplier_specific_quote", "TRUE")),
            }
        ):
            count += 1
    return count


def supplier_matches_category(supplier: dict[str, Any], category_config: dict[str, Any]) -> bool:
    blob = normalize_text(" ".join(str(supplier.get(key, "")) for key in ["products_supplied", "notes", "source_platform", "source_type"]))
    label = normalize_text(category_config.get("label", ""))
    if label and any(part and part in blob for part in re.split(r"[/()]+", label)):
        return True
    return bool(keyword_hits(blob, [str(item) for item in category_config.get("keywords", [])]))


def build_supplier_readiness_by_category(
    suppliers: list[dict[str, Any]],
    quote_rows: list[dict[str, Any]],
    categories_config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    readiness: dict[str, dict[str, Any]] = {}
    for category_id, category_config in categories_config.get("categories", {}).items():
        matched = [supplier for supplier in suppliers if supplier_matches_category(supplier, category_config)]
        quote_count = sum(quote_proof_count_for_supplier(supplier, quote_rows) for supplier in matched)
        gem_count = sum(1 for supplier in matched if as_bool(supplier.get("gem_registered")))
        gst_count = sum(
            1
            for supplier in matched
            if supplier.get("gstin") or normalize_text(supplier.get("gst_verification_status")) in {"verified", "true", "valid"}
        )
        avg_credit = 0
        credit_values = [safe_float(supplier.get("credit_days_offered"), 0) for supplier in matched if supplier.get("credit_days_offered")]
        if credit_values:
            avg_credit = round(sum(credit_values) / len(credit_values), 1)
        score = min(100, len(matched) * 15 + quote_count * 15 + gem_count * 8 + gst_count * 8 + (10 if avg_credit else 0))
        readiness[str(category_id)] = {
            "category": str(category_id),
            "label": category_config.get("label", category_id),
            "number_of_suppliers": len(matched),
            "gem_registered_supplier_count": gem_count,
            "gst_verified_count": gst_count,
            "quote_proof_count": quote_count,
            "average_credit_days": avg_credit,
            "delivery_city_coverage": sorted({supplier.get("city", "") for supplier in matched if supplier.get("city")}),
            "supplier_readiness_score": score,
            "recommended_order_types": category_config.get("recommended_order_types", []),
            "missing_supplier_gaps": supplier_gap_notes(len(matched), quote_count, gem_count, gst_count),
        }
    return readiness


def supplier_gap_notes(supplier_count: int, quote_count: int, gem_count: int, gst_count: int) -> list[str]:
    gaps = []
    if supplier_count < 3:
        gaps.append("fewer than 3 mapped suppliers")
    if quote_count < 2:
        gaps.append("fewer than 2 supplier-specific quote proofs")
    if gem_count == 0:
        gaps.append("GeM registration not proven for matched suppliers")
    if gst_count == 0:
        gaps.append("GST/business verification missing")
    return gaps or ["none"]


def buyer_repeat_lookup(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        buyer = normalize_text(case.get("buyer_name", ""))
        if buyer:
            grouped.setdefault(buyer, []).append(case)
    lookup = {}
    for buyer, rows in grouped.items():
        count = len(rows)
        case_scores = [safe_float(row.get("buyer_repeat_score"), 0) for row in rows]
        score = max(case_scores) if case_scores else 0
        if count > 1:
            score = max(score, min(100, 35 + count * 15))
        lookup[buyer] = {"past_tender_count": count, "buyer_repeat_score": int(score)}
    return lookup


def low_emd(emd: float, value: float) -> bool:
    return emd > 0 and (emd <= 50000 or (value > 0 and emd / value <= 0.02))


def high_emd(emd: float, value: float) -> bool:
    return emd > 100000 or (value > 0 and emd / value > 0.05)


def days_to_deadline(row: dict[str, Any], today: dt.date | None = None) -> int | None:
    today = today or dt.date.today()
    raw = str(row.get("deadline_date", "")).strip()
    if not raw:
        return None
    try:
        return (dt.date.fromisoformat(raw[:10]) - today).days
    except ValueError:
        return None


def evidence_level(row: dict[str, Any]) -> str:
    return str(row.get("evidence_level") or "").strip().upper() or PUBLIC_LISTING_ONLY


def score_case(
    case: dict[str, Any],
    *,
    keyword_config: dict[str, Any],
    categories_config: dict[str, Any],
    scoring_config: dict[str, Any],
    supplier_readiness: dict[str, dict[str, Any]] | None = None,
    buyer_repeat: dict[str, dict[str, Any]] | None = None,
    today: dt.date | None = None,
) -> dict[str, Any]:
    scoring = scoring_config.get("score", {})
    positives = scoring.get("positive", {})
    negatives = scoring.get("negative", {})
    thresholds = scoring_config.get("thresholds", {})
    supplier_readiness = supplier_readiness or {}
    buyer_repeat = buyer_repeat or {}

    score = int(scoring.get("base", 50))
    why: list[str] = []
    risks: list[str] = []
    missing: list[str] = []
    hits = cluster_hits(case, keyword_config)
    category_id, category_config = match_low_competition_category(case, categories_config)
    category_summary = supplier_readiness.get(category_id, {})
    emd = safe_float(case.get("emd_amount_inr"))
    value = safe_float(case.get("estimated_value_inr"))
    blob = text_blob(case)
    deadline_days = days_to_deadline(case, today=today)
    evidence = evidence_level(case)

    def add_positive(key: str, reason: str) -> None:
        nonlocal score
        score += int(positives.get(key, 0))
        why.append(reason)

    def add_negative(key: str, reason: str) -> None:
        nonlocal score
        score += int(negatives.get(key, 0))
        risks.append(reason)

    retender_hits = hits.get("retender_corrigenda", [])
    if retender_hits or safe_float(case.get("corrigenda_count"), 0) > 0:
        add_positive("retender_or_corrigendum", "retender/corrigendum signal may reduce active bidder attention")
    if keyword_hits(blob, ["date extension", "extended bid date", "deadline extended", "technical bid extended"]):
        add_positive("deadline_extended", "deadline/date extension signal gives more recheck time")

    buyer_info = buyer_repeat.get(normalize_text(case.get("buyer_name", "")), {})
    repeat_score = int(max(safe_float(case.get("buyer_repeat_score"), 0), safe_float(buyer_info.get("buyer_repeat_score"), 0)))
    past_tender_count = int(max(safe_float(case.get("past_tender_count"), 0), safe_float(buyer_info.get("past_tender_count"), 0)))
    if repeat_score >= 55 or past_tender_count > 1:
        add_positive("repeat_buyer", "buyer appears to make repeated purchases in similar categories")

    supplier_score = int(safe_float(category_summary.get("supplier_readiness_score"), 0))
    supplier_evidence_gap = False
    if supplier_score >= 60:
        add_positive("supplier_already_available", "mapped supplier base is already available for this category")
    elif category_id:
        supplier_evidence_gap = True
        missing.append("supplier readiness needs at least 2 quote proofs before pricing")

    if keyword_hits(blob, ["local delivery", "local purchase", "nearby", "same city"]) or (
        case.get("delivery_location") and "multiple" not in normalize_text(case.get("delivery_location"))
    ):
        add_positive("local_delivery", "delivery appears local/simple enough for internal review")
    if low_emd(emd, value):
        add_positive("low_emd", "EMD appears low relative to beginner-friendly order capture")
    if as_bool(case.get("deep_read_done")) or keyword_hits(blob, ["boq", "schedule of quantities", "item list", "revised boq"]):
        add_positive("clear_boq", "BOQ/specification signal appears visible")
    if safe_float(category_config.get("beginner_friendly_score"), 0) >= 75:
        add_positive("category_beginner_friendly", "category is marked beginner-friendly in low-competition config")
    if evidence in DOCUMENT_EVIDENCE_LEVELS:
        add_positive("public_documents_available", "public documents or manual evidence are available")
    else:
        missing.append("tender/RFQ documents must be downloaded or manually uploaded before bid-ready review")
    if not as_bool(case.get("oem_required")) and not keyword_hits(blob, ["oem required", "oem authorization mandatory", "oem only"]):
        add_positive("no_oem_requirement_visible", "no OEM-only requirement is visible in current evidence")
    if not as_bool(case.get("past_experience_required")) and not keyword_hits(blob, ["past experience required", "similar work experience", "experience certificate"]):
        add_positive("no_past_experience_visible", "no hard past-experience requirement is visible in current evidence")
    turnover = safe_float(case.get("turnover_required_inr"))
    if turnover <= 0:
        add_positive("no_high_turnover_visible", "no high-turnover requirement is visible in current evidence")

    if hits.get("crowded_watch_keywords"):
        add_negative("obvious_crowded_keyword", "crowded keyword signal needs caution")
    if high_emd(emd, value):
        add_negative("high_emd", "EMD appears high or disproportionate")
    if as_bool(case.get("oem_required")) or keyword_hits(blob, ["oem required", "oem authorization mandatory", "oem authorization"]):
        add_negative("oem_required", "OEM authorization requirement visible")
    if as_bool(case.get("past_experience_required")) or keyword_hits(blob, ["past experience required", "similar work experience", "experience certificate"]):
        add_negative("past_experience_required", "past-experience requirement visible")
    manufacturer_only = bool(keyword_hits(blob, ["manufacturer only", "manufacturer-only", "oem only", "authorized manufacturer", "authorised manufacturer"]))
    if manufacturer_only:
        add_negative("manufacturer_only", "manufacturer-only/OEM-only language visible")
    if deadline_days is not None and 0 <= deadline_days <= 5:
        add_negative("short_deadline", "deadline is too close for safe evidence/supplier proof")
    if keyword_hits(blob, ["remote delivery", "multiple locations", "all india delivery", "pan india", "hard-to-reach"]):
        add_negative("remote_delivery", "delivery appears remote or multi-location")
    if turnover >= 5_000_000 or keyword_hits(blob, ["high turnover", "annual turnover", "turnover certificate"]):
        add_negative("high_turnover", "turnover requirement may be high")
    if evidence == PUBLIC_LISTING_ONLY or keyword_hits(blob, ["boq not available", "documents not available", "unclear boq"]):
        add_negative("unclear_boq", "public listing-only or unclear BOQ; not bid-ready")
    if evidence in BLOCKED_EVIDENCE_LEVELS or keyword_hits(blob, ["login required", "captcha", "paywalled"]):
        add_negative("login_blocked_no_docs", "documents are blocked/unavailable without manual authorized access")
    if as_bool(case.get("scomet_flag")) or keyword_hits(blob, ["scomet", "restricted item", "hazardous", "drug license", "medical-grade"]):
        add_negative("compliance_heavy", "compliance-heavy signal requires specialist stop/review")

    score = max(0, min(100, score))
    avoid_threshold = int(thresholds.get("avoid", 40))
    watch_threshold = int(thresholds.get("watchlist", 55))
    easy_threshold = int(thresholds.get("easy_capture", 75))
    if manufacturer_only:
        score = min(score, avoid_threshold - 1)
    elif any("OEM authorization" in risk or "past-experience" in risk or "turnover" in risk for risk in risks):
        score = min(score, easy_threshold - 1)
    elif supplier_evidence_gap:
        score = min(score, easy_threshold - 1)

    if score >= easy_threshold:
        classification = "EASY_CAPTURE"
    elif score >= watch_threshold:
        classification = "WATCHLIST"
    else:
        classification = "AVOID"

    bid_ready = evidence in DOCUMENT_EVIDENCE_LEVELS and classification != "AVOID" and not manufacturer_only
    if not bid_ready and evidence == PUBLIC_LISTING_ONLY:
        recommended_action = "Keep as lead; download or manually upload public tender/RFQ documents before deep-read or bid-ready treatment."
    elif classification == "EASY_CAPTURE":
        recommended_action = "Route to Deep Read/Supplier Engine for internal evidence review; create approval card before any external action."
    elif classification == "WATCHLIST":
        recommended_action = "Watchlist and recheck hard-kill requirements, BOQ clarity, supplier proof, and approval gates."
    else:
        recommended_action = "Avoid or hold until hard blockers are disproven with public evidence."

    return {
        "case_id": case.get("case_id", ""),
        "source": case.get("source_name", ""),
        "source_url": case.get("source_url", ""),
        "buyer": case.get("buyer_name", ""),
        "title": case.get("opportunity_title", ""),
        "category": category_id or case.get("product_or_service", ""),
        "category_label": category_config.get("label", category_id or case.get("product_or_service", "")),
        "deadline": case.get("deadline_date", ""),
        "estimated_value": case.get("estimated_value_inr") or case.get("estimated_value_usd", ""),
        "EMD": case.get("emd_amount_inr", ""),
        "evidence_level": evidence,
        "repeat_buyer_score": repeat_score,
        "supplier_readiness_score": supplier_score,
        "low_competition_score": score,
        "classification": classification,
        "bid_ready": bid_ready,
        "why_this_is_easier": why or ["no low-competition positive signal strong enough yet"],
        "fulfilment_route": fulfilment_route(category_id, category_summary),
        "risk_flags": risks or ["none"],
        "missing_info": sorted(set(missing)) if missing else ["none"],
        "recommended_next_action": recommended_action,
        "approval_required_before_external_action": True,
        "keyword_hits": {cluster: values for cluster, values in hits.items() if values},
    }


def fulfilment_route(category_id: str, category_summary: dict[str, Any]) -> str:
    if not category_id:
        return "Manual category fit review required before supplier routing."
    suppliers = category_summary.get("number_of_suppliers", 0)
    quote_proofs = category_summary.get("quote_proof_count", 0)
    if suppliers and quote_proofs >= 2:
        return f"{category_id}: use mapped suppliers; quote proof exists for internal pricing review."
    if suppliers:
        return f"{category_id}: mapped suppliers exist; collect supplier-specific quote proofs before pricing."
    return f"{category_id}: source suppliers first; marketplace listing prices are not quote proof."


def report_summary(cards: list[dict[str, Any]], supplier_readiness: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "records_analyzed": len(cards),
        "easy_capture_count": sum(1 for card in cards if card["classification"] == "EASY_CAPTURE"),
        "watchlist_count": sum(1 for card in cards if card["classification"] == "WATCHLIST"),
        "avoid_count": sum(1 for card in cards if card["classification"] == "AVOID"),
        "supplier_ready_category_count": sum(1 for row in supplier_readiness.values() if row["supplier_readiness_score"] >= 60),
    }


def generate_report(
    cases: list[dict[str, Any]],
    suppliers: list[dict[str, Any]],
    quotes: list[dict[str, Any]],
    *,
    keyword_config: dict[str, Any],
    categories_config: dict[str, Any],
    scoring_config: dict[str, Any],
    include_source_runs: bool = True,
) -> dict[str, Any]:
    all_cases = list(cases)
    if include_source_runs:
        for index, record in enumerate(load_source_records()):
            all_cases.append(source_record_to_case(record, index))
    supplier_readiness = build_supplier_readiness_by_category(suppliers, quotes, categories_config)
    repeat_lookup = buyer_repeat_lookup(all_cases)
    cards = [
        score_case(
            case,
            keyword_config=keyword_config,
            categories_config=categories_config,
            scoring_config=scoring_config,
            supplier_readiness=supplier_readiness,
            buyer_repeat=repeat_lookup,
        )
        for case in all_cases
    ]
    cards = sorted(cards, key=lambda item: item["low_competition_score"], reverse=True)
    summary = report_summary(cards, supplier_readiness)

    def select(predicate, limit=10):
        return [card for card in cards if predicate(card)][:limit]

    easy = select(lambda card: card["classification"] == "EASY_CAPTURE", 8)
    return {
        "run_id": f"RUN-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-LOWCOMP-{uuid.uuid4().hex[:6]}",
        "created_at": now_utc(),
        "safety_boundary": "Internal-only local analysis. No external send, upload, bid, payment, DSC, final price, delivery commitment, HSN/ITC-HS, origin, tax, or legal certification executed.",
        "summary": summary,
        "sections": {
            "executive_summary": [
                {
                    "records_analyzed": summary["records_analyzed"],
                    "top_candidates_count": len(easy),
                    "note": "Public listing-only rows remain leads until documents are downloaded or manually uploaded.",
                }
            ],
            "best_easy_to_capture_orders": easy,
            "retenders_corrigenda_date_extensions": select(
                lambda card: bool(card["keyword_hits"].get("retender_corrigenda")) or "corrigendum" in " ".join(card["why_this_is_easier"]).lower()
            ),
            "repeat_buyers": select(lambda card: card["repeat_buyer_score"] >= 55),
            "supplier_ready_categories": sorted(supplier_readiness.values(), key=lambda row: row["supplier_readiness_score"], reverse=True)[:12],
            "low_emd_opportunities": select(lambda card: "EMD appears low" in " ".join(card["why_this_is_easier"])),
            "clear_boq_opportunities": select(lambda card: "BOQ" in " ".join(card["why_this_is_easier"])),
            "badly_titled_under_seen_opportunities": select(
                lambda card: any(cluster in card["keyword_hits"] for cluster in ["badly_titled_operational", "maintenance_amc", "record_digitisation"])
            ),
            "local_simple_delivery_opportunities": select(lambda card: "delivery appears local" in " ".join(card["why_this_is_easier"])),
            "avoid_list": select(lambda card: card["classification"] == "AVOID", 12),
            "next_owner_action": [
                {
                    "recommended_action": next_owner_action(easy, cards),
                    "approval_boundary": "Approval is required before any supplier/buyer message, quotation, upload, submission, payment, DSC, final compliance claim, price, or delivery commitment.",
                }
            ],
        },
        "opportunity_cards": cards,
    }


def next_owner_action(easy: list[dict[str, Any]], cards: list[dict[str, Any]]) -> str:
    if easy:
        first = easy[0]
        return f"Deep-read {first['case_id']} and verify supplier quote proof before creating any approval card."
    watch = next((card for card in cards if card["classification"] == "WATCHLIST"), None)
    if watch:
        return f"Recheck missing evidence for watchlist lead {watch['case_id']}; keep it internal until documents and supplier proof exist."
    return "Run source scans and supplier-readiness matching; no easy-capture candidate is proven from current local data."


def render_metric(label: str, value: Any) -> str:
    return f'<div class="metric"><strong>{html.escape(str(value))}</strong><span>{html.escape(label)}</span></div>'


def render_card(card: dict[str, Any]) -> str:
    classification = card.get("classification", "")
    class_name = "easy" if classification == "EASY_CAPTURE" else "watchlist" if classification == "WATCHLIST" else "avoid"
    why = "; ".join(str(item) for item in card.get("why_this_is_easier", [])[:3])
    risks = "; ".join(str(item) for item in card.get("risk_flags", [])[:3])
    missing = "; ".join(str(item) for item in card.get("missing_info", [])[:3])
    return f"""
    <div class="card">
      <div class="card-head"><span class="case">{html.escape(str(card.get('case_id', '')))}</span><span class="score {class_name}">{html.escape(str(card.get('low_competition_score', '')))} / 100 · {html.escape(classification)}</span></div>
      <div class="title">{html.escape(str(card.get('title', '')))}</div>
      <div class="grid">
        <div>Buyer: {html.escape(str(card.get('buyer', '') or 'unknown'))}</div>
        <div>Source: {html.escape(str(card.get('source', '') or 'unknown'))}</div>
        <div>Category: {html.escape(str(card.get('category_label', '') or card.get('category', '')))}</div>
        <div>Deadline: {html.escape(str(card.get('deadline', '') or 'unknown'))}</div>
        <div>EMD: {html.escape(str(card.get('EMD', '') or 'unknown'))}</div>
        <div>Evidence: {html.escape(str(card.get('evidence_level', '')))}</div>
      </div>
      <div class="flags"><span class="badge">Why easier</span>{html.escape(why)}</div>
      <div class="flags"><span class="badge">Risk</span>{html.escape(risks)}</div>
      <div class="flags"><span class="badge">Missing</span>{html.escape(missing)}</div>
      <div class="flags"><span class="badge">Next</span>{html.escape(str(card.get('recommended_next_action', '')))}</div>
    </div>"""


def render_generic_row(row: dict[str, Any]) -> str:
    pairs = []
    for key, value in list(row.items())[:8]:
        if isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=False)
        pairs.append(f"<div>{html.escape(str(key))}: {html.escape(str(value))}</div>")
    return f'<div class="card"><div class="grid">{"".join(pairs)}</div></div>'


def render_report_html(report: dict[str, Any]) -> str:
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    summary = report["summary"]
    summary_cards = "".join(
        [
            render_metric("Records analyzed", summary["records_analyzed"]),
            render_metric("Easy capture", summary["easy_capture_count"]),
            render_metric("Watchlist", summary["watchlist_count"]),
            render_metric("Avoid", summary["avoid_count"]),
            render_metric("Supplier-ready categories", summary["supplier_ready_category_count"]),
        ]
    )
    sections_html = []
    for section_key, title in REPORT_SECTIONS:
        rows = report["sections"].get(section_key, [])
        if not rows:
            body = '<p class="muted">Nothing proven from current local data.</p>'
        elif section_key == "next_owner_action":
            body = "".join(render_generic_row(row) for row in rows)
        elif rows and "low_competition_score" in rows[0]:
            body = "".join(render_card(row) for row in rows)
        else:
            body = "".join(render_generic_row(row) for row in rows)
        sections_html.append(f"<section><h2>{html.escape(title)}</h2>{body}</section>")
    return (
        template.replace("{{generated_date}}", dt.date.today().isoformat())
        .replace("{{generated_at}}", html.escape(report["created_at"]))
        .replace("{{summary_cards}}", summary_cards)
        .replace("{{sections}}", "\n".join(sections_html))
    )


def write_outputs(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = today_compact()
    json_path = output_dir / f"low_competition_order_radar_{stamp}.json"
    html_path = output_dir / f"low_competition_order_radar_{stamp}.html"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path.write_text(render_report_html(report), encoding="utf-8")
    return html_path, json_path


def load_runtime_inputs() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    cases = load_csv(DATA_DIR / "master_cases.csv", "master_cases.example.csv")
    suppliers = load_csv(DATA_DIR / "supplier_master.csv", "supplier_master.example.csv")
    quotes = load_csv(DATA_DIR / "quote_master.csv", "quote_master.example.csv")
    return cases, suppliers, quotes


def maybe_append_event(report: dict[str, Any], json_path: Path, *, dry_run: bool, record_event: bool) -> None:
    if dry_run or not record_event:
        return
    append_event(
        "low_competition.radar_generated",
        "low_competition_order_radar",
        object_type="low_competition_radar",
        object_id=report["run_id"],
        source="local_runtime",
        payload={
            "run_id": report["run_id"],
            "report_path": relative(json_path),
            "records_analyzed": report["summary"]["records_analyzed"],
            "top_candidates_count": report["summary"]["easy_capture_count"],
            "created_at": report["created_at"],
        },
        citations=[relative(json_path)],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Low-Competition Order Radar report")
    parser.add_argument("--dry-run", action="store_true", help="Write local report only; do not append events")
    parser.add_argument("--json", action="store_true", help="Print report JSON to stdout")
    parser.add_argument("--record-event", action="store_true", help="Append event ledger row when not in dry-run")
    parser.add_argument("--no-source-runs", action="store_true", help="Only analyze master_cases.csv rows")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    cases, suppliers, quotes = load_runtime_inputs()
    report = generate_report(
        cases,
        suppliers,
        quotes,
        keyword_config=load_yaml_config(DEFAULT_KEYWORDS),
        categories_config=load_yaml_config(DEFAULT_CATEGORIES),
        scoring_config=load_yaml_config(DEFAULT_SCORING),
        include_source_runs=not args.no_source_runs,
    )
    html_path, json_path = write_outputs(report, Path(args.output_dir))
    maybe_append_event(report, json_path, dry_run=args.dry_run, record_event=args.record_event)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Low-competition radar report: {html_path}")
        print(f"Low-competition radar JSON: {json_path}")
        print("No external action was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
