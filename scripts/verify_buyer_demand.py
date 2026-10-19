#!/usr/bin/env python3
"""Classify export buyer demand evidence into the staged buyer/RFQ funnel."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "buyer_verification"

BUYER_FIELDS = [
    "buyer_id", "buyer_name", "buyer_type", "country", "source_name", "source_url",
    "contact_path", "identity_status", "verification_status", "buyer_stage",
    "buyer_score", "source_reliability_score", "fraud_flags", "evidence_links",
    "notes", "created_at", "updated_at",
]
RFQ_FIELDS = [
    "rfq_id", "case_id", "buyer_id", "source_name", "source_url", "rfq_reference",
    "product_or_service", "quantity", "unit", "buyer_country", "deadline_date",
    "payment_terms", "incoterms", "evidence_status", "rfq_stage", "rfq_score",
    "market_fit_score", "source_reliability_score", "missing_evidence",
    "evidence_links", "notes", "created_at", "updated_at",
]


def today() -> str:
    return dt.date.today().isoformat()


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def upsert(rows: list[dict], key: str, row: dict) -> list[dict]:
    updated = False
    out = []
    for existing in rows:
        if existing.get(key) == row.get(key):
            merged = dict(existing)
            merged.update(row)
            out.append(merged)
            updated = True
        else:
            out.append(existing)
    if not updated:
        out.append(row)
    return out


def normalize_url(url: str) -> str:
    return (url or "").strip()


def is_generic_alibaba(case: dict) -> bool:
    source_url = normalize_url(case.get("source_url", ""))
    parsed = urlparse(source_url)
    return "alibaba" in (case.get("source_name", "") + parsed.netloc).lower() and parsed.path in {"", "/"}


def extract_reference(case: dict) -> str:
    text = " ".join([case.get("opportunity_title", ""), case.get("notes", ""), case.get("source_url", "")])
    for pattern in [r"UNDP-[A-Z]{3}-[0-9-]+", r"nego_id=([0-9]+)", r"RFQ[-_ A-Z0-9/]+"]:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return ""


def contact_path(case: dict) -> str:
    notes = case.get("notes", "")
    email = re.search(r"[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}", notes)
    if email:
        return email.group(0)
    if "Quantum" in notes or "portal" in notes.lower():
        return "public procurement portal"
    return ""


def classify_case(case: dict) -> dict:
    buyer_name = case.get("buyer_name", "").strip() or "Unknown buyer"
    source_name = case.get("source_name", "")
    source_url = normalize_url(case.get("source_url", ""))
    country = case.get("buyer_country", "") or case.get("delivery_location", "")
    notes = case.get("notes", "")
    missing = []
    buyer_type = "Company"
    identity_status = "VISIBLE"
    stage = "BUYER_VISIBLE"
    evidence_status = "PARTIAL"
    buyer_score = 45
    rfq_score = 40
    source_score = 45
    market_fit = 55
    fraud_flags = ""
    rfq_notes = "Public-source buyer/RFQ evidence is partial."

    lower = " ".join([buyer_name, source_name, source_url, notes]).lower()
    has_product = bool(case.get("product_or_service"))
    has_country = bool(country)
    has_deadline = bool(case.get("deadline_date"))
    has_quantity = bool(case.get("quantity"))

    if not source_url:
        stage = "RAW_LEAD"
        identity_status = "UNKNOWN"
        evidence_status = "MISSING"
        buyer_score = 10
        rfq_score = 0
        source_score = 10
        missing.extend(["original source URL", "buyer legal identity", "buyer-specific RFQ proof"])
        rfq_notes = "No public buyer-specific source is available."
    elif is_generic_alibaba(case):
        stage = "RAW_LEAD"
        identity_status = "UNKNOWN"
        evidence_status = "MISSING"
        buyer_score = 15
        rfq_score = 5
        source_score = 25
        missing.extend(["buyer-specific Alibaba RFQ URL", "buyer identity proof", "RFQ artifact or screenshot"])
        rfq_notes = "Generic marketplace landing page is not demand proof."
    elif "tradekey" in lower or "hidden" in lower or "masked" in lower:
        stage = "BUYER_VISIBLE"
        identity_status = "MASKED"
        evidence_status = "MARKETPLACE_MASKED"
        buyer_type = "Marketplace buyer lead"
        buyer_score = 35
        rfq_score = 35 if has_product and has_country else 25
        source_score = 40
        fraud_flags = "masked_identity"
        missing.extend(["unmasked buyer legal name", "direct contact path", "quantity", "deadline"])
        rfq_notes = "Marketplace lead remains weak until buyer identity and RFQ details are visible."
    elif "undp" in lower and source_url and has_deadline and has_product and has_country:
        stage = "RFQ_VERIFIED"
        identity_status = "INSTITUTION"
        evidence_status = "RFQ_VERIFIED"
        buyer_type = "Multilateral institution"
        buyer_score = 88
        rfq_score = 82 if has_quantity else 76
        source_score = 92
        market_fit = 72
        rfq_notes = "Public institutional notice has buyer, product, country, deadline, and portal/contact path."
        if not contact_path(case):
            missing.append("named portal or contact path")
    else:
        if not has_product:
            missing.append("product")
        if not has_country:
            missing.append("destination country")
        if not has_deadline:
            missing.append("deadline")
        if not contact_path(case):
            missing.append("contact path")
        if buyer_name.lower().startswith("unknown"):
            stage = "RAW_LEAD"
            identity_status = "UNKNOWN"
            buyer_score = 20
        elif contact_path(case) and source_url:
            stage = "BUYER_VERIFIED"
            identity_status = "VERIFIED"
            buyer_score = 60
            source_score = 55

    if not missing:
        missing = ["none"]

    buyer_id = f"BUY-{case.get('case_id')}"
    rfq_id = f"RFQ-{case.get('case_id')}"
    evidence_links = source_url
    created = case.get("created_at") or today()
    updated = today()

    buyer = {
        "buyer_id": buyer_id,
        "buyer_name": buyer_name,
        "buyer_type": buyer_type,
        "country": country,
        "source_name": source_name,
        "source_url": source_url,
        "contact_path": contact_path(case),
        "identity_status": identity_status,
        "verification_status": stage,
        "buyer_stage": stage,
        "buyer_score": buyer_score,
        "source_reliability_score": source_score,
        "fraud_flags": fraud_flags,
        "evidence_links": evidence_links,
        "notes": rfq_notes,
        "created_at": created,
        "updated_at": updated,
    }
    rfq = {
        "rfq_id": rfq_id,
        "case_id": case.get("case_id", ""),
        "buyer_id": buyer_id,
        "source_name": source_name,
        "source_url": source_url,
        "rfq_reference": extract_reference(case),
        "product_or_service": case.get("product_or_service", ""),
        "quantity": case.get("quantity", ""),
        "unit": case.get("unit", ""),
        "buyer_country": country,
        "deadline_date": case.get("deadline_date", ""),
        "payment_terms": case.get("payment_terms", ""),
        "incoterms": case.get("incoterms", ""),
        "evidence_status": evidence_status,
        "rfq_stage": stage,
        "rfq_score": rfq_score,
        "market_fit_score": market_fit,
        "source_reliability_score": source_score,
        "missing_evidence": "; ".join(missing),
        "evidence_links": evidence_links,
        "notes": rfq_notes,
        "created_at": created,
        "updated_at": updated,
    }
    return {"case_id": case.get("case_id", ""), "stage": stage, "buyer": buyer, "rfq": rfq}


def write_case_note(result: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rfq = result["rfq"]
    buyer = result["buyer"]
    path = OUTPUT_DIR / f"{result['case_id']}.md"
    lines = [
        f"# Buyer Demand Verification - {result['case_id']}",
        "",
        f"- Stage: {result['stage']}",
        f"- Buyer: {buyer['buyer_name']}",
        f"- Buyer score: {buyer['buyer_score']}",
        f"- RFQ score: {rfq['rfq_score']}",
        f"- Source reliability score: {rfq['source_reliability_score']}",
        f"- Evidence status: {rfq['evidence_status']}",
        f"- Missing evidence: {rfq['missing_evidence']}",
        f"- Source: {rfq['source_url'] or 'missing'}",
        "",
        "No external contact, portal login, submission, quote send, payment, or owner approval decision was performed.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def append_run_log(processed: int, updated: int, dry_run: bool) -> None:
    path = DATA_DIR / "agent_run_log.csv"
    file_exists = path.exists()
    row = {
        "run_id": f"RUN-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-BUYER-DEMAND",
        "run_date": today(),
        "run_time": dt.datetime.now().strftime("%H:%M:%S"),
        "agent_name": "buyer_verification_agent",
        "trigger_type": "manual",
        "cases_processed": processed,
        "cases_created": 0,
        "cases_rejected": 0,
        "cases_updated": updated,
        "sources_checked": 0,
        "sources_failed": 0,
        "actions_taken": "verify_buyer_demand_dry_run" if dry_run else "verify_buyer_demand",
        "approval_cards_created": 0,
        "receipts_created": updated,
        "errors": 0,
        "warnings": 0,
        "runtime_seconds": 0,
        "status": "SUCCESS",
        "notes": "Buyer/RFQ demand stages refreshed; no external actions.",
    }
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify export buyer demand evidence")
    parser.add_argument("--case-id", help="Verify one export case")
    parser.add_argument("--all", action="store_true", help="Verify all export cases")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing registers")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    args = parser.parse_args()

    if not args.case_id and not args.all:
        print("Provide --case-id or --all.")
        return 2

    cases = [
        case for case in load_csv(DATA_DIR / "master_cases.csv")
        if case.get("workflow_type") == "EXPORT" and (args.all or case.get("case_id") == args.case_id)
    ]
    if not cases:
        print("No matching export cases found.")
        return 1

    results = [classify_case(case) for case in cases]

    if not args.dry_run:
        buyers = load_csv(DATA_DIR / "buyer_master.csv")
        rfqs = load_csv(DATA_DIR / "rfq_master.csv")
        for result in results:
            buyers = upsert(buyers, "buyer_id", result["buyer"])
            rfqs = upsert(rfqs, "rfq_id", result["rfq"])
            note_path = write_case_note(result)
            append_event(
                "buyer.created",
                "verify_buyer_demand",
                case_id=result["case_id"],
                object_type="buyer",
                object_id=result["buyer"]["buyer_id"],
                payload={"updates": result["buyer"]},
                citations=[str(note_path.relative_to(PROJECT_ROOT)), result["buyer"].get("source_url", "")],
            )
            append_event(
                "rfq.created",
                "verify_buyer_demand",
                case_id=result["case_id"],
                object_type="rfq",
                object_id=result["rfq"]["rfq_id"],
                payload={"updates": result["rfq"]},
                citations=[str(note_path.relative_to(PROJECT_ROOT)), result["rfq"].get("source_url", "")],
            )
            append_event(
                "buyer.verification_drafted",
                "verify_buyer_demand",
                case_id=result["case_id"],
                object_type="buyer",
                object_id=result["buyer"]["buyer_id"],
                payload={"stage": result["stage"], "rfq_id": result["rfq"]["rfq_id"]},
                citations=[str(note_path.relative_to(PROJECT_ROOT))],
            )
        write_csv(DATA_DIR / "buyer_master.csv", BUYER_FIELDS, buyers)
        write_csv(DATA_DIR / "rfq_master.csv", RFQ_FIELDS, rfqs)
        append_run_log(len(results), len(results), args.dry_run)

    summary = [
        {
            "case_id": result["case_id"],
            "stage": result["stage"],
            "buyer_score": result["buyer"]["buyer_score"],
            "rfq_score": result["rfq"]["rfq_score"],
            "missing_evidence": result["rfq"]["missing_evidence"],
        }
        for result in results
    ]
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for item in summary:
            print(f"{item['case_id']}: {item['stage']} buyer={item['buyer_score']} rfq={item['rfq_score']}")
            print(f"  missing: {item['missing_evidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
