#!/usr/bin/env python3
"""Tender Export OS morning opportunity intelligence pipeline.

This is the owner-facing, read-only orchestration layer for the daily morning
workflow the founder described:

1. Public/source-intake radar check for GOV tenders and EXPORT RFQ sources.
2. Requirements/deep-read pass from the case register and evidence notes.
3. Supplier pass using the 5-3-2 rule from supplier/quote registers.
4. Per-case supply-chain document drafts.
5. Pricing/quote proof assistance without final price commitments.
6. Blind-spot routing and approval-gate surfacing.
7. HTML report file for the founder.

Safety: this report script itself never sends buyer/supplier messages, submits
bids/RFQs, logs in to portals, uploads documents, pays money, uses DSC, confirms
HSN/ITC-HS/origin, or commits final prices/terms. Supplier outreach and portal
login/signup are now standing-authorized in `config/approval_policy.yaml`, but
this script only reports/routes them; execution scripts must still write receipts
and keep buyer/bid/payment/final-commitment gates intact.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import math
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from event_ledger import append_event
except Exception:  # pragma: no cover - report should still render if ledger import breaks
    append_event = None  # type: ignore[assignment]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "opportunity_intelligence"
SUPPLY_CHAIN_DIR = PROJECT_ROOT / "outputs" / "supply_chain"
RUN_LOG = DATA_DIR / "agent_run_log.csv"

ACTIVE_STATUSES = {
    "NEW",
    "FAST_KILL",
    "WATCHLIST",
    "DEEP_READ",
    "SUPPLIER_SEARCH",
    "PRICING_READY",
    "ARTIFACT_PRODUCTION",
    "APPROVAL_REQUIRED",
    "APPROVED",
    "FOLLOW_UP",
}
TERMINAL_STATUSES = {"REJECTED", "WON", "LOST", "ARCHIVED"}
RUN_LOG_FIELDS = [
    "run_id",
    "run_date",
    "run_time",
    "agent_name",
    "trigger_type",
    "cases_processed",
    "cases_created",
    "cases_rejected",
    "cases_updated",
    "sources_checked",
    "sources_failed",
    "actions_taken",
    "approval_cards_created",
    "receipts_created",
    "errors",
    "warnings",
    "runtime_seconds",
    "status",
    "notes",
]


def now_local() -> dt.datetime:
    return dt.datetime.now().astimezone()


def today_iso() -> str:
    return now_local().date().isoformat()


def today_compact() -> str:
    return now_local().strftime("%Y%m%d")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(p)


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def load_csv(name: str) -> list[dict[str, str]]:
    path = DATA_DIR / name
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_run_log(row: dict[str, Any]) -> None:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    exists = RUN_LOG.exists()
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RUN_LOG_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in RUN_LOG_FIELDS})


def parse_number(value: object) -> float | None:
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    text = re.sub(r"[^0-9.\-]", "", text)
    if not text or text in {"-", "."}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d-%b-%y", "%d-%b-%Y"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def days_until(value: str) -> int | None:
    parsed = parse_date(value)
    if not parsed:
        return None
    return (parsed - now_local().date()).days


def boolish(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def compact_text(value: str, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def command_tail(text: str, limit: int = 1200) -> str:
    text = str(text or "")
    return text[-limit:] if len(text) > limit else text


def run_step(label: str, command: list[str], timeout: int = 120) -> dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "label": label,
            "command": " ".join(command),
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout_tail": command_tail(proc.stdout),
            "stderr_tail": command_tail(proc.stderr),
            "runtime_seconds": round(time.time() - started, 2),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "label": label,
            "command": " ".join(command),
            "ok": False,
            "exit_code": "timeout",
            "stdout_tail": command_tail(exc.stdout or ""),
            "stderr_tail": command_tail(exc.stderr or f"Timed out after {timeout}s"),
            "runtime_seconds": round(time.time() - started, 2),
        }
    except Exception as exc:  # noqa: BLE001 - orchestrator records operational failures
        return {
            "label": label,
            "command": " ".join(command),
            "ok": False,
            "exit_code": "exception",
            "stdout_tail": "",
            "stderr_tail": f"{type(exc).__name__}: {exc}",
            "runtime_seconds": round(time.time() - started, 2),
        }


def latest_file(pattern: str) -> Path | None:
    matches = list(PROJECT_ROOT.glob(pattern))
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def load_latest_json(pattern: str) -> dict[str, Any]:
    path = latest_file(pattern)
    if not path:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_path"] = rel(path)
        return data
    except Exception:
        return {"_path": rel(path), "_error": "could_not_parse_json"}


def score_case(case: dict[str, str]) -> float:
    explicit = parse_number(case.get("score_gov") or case.get("score_export"))
    if explicit is not None:
        return explicit
    score = 0.0
    if case.get("workflow_type") == "EXPORT":
        score += 15
    elif case.get("workflow_type") == "GOV":
        score += 12
    status = (case.get("status") or "").upper()
    if status == "NEW":
        score += 20
    if status in {"SUPPLIER_SEARCH", "PRICING_READY", "APPROVAL_REQUIRED"}:
        score += 25
    if case.get("source_url"):
        score += 10
    d = days_until(case.get("deadline_date", ""))
    if d is not None:
        if 3 <= d <= 21:
            score += 20
        elif d < 3:
            score -= 15
        elif d <= 45:
            score += 8
    return score


def active_cases(cases: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [c for c in cases if (c.get("status") or "").upper() not in TERMINAL_STATUSES]
    rows.sort(key=lambda c: (score_case(c), -(days_until(c.get("deadline_date", "")) or 9999)), reverse=True)
    return rows


GENERIC_SUPPLIER_MATCH_TOKENS = {
    "supply",
    "supplies",
    "supplier",
    "items",
    "item",
    "product",
    "products",
    "service",
    "services",
    "with",
    "from",
    "tender",
    "government",
    "procurement",
    "food",
    "kit",
    "kits",
    "equipment",
    "goods",
}


def case_tokens(case: dict[str, str]) -> set[str]:
    text = " ".join([
        case.get("product_or_service", ""),
        case.get("opportunity_title", ""),
        case.get("mandatory_certs", ""),
    ]).lower()
    return {tok for tok in re.findall(r"[a-z0-9]{4,}", text) if tok not in GENERIC_SUPPLIER_MATCH_TOKENS}


def suppliers_for_case(case: dict[str, str], suppliers: list[dict[str, str]], *, max_related: int = 8) -> list[dict[str, str]]:
    """Return supplier rows with evidence tied to the case.

    Exact case-linked suppliers are always shown. Loose fuzzy matches are only
    allowed after a case has advanced beyond NEW and only when at least two
    non-generic product tokens overlap. This prevents the report from implying
    that generic database suppliers are real candidates for fresh leads.
    """
    cid = case.get("case_id", "")
    exact = [s for s in suppliers if s.get("last_quote_case_id") == cid or cid in (s.get("notes") or "")]
    if len(exact) >= max_related or (case.get("status") or "").upper() == "NEW":
        return exact[:max_related]
    tokens = case_tokens(case)
    if len(tokens) < 2:
        return exact[:max_related]
    related: list[tuple[int, dict[str, str]]] = []
    exact_ids = {s.get("supplier_id") for s in exact}
    for supplier in suppliers:
        if supplier.get("supplier_id") in exact_ids:
            continue
        text = " ".join([
            supplier.get("products_supplied", ""),
            supplier.get("notes", ""),
            supplier.get("hsn_codes", ""),
        ]).lower()
        overlap_tokens = {tok for tok in tokens if tok in text}
        if len(overlap_tokens) >= 2:
            total_score = int(parse_number(supplier.get("total_supplier_score")) or 0)
            related.append((len(overlap_tokens) * 100 + total_score, supplier))
    related.sort(key=lambda item: item[0], reverse=True)
    return exact + [item[1] for item in related[: max(0, max_related - len(exact))]]


def quotes_for_case(case_id: str, quotes: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [q for q in quotes if q.get("case_id") == case_id]
    rows.sort(key=lambda q: int(parse_number(q.get("price_rank")) or 999))
    return rows


def approval_for_case(case_id: str, approvals: list[dict[str, str]]) -> list[dict[str, str]]:
    return [a for a in approvals if a.get("case_id") == case_id and (a.get("approval_status") or "").upper() == "PENDING"]


def quote_counts(case_quotes: list[dict[str, str]]) -> dict[str, int]:
    formal = 0
    public_price = 0
    any_price = 0
    for quote in case_quotes:
        has_price = any(quote.get(field) for field in ["unit_price_inr", "unit_price_usd", "total_price_inr", "total_price_usd", "fob_price_usd", "cif_price_usd"])
        if has_price:
            any_price += 1
        if quote.get("quote_request_sent_at") and quote.get("quote_received_at"):
            formal += 1
        if has_price and not quote.get("quote_request_sent_at"):
            public_price += 1
    return {"formal_quote_proofs": formal, "public_price_proofs": public_price, "price_proofs_total": any_price}


def source_type_count(case_suppliers: list[dict[str, str]]) -> int:
    return len({s.get("source_type") for s in case_suppliers if s.get("source_type")})


def requirements_for_case(case: dict[str, str], rfqs_by_case: dict[str, dict[str, str]]) -> list[str]:
    workflow = case.get("workflow_type", "")
    reqs: list[str] = []
    if case.get("product_or_service"):
        reqs.append(f"Product/service: {case['product_or_service']}")
    if case.get("quantity"):
        reqs.append(f"Quantity: {case.get('quantity')} {case.get('unit', '')}".strip())
    if case.get("mandatory_certs"):
        reqs.append(f"Mandatory certs/specs seen: {case['mandatory_certs']}")
    if case.get("delivery_location"):
        reqs.append(f"Delivery: {case['delivery_location']} within {case.get('delivery_days') or 'TBD'} days")
    if case.get("payment_terms"):
        reqs.append(f"Payment terms seen: {case['payment_terms']}")
    if case.get("emd_amount_inr"):
        reqs.append(f"EMD/security noted: INR {case['emd_amount_inr']} (owner approval required before payment)")
    if boolish(case.get("past_experience_required", "")) or case.get("experience_details"):
        reqs.append(f"Experience requirement: {case.get('experience_details') or 'past experience required'}")
    if workflow == "GOV":
        reqs.extend([
            "GOV docs/checks: tender notice/PDF/BOQ, eligibility clauses, GST/PAN/MSME/Udyam if applicable, GeM/portal registration, EMD exemption/payment path, delivery/penalty clauses.",
            "Do not upload bid documents, use DSC, or pay EMD without a separate approval card. Supplier quote/availability outreach is standing-authorized when receipts are logged.",
        ])
    elif workflow == "EXPORT":
        rfq = rfqs_by_case.get(case.get("case_id", ""), {})
        if rfq:
            reqs.append(f"Buyer/RFQ evidence stage: {rfq.get('rfq_stage')} / {rfq.get('evidence_status')}; missing: {rfq.get('missing_evidence')}")
        reqs.extend([
            "EXPORT docs/checks: buyer-specific RFQ proof, buyer identity verification, IEC/export readiness, draft ITC-HS only, product spec/COA/MSDS if relevant, packing list, proforma invoice draft, logistics/incoterms assumptions.",
            "Do not confirm HSN/ITC-HS, origin, Incoterms, delivery, payment terms, or final quote externally without separate approval. Supplier quote/availability outreach and portal login/signup are standing-authorized when receipts are logged.",
        ])
    if not case.get("source_url"):
        reqs.append("Evidence gap: original source URL missing; recover/source before any external action.")
    if not boolish(case.get("deep_read_done", "")):
        reqs.append("Deep-read gap: structured requirement extraction is not complete yet.")
    return reqs


def routing_for_case(
    case: dict[str, str],
    case_suppliers: list[dict[str, str]],
    case_quotes: list[dict[str, str]],
    case_approvals: list[dict[str, str]],
    rfqs_by_case: dict[str, dict[str, str]],
) -> list[str]:
    status = (case.get("status") or "").upper()
    workflow = case.get("workflow_type", "")
    counts = quote_counts(case_quotes)
    routes: list[str] = []
    d = days_until(case.get("deadline_date", ""))
    if d is not None and d <= 2:
        routes.append(f"Deadline urgent ({d} day(s)); fast-kill unless all prerequisites are already complete.")
    if status == "NEW":
        routes.append("Route to Fast Kill, then Deep Read only if viable.")
    if status in {"WATCHLIST", "FAST_KILL"} and not boolish(case.get("deep_read_done", "")):
        routes.append("Route to Deep Read if evidence is readable; never infer eligibility from missing data.")
    if status in {"DEEP_READ", "SUPPLIER_SEARCH"}:
        if len(case_suppliers) < 5 or source_type_count(case_suppliers) < 3:
            routes.append("Route to Supplier Engine: need 5 candidates across 3 source types.")
        if counts["price_proofs_total"] < 2:
            routes.append("Pricing blocked: need 2 quote/price proofs; supplier quote/availability outreach is standing-authorized, but final buyer quote remains approval-gated.")
    if workflow == "EXPORT":
        rfq = rfqs_by_case.get(case.get("case_id", ""), {})
        if rfq and rfq.get("evidence_status") != "RFQ_VERIFIED":
            routes.append("Buyer/RFQ verification is weak; do not count as verified demand until buyer-specific proof exists.")
        if not case.get("hsn_itchs_candidate"):
            routes.append("Compliance draft needed: ITC-HS candidate missing; final classification remains owner/specialist-gated.")
    if case_approvals:
        ids = ", ".join(a.get("approval_id") or a.get("case_id", "") for a in case_approvals)
        routes.append(f"Owner approval pending: {ids}.")
    if not routes:
        routes.append("No immediate blocker found; keep in normal stage queue and re-check source/quote freshness.")
    return routes


def pricing_summary(case: dict[str, str], case_quotes: list[dict[str, str]]) -> dict[str, Any]:
    counts = quote_counts(case_quotes)
    rows: list[dict[str, Any]] = []
    totals_inr: list[float] = []
    totals_usd: list[float] = []
    for quote in case_quotes:
        qty = parse_number(quote.get("quantity") or case.get("quantity")) or 0
        unit_inr = parse_number(quote.get("price_incl_gst_inr") or quote.get("unit_price_inr"))
        unit_usd = parse_number(quote.get("unit_price_usd") or quote.get("fob_price_usd") or quote.get("cif_price_usd"))
        total_inr = parse_number(quote.get("total_price_inr"))
        total_usd = parse_number(quote.get("total_price_usd"))
        if total_inr is None and unit_inr is not None and qty:
            total_inr = unit_inr * qty
        if total_usd is None and unit_usd is not None and qty:
            total_usd = unit_usd * qty
        if total_inr is not None and math.isfinite(total_inr):
            totals_inr.append(total_inr)
        if total_usd is not None and math.isfinite(total_usd):
            totals_usd.append(total_usd)
        rows.append({
            "quote_id": quote.get("quote_id"),
            "supplier_name": quote.get("supplier_name"),
            "product_description": quote.get("product_description"),
            "currency": quote.get("currency"),
            "unit_price_inr": quote.get("unit_price_inr"),
            "unit_price_usd": quote.get("unit_price_usd") or quote.get("fob_price_usd") or quote.get("cif_price_usd"),
            "total_inr_estimate": round(total_inr, 2) if total_inr is not None else "",
            "total_usd_estimate": round(total_usd, 2) if total_usd is not None else "",
            "formal": bool(quote.get("quote_request_sent_at") and quote.get("quote_received_at")),
            "notes": compact_text(quote.get("notes", ""), 120),
        })
    status = "BLOCKED_NEEDS_2_PRICE_PROOFS"
    if counts["price_proofs_total"] >= 2:
        status = "INTERNAL_PRICING_ASSIST_READY_NOT_FINAL"
    return {
        "status": status,
        "counts": counts,
        "quote_rows": rows,
        "draft_range_inr": [round(min(totals_inr), 2), round(max(totals_inr), 2)] if totals_inr else [],
        "draft_range_usd": [round(min(totals_usd), 2), round(max(totals_usd), 2)] if totals_usd else [],
        "safety": "Internal quote assistance only; no final buyer/supplier price commitment.",
    }


def supply_chain_lines(
    case: dict[str, str],
    case_suppliers: list[dict[str, str]],
    case_quotes: list[dict[str, str]],
    reqs: list[str],
    routes: list[str],
    pricing: dict[str, Any],
) -> list[str]:
    cid = case.get("case_id", "UNKNOWN")
    lines = [
        f"# Supply Chain Document Draft — {cid}",
        "",
        "Safety: internal planning draft only. This is not a supplier contract, buyer quotation, purchase order, origin claim, final classification, or submitted bid.",
        "",
        "## 1. Demand / opportunity",
        f"- Workflow: {case.get('workflow_type', '')}",
        f"- Title: {case.get('opportunity_title', '')}",
        f"- Buyer: {case.get('buyer_name', '')}",
        f"- Source: {case.get('source_name', '')} — {case.get('source_url', '')}",
        f"- Deadline: {case.get('deadline_date', '') or 'not stated'}",
        "",
        "## 2. Requirements extracted / needed",
    ]
    lines.extend(f"- {item}" for item in reqs)
    lines.extend(["", "## 3. Supplier capacity map"])
    if case_suppliers:
        lines.extend([
            "| Supplier | Source type | Products | Lead time | Score | Quote/proof |",
            "|---|---|---|---:|---:|---|",
        ])
        quote_supplier_ids = {q.get("supplier_id") for q in case_quotes}
        for supplier in case_suppliers[:10]:
            has_quote = "yes" if supplier.get("supplier_id") in quote_supplier_ids else "no"
            lines.append(
                f"| {supplier.get('supplier_name', '')} | {supplier.get('source_type', '')} | "
                f"{compact_text(supplier.get('products_supplied', ''), 90)} | {supplier.get('lead_time_days', '')} | "
                f"{supplier.get('total_supplier_score', '')} | {has_quote} |"
            )
    else:
        lines.append("- No supplier candidates are registered yet for this case.")
    lines.extend([
        "",
        "## 4. Quote / price proof map",
        f"- Price proof status: {pricing['status']}",
        f"- Formal quote proofs: {pricing['counts']['formal_quote_proofs']}",
        f"- Public/indicative price proofs: {pricing['counts']['public_price_proofs']}",
    ])
    if pricing["draft_range_inr"]:
        lines.append(f"- Internal INR total range from recorded quote proofs: {pricing['draft_range_inr']}")
    if pricing["draft_range_usd"]:
        lines.append(f"- Internal USD total range from recorded quote proofs: {pricing['draft_range_usd']}")
    lines.extend([
        "",
        "## 5. Contract / document checklist",
        "- Supplier quotation with validity, GST/tax, delivery terms, payment terms, packing, warranty/quality terms.",
        "- Buyer/tender requirement document, BOQ/specification, delivery schedule, penalty/payment clauses.",
        "- Compliance documents: GST/PAN/Udyam/GEM/IEC/certificates as applicable; ITC-HS/origin only as draft until approved.",
        "- Logistics checklist: pickup, packing, insurance, freight, delivery timeline, inspection/proof of delivery.",
        "- Standing authorization covers supplier RFQ/follow-up and portal login/signup for research; log receipts and secret aliases only. Separate approval remains required before buyer sends, bid uploads, payments, DSC, POs, final classifications/origin claims, or final price/terms.",
        "",
        "## 6. Routing / blockers",
    ])
    lines.extend(f"- {item}" for item in routes)
    lines.extend(["", "## 7. Sources used", "- data/master_cases.csv", "- data/supplier_master.csv", "- data/quote_master.csv", "- data/approvals_receipts.csv"])
    if case.get("source_url"):
        lines.append(f"- {case.get('source_url')}")
    return lines


def write_supply_chain_doc(
    case: dict[str, str],
    case_suppliers: list[dict[str, str]],
    case_quotes: list[dict[str, str]],
    reqs: list[str],
    routes: list[str],
    pricing: dict[str, Any],
) -> Path:
    SUPPLY_CHAIN_DIR.mkdir(parents=True, exist_ok=True)
    cid = case.get("case_id", "UNKNOWN")
    path = SUPPLY_CHAIN_DIR / f"supply_chain_{cid}_{today_compact()}.md"
    path.write_text("\n".join(supply_chain_lines(case, case_suppliers, case_quotes, reqs, routes, pricing)) + "\n", encoding="utf-8")
    return path


def analyze_cases(
    cases: list[dict[str, str]],
    suppliers: list[dict[str, str]],
    quotes: list[dict[str, str]],
    approvals: list[dict[str, str]],
    rfqs: list[dict[str, str]],
    max_cases: int,
) -> list[dict[str, Any]]:
    rfqs_by_case = {row.get("case_id", ""): row for row in rfqs if row.get("case_id")}
    analyzed: list[dict[str, Any]] = []
    for case in active_cases(cases)[:max_cases]:
        cid = case.get("case_id", "")
        case_suppliers = suppliers_for_case(case, suppliers)
        case_quotes = quotes_for_case(cid, quotes)
        case_approvals = approval_for_case(cid, approvals)
        reqs = requirements_for_case(case, rfqs_by_case)
        routes = routing_for_case(case, case_suppliers, case_quotes, case_approvals, rfqs_by_case)
        pricing = pricing_summary(case, case_quotes)
        sc_path = write_supply_chain_doc(case, case_suppliers, case_quotes, reqs, routes, pricing)
        analyzed.append({
            "case": case,
            "score": score_case(case),
            "requirements": reqs,
            "suppliers": case_suppliers,
            "supplier_candidate_count": len(case_suppliers),
            "supplier_source_type_count": source_type_count(case_suppliers),
            "quotes": case_quotes,
            "approvals": case_approvals,
            "pricing": pricing,
            "routing": routes,
            "supply_chain_doc": rel(sc_path),
        })
    return analyzed


def render_supplier_badges(item: dict[str, Any]) -> str:
    candidate_count = item["supplier_candidate_count"]
    source_types = item["supplier_source_type_count"]
    quote_total = item["pricing"]["counts"]["price_proofs_total"]
    status = "PASS" if candidate_count >= 5 and source_types >= 3 and quote_total >= 2 else "BLOCKED"
    cls = "ok" if status == "PASS" else "warn"
    return (
        f'<span class="pill {cls}">5-3-2 {esc(status)}</span> '
        f'<span class="pill">{candidate_count} suppliers</span> '
        f'<span class="pill">{source_types} source types</span> '
        f'<span class="pill">{quote_total} price proofs</span>'
    )


def render_quote_table(item: dict[str, Any]) -> str:
    rows = item["pricing"].get("quote_rows", [])
    if not rows:
        return '<p class="muted">No quote/price proof registered yet.</p>'
    body = "\n".join(
        f"<tr><td>{esc(row.get('quote_id'))}</td><td>{esc(row.get('supplier_name'))}</td><td>{esc(row.get('product_description'))}</td>"
        f"<td>{esc(row.get('unit_price_inr'))}</td><td>{esc(row.get('unit_price_usd'))}</td>"
        f"<td>{esc(row.get('total_inr_estimate'))}</td><td>{esc(row.get('total_usd_estimate'))}</td>"
        f"<td>{'formal' if row.get('formal') else 'public/indicative'}</td></tr>"
        for row in rows
    )
    return f"<table><thead><tr><th>ID</th><th>Supplier</th><th>Product</th><th>Unit INR</th><th>Unit USD</th><th>Total INR est.</th><th>Total USD est.</th><th>Proof type</th></tr></thead><tbody>{body}</tbody></table>"


def render_html_report(
    analyzed: list[dict[str, Any]],
    all_cases: list[dict[str, str]],
    approvals: list[dict[str, str]],
    source_health: list[dict[str, str]],
    plugin_health: list[dict[str, str]],
    command_results: list[dict[str, Any]],
    latest_artifacts: dict[str, str],
    external_intake: dict[str, Any],
    output_path: Path,
) -> None:
    active = active_cases(all_cases)
    new_today = [c for c in all_cases if (c.get("created_at") or "").startswith(today_iso())]
    pending_approvals = [a for a in approvals if (a.get("approval_status") or "").upper() == "PENDING"]
    gov = sum(1 for c in active if c.get("workflow_type") == "GOV")
    exp = sum(1 for c in active if c.get("workflow_type") == "EXPORT")
    source_issues = [s for s in source_health if (s.get("health_status") or "") not in {"Working", ""}]
    plugin_issues = [p for p in plugin_health if (p.get("health_status") or "") not in {"Working", ""} or (p.get("blocker") or "").strip()]
    step_rows = "\n".join(
        f"<tr><td>{esc(step['label'])}</td><td>{'✅' if step['ok'] else '⚠️'}</td><td>{esc(step['exit_code'])}</td><td>{esc(step['runtime_seconds'])}</td><td><code>{esc(compact_text(step.get('stderr_tail') or step.get('stdout_tail') or '', 220))}</code></td></tr>"
        for step in command_results
    )

    case_cards = []
    for item in analyzed:
        case = item["case"]
        cid = case.get("case_id", "")
        source_link = f'<a href="{esc(case.get("source_url"))}">source</a>' if case.get("source_url") else '<span class="muted">source missing</span>'
        req_list = "".join(f"<li>{esc(req)}</li>" for req in item["requirements"][:8])
        routes = "".join(f"<li>{esc(route)}</li>" for route in item["routing"])
        supplier_rows = "".join(
            f"<tr><td>{esc(s.get('supplier_name'))}</td><td>{esc(s.get('source_type'))}</td><td>{esc(compact_text(s.get('products_supplied', ''), 90))}</td><td>{esc(s.get('total_supplier_score'))}</td></tr>"
            for s in item["suppliers"][:6]
        ) or '<tr><td colspan="4" class="muted">No suppliers registered.</td></tr>'
        case_cards.append(f"""
