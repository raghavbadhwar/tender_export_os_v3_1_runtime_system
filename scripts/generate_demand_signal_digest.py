#!/usr/bin/env python3
"""Generate a founder-facing demand signal digest from master_cases.csv.

This is read/report only. It does not contact buyers/suppliers, submit bids,
commit prices, classify products finally, or use DSC.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MASTER = PROJECT_ROOT / "data" / "master_cases.csv"
OUT_DIR = PROJECT_ROOT / "outputs" / "demand_signals"


def today_local() -> dt.date:
    return dt.datetime.now().astimezone().date()


def parse_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def int_or_none(value: str) -> int | None:
    try:
        if str(value).strip() == "":
            return None
        return int(float(str(value).replace(",", "")))
    except Exception:
        return None


def load_cases() -> list[dict[str, str]]:
    with MASTER.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def signal_score(row: dict[str, str], today: dt.date) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    status = (row.get("status") or "").upper()
    workflow = row.get("workflow_type", "")
    deadline = parse_date(row.get("deadline_date", ""))
    days = int_or_none(row.get("days_to_deadline", ""))
    if status == "NEW":
        score += 30
        reasons.append("new")
    if workflow == "EXPORT":
        score += 15
    elif workflow == "GOV":
        score += 10
    if deadline:
        d = (deadline - today).days
        if 3 <= d <= 21:
            score += 25
            reasons.append(f"deadline {d}d")
        elif d < 3:
            score -= 20
            reasons.append(f"deadline too close {d}d")
        elif d <= 45:
            score += 10
            reasons.append(f"deadline {d}d")
    elif days is not None:
        if 3 <= days <= 21:
            score += 20
            reasons.append(f"deadline {days}d")
        elif days < 3:
            score -= 20
            reasons.append(f"deadline too close {days}d")
    if row.get("source_url", "").strip():
        score += 10
        reasons.append("source link")
    notes = row.get("notes", "").lower()
    if "evidence-backed" in notes or "public gem" in notes or "bid_document_http_status=200" in notes:
        score += 15
        reasons.append("evidence-backed")
    if "login" in notes or "contact hidden" in notes or "registration" in notes:
        score -= 5
        reasons.append("login/registration gate")
    if "not deep-read" in notes:
        score -= 5
        reasons.append("needs deep-read")
    if "deadline is today" in notes:
        score -= 30
        reasons.append("likely fast-kill")
    return score, reasons


def as_signal(row: dict[str, str], today: dt.date) -> dict[str, Any]:
    score, reasons = signal_score(row, today)
    return {
        "case_id": row.get("case_id", ""),
        "workflow_type": row.get("workflow_type", ""),
        "status": row.get("status", ""),
        "source_name": row.get("source_name", ""),
        "source_url": row.get("source_url", ""),
        "opportunity_title": row.get("opportunity_title", ""),
        "buyer_name": row.get("buyer_name", ""),
        "country_or_location": row.get("buyer_country") or row.get("location") or row.get("state", ""),
        "product_or_service": row.get("product_or_service", ""),
        "deadline_date": row.get("deadline_date", ""),
        "days_to_deadline": row.get("days_to_deadline", ""),
        "estimated_value_inr": row.get("estimated_value_inr", ""),
        "score": score,
        "signal_reasons": reasons,
        "notes": row.get("notes", ""),
    }


def md_escape(text: str, max_len: int = 180) -> str:
    text = (text or "").replace("\n", " ").replace("|", "-").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def write_md(signals: list[dict[str, Any]], out: Path, generated_at: str) -> None:
    top = signals[:10]
    export_count = sum(s["workflow_type"] == "EXPORT" for s in signals)
    gov_count = sum(s["workflow_type"] == "GOV" for s in signals)
    lines = [
        f"# Demand Signal Digest — {generated_at}",
        "",
        "Safety: owner-facing intelligence only. No buyer/supplier contact, bid/RFQ submission, payment, DSC, final HSN/ITC-HS, origin, or price commitment executed.",
        "",
        f"## Summary: {len(signals)} active demand signals",
        f"- EXPORT RFQs/leads: {export_count}",
        f"- GOV tenders: {gov_count}",
        "",
    ]
    if not signals:
        lines += [
            "No active NEW / WATCHLIST / SUPPLIER_SEARCH / APPROVAL_REQUIRED demand signals found in `data/master_cases.csv`.",
            "Recommended action: improve source adapters and/or provide login credentials for gated sources if you want deeper coverage.",
        ]
    else:
        lines += [
            "## Top demand signals",
            "| Rank | Case | Type | Score | Buyer/location | Product | Deadline | Source |",
            "|---:|---|---|---:|---|---|---|---|",
        ]
        for i, s in enumerate(top, start=1):
            lines.append(
                f"| {i} | `{s['case_id']}` | {s['workflow_type']} | {s['score']} | "
                f"{md_escape(s['buyer_name'] or s['country_or_location'], 80)} | {md_escape(s['product_or_service'], 80)} | "
                f"{s['deadline_date'] or 'not stated'} | {md_escape(s['source_name'], 60)} |"
            )
        lines += ["", "## Details"]
        for s in top:
            lines += [
                f"### {s['case_id']} — {s['opportunity_title']}",
                f"- Type/status: {s['workflow_type']} / {s['status']}",
                f"- Buyer/location: {s['buyer_name'] or s['country_or_location'] or 'not clear'}",
                f"- Product/service: {s['product_or_service'] or 'not clear'}",
                f"- Deadline: {s['deadline_date'] or 'not stated'}",
                f"- Source: {s['source_name']} — {s['source_url']}",
                f"- Why surfaced: {', '.join(s['signal_reasons']) or 'active case'}",
                f"- Next safe action: deep-read/fast-kill and create approval card before any external action.",
                "",
            ]
        lines += [
            "## Recommended action",
            "Review the top 3 signals, fast-kill bad fits, and approve only the next internal deep-read/supplier-discovery step. Do not send externally until an approval card is approved.",
        ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since-date", default="", help="Only include cases created/updated on or after YYYY-MM-DD")
    ap.add_argument("--status", default="NEW,WATCHLIST,SUPPLIER_SEARCH,APPROVAL_REQUIRED", help="Comma statuses to include")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--json", action="store_true", help="Print JSON summary instead of text")
    args = ap.parse_args()

    today = today_local()
    statuses = {s.strip().upper() for s in args.status.split(",") if s.strip()}
    since = parse_date(args.since_date) if args.since_date else None
    cases = load_cases()
    active: list[dict[str, Any]] = []
    for row in cases:
        if (row.get("status") or "").upper() not in statuses:
            continue
        if since:
            created = parse_date(row.get("created_at", "")) or parse_date(row.get("updated_at", ""))
            if created and created < since:
                continue
        active.append(as_signal(row, today))
    active.sort(key=lambda s: (s["score"], s.get("deadline_date") or "9999-99-99"), reverse=True)
    if args.top:
        active = active[: args.top]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    generated_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    json_path = OUT_DIR / f"demand_signal_digest_{stamp}.json"
    md_path = OUT_DIR / f"demand_signal_digest_{stamp}.md"
    payload = {
        "generated_at": generated_at,
        "source": "data/master_cases.csv",
        "signals_count": len(active),
        "signals": active,
        "safety": "owner_intelligence_only_no_external_business_action",
        "markdown_report": str(md_path.relative_to(PROJECT_ROOT)),
        "json_report": str(json_path.relative_to(PROJECT_ROOT)),
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_md(active, md_path, generated_at)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Demand signals: {len(active)}")
        print(f"Markdown: {md_path.relative_to(PROJECT_ROOT)}")
        print(f"JSON: {json_path.relative_to(PROJECT_ROOT)}")
        for s in active[:5]:
            print(f"- {s['case_id']} [{s['workflow_type']}] score={s['score']} {s['opportunity_title'][:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
