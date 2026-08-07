#!/usr/bin/env python3
"""Stage foreign-retailer catalogue signals and approval-gated outreach drafts."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

try:
    from approval_lifecycle import approval_timeout_at
    from event_ledger import append_event
    from generate_approval_cards import approval_scope_hash, render_card, structured_card
except ModuleNotFoundError:  # pragma: no cover
    from scripts.approval_lifecycle import approval_timeout_at
    from scripts.event_ledger import append_event
    from scripts.generate_approval_cards import approval_scope_hash, render_card, structured_card


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "buyer_market_research"
APPROVAL_TEMPLATE = PROJECT_ROOT / "templates" / "approval_card.html"
CONTACT_SCOPES = {"UNKNOWN", "GENERAL_CONTACT", "PROCUREMENT", "BUYING", "TRADE_ACCOUNT"}
EVIDENCE_LEVELS = {
    "CATALOG_OBSERVED",
    "COMPANY_AND_CATALOG_VERIFIED",
    "CONTACT_PATH_VERIFIED",
    "BUYER_RESPONSE",
    "RFQ_VERIFIED",
}
DEMAND_CONFIDENCE = {"LOW", "MEDIUM", "HIGH"}
HTTPS_RE = re.compile(r"^https://[^\s]+$", re.I)
PROHIBITED_COMMITMENT_PATTERNS = {
    "final price": ("our price is", "we quote", "price is"),
    "delivery commitment": ("we will deliver", "delivery in ", "lead time is"),
    "payment commitment": ("payment terms are", "we accept payment"),
    "certification claim": ("we are certified", "certified for"),
    "origin claim": ("country of origin is", "origin is guaranteed"),
    "availability guarantee": ("we guarantee availability", "available immediately"),
}


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def stable_hash(*values: str, length: int = 12) -> str:
    normalized = "|".join(str(value or "").strip().lower() for value in values)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:length].upper()


def as_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def normalize_item(raw: dict[str, Any], *, category_name: str) -> dict[str, Any]:
    item = dict(raw)
    item["category_name"] = str(item.get("category_name") or category_name).strip()
    item["outreach_category"] = str(item.get("outreach_category") or item["category_name"]).strip()
    item["company_name"] = str(item.get("company_name") or "").strip()
    item["country"] = str(item.get("country") or "").strip()
    item["company_type"] = str(item.get("company_type") or "Retailer").strip()
    item["website_url"] = str(item.get("website_url") or "").strip()
    item["catalog_url"] = str(item.get("catalog_url") or "").strip()
    item["contact_page_url"] = str(item.get("contact_page_url") or "").strip()
    item["public_contact"] = str(item.get("public_contact") or "").strip()
    item["contact_scope"] = str(item.get("contact_scope") or "UNKNOWN").strip().upper()
    item["evidence_level"] = str(item.get("evidence_level") or "CATALOG_OBSERVED").strip().upper()
    item["demand_confidence"] = str(item.get("demand_confidence") or "LOW").strip().upper()
    item["matching_products"] = [product for product in as_list(item.get("matching_products")) if isinstance(product, dict)]
    item["source_citations"] = [str(url).strip() for url in as_list(item.get("source_citations")) if str(url).strip()]
    try:
        item["market_fit_score"] = max(0, min(100, int(float(item.get("market_fit_score") or 0))))
    except (TypeError, ValueError):
        item["market_fit_score"] = 0

    if item["public_contact"] and item["contact_scope"] in {"PROCUREMENT", "BUYING"}:
        item["contact_status"] = "VERIFIED_BUYING_CONTACT"
    elif item["public_contact"] or item["contact_page_url"]:
        item["contact_status"] = "PUBLIC_GENERAL_CONTACT"
    else:
        item["contact_status"] = "MISSING"

    if item["market_fit_score"] >= 65 and item["contact_status"] != "MISSING":
        item["next_safe_action"] = "DRAFT_OUTREACH_FOR_APPROVAL"
    elif item["contact_status"] == "MISSING":
        item["next_safe_action"] = "VERIFY_PUBLIC_CONTACT_PATH"
    else:
        item["next_safe_action"] = "RESEARCH_MORE"
    base_note = str(item.get("assortment_evidence") or "").strip()
    item["personalization_angle"] = str(item.get("personalization_angle") or base_note).strip()
    item["assortment_evidence_note"] = f"{base_note} Catalogue fit is a demand hypothesis, not an RFQ or proof that the company wants a new supplier.".strip()
    item["demand_claim_status"] = "CATALOGUE_HYPOTHESIS"
    return item


def validate_item(item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("company_name", "country", "company_type", "website_url", "catalog_url", "category_name"):
        if not item.get(field):
            errors.append(f"missing required field {field}")
    for field in ("website_url", "catalog_url", "contact_page_url"):
        value = str(item.get(field) or "")
        if value and not HTTPS_RE.match(value):
            errors.append(f"{field} must be a public HTTPS URL")
    if not item.get("matching_products"):
        errors.append("at least one matching product is required")
    citations = set(item.get("source_citations") or [])
    if item.get("catalog_url") not in citations:
        errors.append("catalog_url must be cited")
    for product in item.get("matching_products") or []:
        product_url = str(product.get("product_url") or "")
        if not product.get("product_name") or not product_url:
            errors.append("each matching product requires product_name and product_url")
        elif product_url not in citations:
            errors.append(f"matching product must be cited: {product_url}")
    if item.get("public_contact") and (
        not item.get("contact_page_url") or item.get("contact_page_url") not in citations
    ):
        errors.append("public_contact requires cited contact_page_url")
    if item.get("contact_scope") not in CONTACT_SCOPES:
        errors.append(f"unsupported contact_scope {item.get('contact_scope')}")
    if item.get("evidence_level") not in EVIDENCE_LEVELS:
        errors.append(f"unsupported evidence_level {item.get('evidence_level')}")
    if item.get("demand_confidence") not in DEMAND_CONFIDENCE:
        errors.append(f"unsupported demand_confidence {item.get('demand_confidence')}")
    return errors


def build_outreach_draft(item: dict[str, Any], *, outreach_id: str) -> dict[str, Any]:
    product_names = [str(product.get("product_name") or "").strip() for product in item.get("matching_products", [])]
    product_phrase = ", ".join(name for name in product_names[:3] if name) or item["category_name"]
    subject = f"Indian artisan {item['outreach_category'].lower()} for {item['company_name']}"
    opt_out_sentence = "If this is not relevant, please let me know and I will not follow up."
    body = f"""Hello {item['company_name']} team,