<section class="case-card">
  <div class="case-head">
    <div>
      <div class="kicker">{esc(case.get('workflow_type'))} · {esc(case.get('status'))} · score {esc(round(item['score'], 1))}</div>
      <h2>{esc(cid)} — {esc(case.get('opportunity_title'))}</h2>
      <p class="muted">Buyer: {esc(case.get('buyer_name') or 'not clear')} · Deadline: {esc(case.get('deadline_date') or 'not stated')} · {source_link}</p>
    </div>
    <a class="doclink" href="../supply_chain/{esc(Path(item['supply_chain_doc']).name)}">Supply-chain doc</a>
  </div>
  <div class="pipeline-badges">{render_supplier_badges(item)}</div>
  <div class="cols">
    <div><h3>Requirements pass</h3><ul>{req_list}</ul></div>
    <div><h3>Routing / blind spots</h3><ul>{routes}</ul></div>
  </div>
  <h3>Supplier pass</h3>
  <table><thead><tr><th>Supplier</th><th>Source type</th><th>Products</th><th>Score</th></tr></thead><tbody>{supplier_rows}</tbody></table>
  <h3>Pricing / quote assistance</h3>
  <p class="muted">{esc(item['pricing']['status'])}. Internal only; no final price commitment.</p>
  {render_quote_table(item)}
</section>
""")

    source_rows = "\n".join(
        f"<tr><td>{esc(s.get('source_name'))}</td><td>{esc(s.get('workflow'))}</td><td>{esc(s.get('health_status'))}</td><td>{esc(s.get('url'))}</td><td>{esc(compact_text(s.get('notes', ''), 130))}</td></tr>"
        for s in source_health
    )
    approval_rows = "\n".join(
        f"<tr><td>{esc(a.get('approval_id'))}</td><td>{esc(a.get('case_id'))}</td><td>{esc(a.get('workflow_type'))}</td><td>{esc(a.get('action_approved') or a.get('proposed_action'))}</td><td>{esc(a.get('approval_status'))}</td></tr>"
        for a in pending_approvals
    ) or '<tr><td colspan="5" class="muted">No pending approvals.</td></tr>'
    artifact_links = "".join(
        f"<li><strong>{esc(label)}:</strong> <code>{esc(path)}</code></li>"
        for label, path in latest_artifacts.items() if path
    )
    external_summary = external_intake.get("summary") or {}

    css = """
:root { color-scheme: dark; }
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#07111f; color:#e5edf8; }
main { max-width:1180px; margin:0 auto; padding:30px 18px 60px; }
a { color:#7dd3fc; text-decoration:none; }
h1 { font-size:34px; margin:0; }
h2 { margin:0 0 8px; font-size:22px; }
h3 { margin:18px 0 8px; color:#bfdbfe; }
.hero { border:1px solid #1e3a5f; background:linear-gradient(135deg,#0f172a,#082f49); padding:22px; border-radius:18px; box-shadow:0 20px 45px rgba(0,0,0,.3); }
.kicker { color:#93c5fd; font-size:12px; text-transform:uppercase; letter-spacing:.08em; font-weight:700; }
.muted { color:#94a3b8; }
.tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin:18px 0; }
.tile { background:#0f1d33; border:1px solid #1f3b61; border-radius:14px; padding:14px; }
.tile b { display:block; font-size:28px; }
.flow { display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }
.flow span,.pill { display:inline-block; padding:6px 9px; background:#172554; border:1px solid #1d4ed8; color:#dbeafe; border-radius:999px; font-size:12px; }
.pill.ok { background:#064e3b; border-color:#10b981; }
.pill.warn { background:#713f12; border-color:#f59e0b; }
.case-card { margin-top:18px; background:#0d1b2e; border:1px solid #1f3b61; border-radius:18px; padding:18px; }
.case-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
.doclink { white-space:nowrap; padding:8px 10px; border:1px solid #38bdf8; border-radius:10px; }
.cols { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px; }
table { border-collapse:collapse; width:100%; margin:10px 0; font-size:13px; }
th,td { border-bottom:1px solid #1e3a5f; padding:8px 9px; text-align:left; vertical-align:top; }
th { color:#bfdbfe; background:#10213a; }
code { color:#c4b5fd; white-space:pre-wrap; }
.warnbox { border:1px solid #f59e0b; background:#422006; color:#fde68a; border-radius:14px; padding:12px; margin-top:16px; }
"""
    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Tender Export OS Daily Opportunity Intelligence {esc(today_iso())}</title><style>{css}</style></head>
<body><main>
<section class="hero">
  <div class="kicker">Tender Export OS · Morning Opportunity Intelligence</div>
  <h1>Daily opportunity pipeline — {esc(today_iso())}</h1>
  <p class="muted">Generated {esc(now_local().isoformat(timespec='seconds'))}. Internal intelligence report; supplier RFQ/follow-up and portal login/signup are standing-authorized, while buyer/bid/payment/DSC/final commitment actions remain approval-gated.</p>
  <div class="flow"><span>Radar</span><span>Requirements deep pass</span><span>Supplier 5-3-2</span><span>Supply-chain docs</span><span>Pricing assistance</span><span>Blind-spot routing</span><span>HTML report</span></div>
</section>
<div class="tiles">
  <div class="tile"><span class="muted">Active cases</span><b>{len(active)}</b></div>
  <div class="tile"><span class="muted">New/updated today</span><b>{len(new_today)}</b></div>
  <div class="tile"><span class="muted">GOV active</span><b>{gov}</b></div>
  <div class="tile"><span class="muted">EXPORT active</span><b>{exp}</b></div>
  <div class="tile"><span class="muted">Pending approvals</span><b>{len(pending_approvals)}</b></div>
  <div class="tile"><span class="muted">Source issues</span><b>{len(source_issues)}</b></div>
</div>
<section class="warnbox"><strong>Guardrails:</strong> this report run did not execute messages, portal logins, submissions, document uploads, payments, DSC use, final HSN/ITC-HS/origin claims, or final price/terms. Standing authorization now covers supplier quote/availability outreach and portal login/signup for research when receipts and secret aliases are logged.</section>
<section class="case-card">
  <h2>Morning source/radar handoff</h2>
  <p>Safe public probe checked <strong>{esc(external_summary.get('sources_checked', 'n/a'))}</strong> source(s), reachable <strong>{esc(external_summary.get('reachable', 'n/a'))}</strong>, blocked/login-like <strong>{esc(external_summary.get('blocked', 'n/a'))}</strong>, failed/errors <strong>{esc(external_summary.get('failed', 'n/a'))}</strong>.</p>
  <p class="muted">Deep portal coverage improves as standing-authorized login/signup flows are connected. The pipeline still avoids paywalls, CAPTCHA/OTP, and legal/payment commitments without the required live step or separate approval.</p>
</section>
<section class="case-card">
  <h2>Pending approvals</h2>
  <table><thead><tr><th>Approval</th><th>Case</th><th>Workflow</th><th>Action</th><th>Status</th></tr></thead><tbody>{approval_rows}</tbody></table>
</section>
{''.join(case_cards) if case_cards else '<section class="case-card"><h2>No active cases</h2><p class="muted">No active opportunities in the local registers.</p></section>'}
<section class="case-card">
  <h2>Source health / portal coverage</h2>
  <table><thead><tr><th>Source</th><th>Workflow</th><th>Health</th><th>URL</th><th>Notes</th></tr></thead><tbody>{source_rows}</tbody></table>
</section>
<section class="case-card">
  <h2>Automation steps run</h2>
  <table><thead><tr><th>Step</th><th>OK</th><th>Exit</th><th>Seconds</th><th>Output/error tail</th></tr></thead><tbody>{step_rows}</tbody></table>
</section>
<section class="case-card">
  <h2>Sources and linked artifacts used</h2>
  <ul>
    <li><code>data/master_cases.csv</code></li>
    <li><code>data/supplier_master.csv</code></li>
    <li><code>data/quote_master.csv</code></li>
    <li><code>data/approvals_receipts.csv</code></li>
    <li><code>data/source_health.csv</code></li>
    {artifact_links}
  </ul>
</section>
<section class="case-card">
  <h2>Recommended owner action</h2>
  <p>{esc(recommended_action(analyzed, pending_approvals, plugin_issues))}</p>
</section>
</main></body></html>"""
    output_path.write_text(html_doc, encoding="utf-8")


def recommended_action(analyzed: list[dict[str, Any]], pending_approvals: list[dict[str, str]], plugin_issues: list[dict[str, str]]) -> str:
    if pending_approvals:
        first = pending_approvals[0]
        return f"Review approval {first.get('approval_id') or ''} for {first.get('case_id')}: {first.get('action_approved') or first.get('proposed_action') or 'approval action'}."
    for item in analyzed:
        if item["case"].get("status") == "NEW":
            return f"Fast-kill and deep-read {item['case'].get('case_id')} before supplier or pricing work."
    if plugin_issues:
        return f"Fix/confirm tool issue: {plugin_issues[0].get('plugin_or_tool') or plugin_issues[0].get('runtime')}."
    return "Let the morning radar continue and focus today on cases with verified source evidence and at least two quote proofs."


def run_refresh_steps(args: argparse.Namespace) -> list[dict[str, Any]]:
    py = sys.executable or "python3"
    steps: list[tuple[str, list[str], int]] = [
        ("Schema validation", [py, "scripts/validate_register_schemas.py"], 60),
    ]
    if not args.skip_intake:
        steps.append((
            "Public source/task intake",
            [py, "scripts/run_external_task_intake.py", "--limit", str(args.limit), "--timeout", str(args.timeout), "--record-event"],
            max(90, args.limit * args.timeout + 30),
        ))
    steps.extend([
        ("Demand signal digest", [py, "scripts/generate_demand_signal_digest.py", "--top", "20"], 60),
        ("Export buyer demand verification", [py, "scripts/verify_buyer_demand.py", "--all"], 90),
        ("Buyer research horizon", [py, "scripts/research_buyer_horizon.py"], 90),
        ("Buyer demand brief", [py, "scripts/generate_buyer_demand_brief.py", "--date", today_compact()], 60),
        ("Standard daily brief", [py, "scripts/generate_daily_brief.py", "--date", today_compact()], 60),
    ])
    results = []
    for label, command, timeout in steps:
        results.append(run_step(label, command, timeout=timeout))
    return results


def build_payload(analyzed: list[dict[str, Any]], command_results: list[dict[str, Any]], latest_artifacts: dict[str, str]) -> dict[str, Any]:
    serializable_cases = []
    for item in analyzed:
        serializable_cases.append({
            "case_id": item["case"].get("case_id"),
            "workflow_type": item["case"].get("workflow_type"),
            "status": item["case"].get("status"),
            "score": item["score"],
            "supplier_candidate_count": item["supplier_candidate_count"],
            "supplier_source_type_count": item["supplier_source_type_count"],
            "quote_counts": item["pricing"]["counts"],
            "pricing_status": item["pricing"]["status"],
            "supply_chain_doc": item["supply_chain_doc"],
            "routing": item["routing"],
        })
    return {
        "generated_at": now_local().isoformat(timespec="seconds"),
        "safety": "internal_report_only_supplier_outreach_and_portal_access_standing_authorized_no_buyer_bid_payment_final_commitment",
        "cases": serializable_cases,
        "steps": command_results,
        "latest_artifacts": latest_artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Tender Export OS morning opportunity intelligence pipeline")
    parser.add_argument("--limit", type=int, default=8, help="Max public sources for safe intake probe")
    parser.add_argument("--timeout", type=int, default=8, help="HTTP timeout per public intake probe")
    parser.add_argument("--max-cases", type=int, default=12, help="Max active cases to analyze in the HTML report")
    parser.add_argument("--skip-intake", action="store_true", help="Skip public external intake sub-step")
    parser.add_argument("--no-log", action="store_true", help="Do not append orchestrator run log/event")
    parser.add_argument("--no-media-line", action="store_true", help="Do not print MEDIA:<html_path> line for gateway file delivery")
    args = parser.parse_args()

    started = time.time()
    run_id = f"RUN-{now_local().strftime('%Y%m%d%H%M%S')}-OPP-INTEL"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SUPPLY_CHAIN_DIR.mkdir(parents=True, exist_ok=True)

    command_results = run_refresh_steps(args)

    cases = load_csv("master_cases.csv")
    suppliers = load_csv("supplier_master.csv")
    quotes = load_csv("quote_master.csv")
    approvals = load_csv("approvals_receipts.csv")
    source_health = load_csv("source_health.csv")
    plugin_health = load_csv("plugin_health.csv")
    rfqs = load_csv("rfq_master.csv")

    analyzed = analyze_cases(cases, suppliers, quotes, approvals, rfqs, args.max_cases)
    latest_artifacts = {
        "external intake report": rel(latest_file("outputs/external_intake/external_intake_report_*.md") or ""),
        "demand signal digest": rel(latest_file("outputs/demand_signals/demand_signal_digest_*.md") or ""),
        "buyer demand brief": rel(latest_file(f"outputs/buyer_demand/buyer_demand_brief_{today_compact()}.html") or ""),
        "standard daily brief": rel(latest_file(f"outputs/daily_briefs/brief_{today_compact()}.html") or ""),
        "latest GOV/source scan": rel(latest_file("outputs/source_scans/gov_radar_batch_*.json") or ""),
        "latest EXPORT/source scan": rel(latest_file("outputs/source_scans/export_rfq_batch_scan_*.json") or latest_file("outputs/source_scans/export_scan_probe_*.json") or ""),
    }
    external_intake = load_latest_json("outputs/external_intake/external_intake_report_*.json")

    html_path = OUTPUT_DIR / f"daily_opportunity_intelligence_{today_compact()}.html"
    json_path = OUTPUT_DIR / f"daily_opportunity_intelligence_{today_compact()}.json"
    render_html_report(
        analyzed,
        cases,
        approvals,
        source_health,
        plugin_health,
        command_results,
        latest_artifacts,
        external_intake,
        html_path,
    )
    payload = build_payload(analyzed, command_results, latest_artifacts)
    payload["html_report"] = rel(html_path)
    payload["json_report"] = rel(json_path)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    errors = sum(1 for step in command_results if not step["ok"])
    warnings = errors
    for item in analyzed:
        if item["pricing"]["status"] != "INTERNAL_PRICING_ASSIST_READY_NOT_FINAL":
            warnings += 1
        if item["supplier_candidate_count"] < 5 or item["supplier_source_type_count"] < 3:
            warnings += 1
    external_summary = external_intake.get("summary") or {}
    sources_checked = external_summary.get("sources_checked", 0) or 0
    sources_failed = external_summary.get("failed", 0) or 0
    status = "SUCCESS" if errors == 0 else "SUCCESS_WITH_WARNINGS"

    if not args.no_log:
        n = now_local()
        write_run_log({
            "run_id": run_id,
            "run_date": n.date().isoformat(),
            "run_time": n.strftime("%H:%M:%S"),
            "agent_name": "morning_opportunity_intelligence_orchestrator",
            "trigger_type": "manual_or_cron_daily_html_pipeline",
            "cases_processed": len(analyzed),
            "cases_created": 0,
            "cases_rejected": 0,
            "cases_updated": 0,
            "sources_checked": sources_checked,
            "sources_failed": sources_failed,
            "actions_taken": "safe_public_intake;requirements_pass;supplier_5_3_2_pass;supply_chain_docs;pricing_assist;blind_spot_routing;html_report",
            "approval_cards_created": 0,
            "receipts_created": 1 + len(analyzed),
            "errors": errors,
            "warnings": warnings,
            "runtime_seconds": int(time.time() - started),
            "status": status,
            "notes": f"HTML={rel(html_path)} JSON={rel(json_path)} supply_chain_docs={len(analyzed)}; no external business action executed.",
        })
        if append_event:
            try:
                append_event(
                    "system.snapshot_completed",
                    "morning_opportunity_intelligence_orchestrator",
                    object_type="system",
                    object_id=rel(html_path),
                    payload={
                        "run_id": run_id,
                        "cases_analyzed": len(analyzed),
                        "html_report": rel(html_path),
                        "json_report": rel(json_path),
                        "supply_chain_docs": [item["supply_chain_doc"] for item in analyzed],
                        "errors": errors,
                        "warnings": warnings,
                    },
                    citations=[rel(html_path), rel(json_path), "data/master_cases.csv", "data/supplier_master.csv", "data/quote_master.csv"],
                )
            except Exception as exc:  # noqa: BLE001
                print(f"Warning: could not append event ledger row: {exc}", file=sys.stderr)

    abs_html = html_path.resolve()
    print("Tender Export OS daily opportunity intelligence complete.")
    print(f"Status: {status}; cases_analyzed={len(analyzed)}; step_errors={errors}; warnings={warnings}")
    print(f"HTML report: {abs_html}")
    print(f"JSON report: {json_path.resolve()}")
    print(f"Supply-chain docs: {SUPPLY_CHAIN_DIR.resolve()}")
    print("Safety: report-only run. Supplier outreach and portal login/signup are standing-authorized by policy, but this run did not execute them; buyer sends, submissions, uploads, payments, DSC, final classification/origin claims, and final price commitments remain approval-gated.")
    if not args.no_media_line:
        print(f"MEDIA:{abs_html}")
    return 0 if errors == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