I noticed {product_phrase} in your public catalogue. {item['personalization_angle']}

We may be able to assemble a tightly curated India-sourced selection in {item['outreach_category'].lower()}, backed by a verified producer shortlist. Materials, production capacity, MOQ, documentation, and lead-time evidence would be clearly separated from assumptions. Would you be open to reviewing a small, relevant selection? If so, could you point me to the person responsible for sourcing or buying this category?

No price, delivery date, payment term, certification, origin, or product availability is being committed in this introduction. Those details would be verified before any quotation.

{opt_out_sentence}

Regards,
Raghav
"""
    prohibited_claim_check = check_prohibited_claims(body)
    follow_up_sequence = [
        {
            "step": 1,
            "timing": "Only after a fresh owner approval and no stop signal exists.",
            "body": "Hello, I am following up on the factual introduction below. If this category is not relevant, please let me know and I will close the thread.",
            "sendable": False,
            "fresh_approval_required": True,
        },
        {
            "step": 2,
            "timing": "Only after a second fresh owner approval and only if the buyer has not opted out, bounced, or declined.",
            "body": "Hello, I will close this thread after this note unless a relevant sourcing or buying contact would like a factual product overview.",
            "sendable": False,
            "fresh_approval_required": True,
        },
    ]
    return {
        "outreach_id": outreach_id,
        "subject": subject,
        "body": body,
        "personalization_evidence": product_names[:3],
        "personalization_evidence_map": [
            {
                "product_name": str(product.get("product_name") or ""),
                "product_url": str(product.get("product_url") or ""),
                "evidence": str(product.get("evidence") or ""),
            }
            for product in item.get("matching_products", [])
        ],
        "follow_up_sequence": follow_up_sequence,
        "opt_out_sentence": opt_out_sentence,
        "prohibited_claim_check": prohibited_claim_check,
        "content_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "approval_required": True,
        "external_action_executed": False,
    }


def check_prohibited_claims(body: str) -> dict[str, Any]:
    normalized = " ".join(body.lower().split())
    findings = [
        category
        for category, patterns in PROHIBITED_COMMITMENT_PATTERNS.items()
        if any(pattern in normalized for pattern in patterns)
    ]
    return {"passed": not findings, "findings": findings}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def upsert_csv(path: Path, key: str, row: dict[str, Any]) -> bool:
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        if fcntl is not None:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            headers, rows = read_csv(path)
            normalized = {
                header: "" if row.get(header) is None else str(row.get(header, ""))
                for header in headers
            }
            created = True
            for index, existing in enumerate(rows):
                if existing.get(key) == normalized.get(key):
                    rows[index] = normalized
                    created = False
                    break
            if created:
                rows.append(normalized)
            with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as handle:
                temporary = Path(handle.name)
                writer = csv.DictWriter(handle, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            return created
        finally:
            if fcntl is not None:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def blank_row(path: Path) -> dict[str, str]:
    headers, _ = read_csv(path)
    return {header: "" for header in headers}


def event_for_row(object_type: str, object_id: str, row: dict[str, Any], created: bool, citations: list[str], case_id: str = "") -> None:
    event_type = f"{object_type}.{'created' if created else 'updated'}"
    payload: dict[str, Any] = {"updates": row}
    if object_type == "case":
        payload["status"] = row.get("status", "")
    digest = stable_hash(json.dumps(row, sort_keys=True, ensure_ascii=False), length=20)
    append_event(
        event_type,
        "buyer_market_research_stager",
        case_id=case_id,
        object_type=object_type,
        object_id=object_id,
        source="buyer_market_deep_research",
        payload=payload,
        citations=citations,
        idempotency_key=f"{event_type}:{object_id}:{digest}",
    )


def build_rows(item: dict[str, Any], meta: dict[str, Any], draft_path: str) -> dict[str, dict[str, Any]]:
    category_code = str(meta.get("category_code") or "EXP-CATEGORY")
    key = stable_hash(item["company_name"], item["country"], category_code)
    signal_id = f"SIG-{key}"
    buyer_id = f"BUY-TARGET-{key[:10]}"
    case_id = f"EXP-TA-{key[:10]}"
    outreach_id = f"OUT-{key}"
    approval_id = f"APR-OUT-{key[:10]}"
    created_at = today()
    matching_products = "; ".join(str(product.get("product_name") or "") for product in item["matching_products"])
    citations = ";".join(item["source_citations"])

    signal = blank_row(DATA_DIR / "buyer_demand_signals.csv")
    signal.update(
        {
            "signal_id": signal_id,
            "research_report_id": meta.get("research_report_id", ""),
            "category_code": category_code,
            "category_name": item["category_name"],
            "company_name": item["company_name"],
            "country": item["country"],
            "company_type": item["company_type"],
            "website_url": item["website_url"],
            "catalog_url": item["catalog_url"],
            "matching_products": matching_products,
            "assortment_evidence": item["assortment_evidence_note"],
            "price_positioning": item.get("price_positioning", "UNKNOWN"),
            "contact_page_url": item["contact_page_url"],
            "public_contact": item["public_contact"],
            "contact_scope": item["contact_scope"],
            "contact_status": item["contact_status"],
            "evidence_level": item["evidence_level"],
            "market_fit_score": item["market_fit_score"],
            "demand_confidence": item["demand_confidence"],
            "source_citations": citations,
            "next_safe_action": item["next_safe_action"],
            "case_id": case_id,
            "buyer_id": buyer_id,
            "created_at": created_at,
            "updated_at": created_at,
        }
    )

    buyer = blank_row(DATA_DIR / "buyer_master.csv")
    buyer.update(
        {
            "buyer_id": buyer_id,
            "buyer_name": item["company_name"],
            "buyer_type": item["company_type"],
            "country": item["country"],
            "source_name": "Foreign retailer catalogue research",
            "source_url": item["website_url"],
            "contact_path": item["public_contact"] or item["contact_page_url"],
            "identity_status": "VISIBLE",
            "verification_status": "BUYER_VISIBLE",
            "buyer_stage": "BUYER_VISIBLE",
            "buyer_score": item["market_fit_score"],
            "source_reliability_score": "",
            "evidence_links": citations,
            "notes": item["assortment_evidence_note"] + " Legal-entity, sanctions, and buyer-specific demand verification remain open.",
            "created_at": created_at,
            "updated_at": created_at,
        }
    )

    case = blank_row(DATA_DIR / "master_cases.csv")
    case.update(
        {
            "case_id": case_id,
            "workflow_type": "EXPORT",
            "source_name": "Foreign retailer catalogue research",
            "source_url": item["catalog_url"],
            "opportunity_title": f"Strategic account outreach: {item['company_name']} — {item['category_name']}",
            "buyer_name": item["company_name"],
            "buyer_type": item["company_type"],
            "product_or_service": item["category_name"],
            "status": "WATCHLIST",
            "score_export": item["market_fit_score"],
            "approval_status": "PENDING",
            "buyer_country": item["country"],
            "buyer_credibility_score": item["market_fit_score"],
            "notes": f"Catalogue-fit strategic account only; not an RFQ or confirmed demand. Outreach draft={draft_path}",
            "created_at": created_at,
            "updated_at": created_at,
            "created_by_agent": "buyer_market_research_stager",
            "evidence_level": "DETAIL_PAGE_READ",
        }
    )

    outreach = blank_row(DATA_DIR / "outreach_queue.csv")
    outreach.update(
        {
            "outreach_id": outreach_id,
            "case_id": case_id,
            "buyer_id": buyer_id,
            "signal_id": signal_id,
            "channel": "EMAIL" if "@" in item["public_contact"] else "CONTACT_FORM",
            "verified_contact": item["public_contact"] or item["contact_page_url"],
            "contact_scope": item["contact_scope"],
            "subject": build_outreach_draft(item, outreach_id=outreach_id)["subject"],
            "draft_path": draft_path,
            "approval_id": approval_id,
            "approval_status": "PENDING",
            "send_status": "DRAFT_ONLY",
            "reply_status": "NO_REPLY",
            "follow_up_count": 0,
            "created_at": created_at,
            "updated_at": created_at,
        }
    )

    requested_at = now_iso()
    approval = blank_row(DATA_DIR / "approvals_receipts.csv")
    approval.update(
        {
            "approval_id": approval_id,
            "case_id": case_id,
            "workflow_type": "EXPORT",
            "action_approved": "send_buyer_introductory_outreach",
            "proposed_by_agent": "buyer_market_research_stager",
            "approval_card_path": f"receipts/approvals/{case_id}_{outreach_id}_approval_card.html",
            "approval_status": "PENDING",
            "external_effect": "NONE_DECISION_ONLY",
            "notes": f"Approve only the first factual introductory outreach draft at {draft_path}; no quote, delivery, payment, classification, origin, or follow-up is approved.",
            "requested_at": requested_at,
            "approval_timeout_at": approval_timeout_at(requested_at),
        }
    )
    approval["scope_hash"] = approval_scope_hash(approval, case)
    return {"signal": signal, "buyer": buyer, "case": case, "outreach": outreach, "approval": approval}


def write_draft(item: dict[str, Any], output_dir: Path, outreach_id: str) -> tuple[dict[str, Any], Path]:
    draft = build_outreach_draft(item, outreach_id=outreach_id)
    path = output_dir / "drafts" / f"{outreach_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {draft['subject']}\n\n{draft['body']}\n---\nInternal first-contact draft only. Owner approval required before external use. Follow-ups require fresh owner approval.\n",
        encoding="utf-8",
    )
    metadata_path = path.with_suffix(".json")
    metadata_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    draft["metadata_path"] = relative(metadata_path)
    return draft, path


def write_approval_card(approval: dict[str, Any], case: dict[str, Any], citations: list[str]) -> tuple[Path, Path]:
    html_path = PROJECT_ROOT / approval["approval_card_path"]
    json_path = html_path.with_suffix(".json")
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_card(APPROVAL_TEMPLATE.read_text(encoding="utf-8"), approval, case), encoding="utf-8")
    json_path.write_text(json.dumps(structured_card(approval, case, html_path, json_path), indent=2), encoding="utf-8")
    append_event(
        "approval.card_created",
        "buyer_market_research_stager",
        case_id=case["case_id"],
        object_type="approval",
        object_id=approval["approval_id"],
        source="buyer_market_deep_research",
        payload={"html_path": relative(html_path), "json_path": relative(json_path)},
        citations=[relative(html_path), relative(json_path), *citations],
        idempotency_key=f"approval-card:{approval['approval_id']}:{approval['scope_hash']}",
    )
    return html_path, json_path


def stage(input_path: Path, *, persist: bool) -> tuple[dict[str, Any], Path]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    meta = {
        "research_report_id": payload.get("research_report_id", ""),
        "category_code": payload.get("category_code", ""),
        "category_name": payload.get("category_name", ""),
    }
    if not all(meta.values()) or not isinstance(payload.get("items"), list):
        raise ValueError("research_report_id, category_code, category_name, and items[] are required")
    normalized = [normalize_item(item, category_name=meta["category_name"]) for item in payload["items"] if isinstance(item, dict)]
    errors = [f"item {index}: {error}" for index, item in enumerate(normalized, 1) for error in validate_item(item)]
    if errors:
        raise ValueError("; ".join(errors))

    output_dir = OUTPUT_ROOT / safe_report_id(meta["research_report_id"])
    output_dir.mkdir(parents=True, exist_ok=True)
    staged_items = []
    for item in normalized:
        key = stable_hash(item["company_name"], item["country"], meta["category_code"])
        outreach_id = f"OUT-{key}"
        draft, draft_path = write_draft(item, output_dir, outreach_id)
        rows = build_rows(item, meta, relative(draft_path))
        staged = {
            "company_name": item["company_name"],
            "signal_id": rows["signal"]["signal_id"],
            "buyer_id": rows["buyer"]["buyer_id"],
            "case_id": rows["case"]["case_id"],
            "outreach_id": rows["outreach"]["outreach_id"],
            "approval_id": rows["approval"]["approval_id"],
            "draft_path": relative(draft_path),
            "next_safe_action": item["next_safe_action"],
            "persisted": persist,
            "external_action_executed": False,
        }
        if persist:
            citations = [relative(input_path), *item["source_citations"], relative(draft_path)]
            register_specs = [
                ("buyer_demand_signal", DATA_DIR / "buyer_demand_signals.csv", "signal_id", rows["signal"], ""),
                ("buyer", DATA_DIR / "buyer_master.csv", "buyer_id", rows["buyer"], rows["case"]["case_id"]),
                ("case", DATA_DIR / "master_cases.csv", "case_id", rows["case"], rows["case"]["case_id"]),
                ("outreach", DATA_DIR / "outreach_queue.csv", "outreach_id", rows["outreach"], rows["case"]["case_id"]),
                ("approval", DATA_DIR / "approvals_receipts.csv", "approval_id", rows["approval"], rows["case"]["case_id"]),
            ]
            for object_type, path, id_field, row, case_id in register_specs:
                created = upsert_csv(path, id_field, row)
                event_for_row(object_type, row[id_field], row, created, citations, case_id=case_id)
            html_path, json_path = write_approval_card(rows["approval"], rows["case"], citations)
            staged["approval_card_html"] = relative(html_path)
            staged["approval_card_json"] = relative(json_path)
        staged_items.append(staged)

    result = {
        "research_report_id": meta["research_report_id"],
        "category_code": meta["category_code"],
        "category_name": meta["category_name"],
        "mode": "STAGED" if persist else "DRY_RUN",
        "item_count": len(staged_items),
        "items": staged_items,
        "external_action_executed": False,
        "safety": "Catalogue signals are hypotheses. Drafts and follow-ups require owner approval; no message was sent.",
    }
    result_path = output_dir / ("staged_result.json" if persist else "dry_run_result.json")
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result, result_path


def safe_report_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "buyer-market-research"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage buyer-market Deep Research and create approval-gated drafts")
    parser.add_argument("--input", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--stage", action="store_true", help="Persist projections, events, drafts, and approval cards")
    mode.add_argument("--dry-run", action="store_true", help="Validate and render previews only (default)")
    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    result, path = stage(input_path, persist=args.stage)
    print(json.dumps({"mode": result["mode"], "items": result["item_count"], "result": relative(path), "external_action_executed": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
