#!/usr/bin/env python3
"""Generate an owner-facing verified buyer demand brief."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "buyer_demand"


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def score(row: dict, field: str) -> int:
    try:
        return int(float(row.get(field, "") or 0))
    except ValueError:
        return 0


def split_rows(rfqs: list[dict], demand_rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    verified = [
        row for row in rfqs
        if row.get("rfq_stage") in {"RFQ_VERIFIED", "READY_FOR_SUPPLIER_PROOF"}
        and row.get("evidence_status") == "RFQ_VERIFIED"
    ]
    blocked = [
        row for row in rfqs
        if row.get("rfq_stage") in {"RAW_LEAD", "BUYER_VISIBLE", "BLOCKED"}
        or row.get("evidence_status") in {"MISSING", "MARKETPLACE_MASKED", "PARTIAL"}
    ]
    research = sorted(
        demand_rows,
        key=lambda row: (
            score(row, "market_fit_score") + score(row, "source_reliability_score") + score(row, "evidence_density_score")
        ),
        reverse=True,
    )
    return (
        sorted(verified, key=lambda row: score(row, "rfq_score"), reverse=True),
        research[:12],
        sorted(blocked, key=lambda row: score(row, "rfq_score")),
    )


def row_md(row: dict) -> str:
    return (
        f"| {row.get('case_id', '')} | {row.get('buyer_country', '')} | {row.get('product_or_service', '')} | "
        f"{row.get('deadline_date', '')} | {row.get('rfq_score', '')} | {row.get('source_url', '')} |"
    )


def write_markdown(verified: list[dict], research: list[dict], blocked: list[dict], date_str: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"buyer_demand_brief_{date_str}.md"
    lines = [
        f"# Verified Buyer Demand Brief - {date_str}",
        "",
        "Public-source-only digest. Verified demand requires buyer-specific RFQ proof.",
        "",
        "## Verified RFQ Demand",
    ]
    if verified:
        lines.extend([
            "| Case | Country | Product | Deadline | RFQ score | Source |",
            "|---|---|---|---|---:|---|",
        ])
        lines.extend(row_md(row) for row in verified)
    else:
        lines.append("No RFQ-verified demand is currently available.")

    lines.extend(["", "## Promising Research Lanes"])
    if research:
        lines.extend(["| Category | Country | Tier | Source | Market fit | Next action |", "|---|---|---|---|---:|---|"])
        for row in research:
            lines.append(
                f"| {row.get('category_name', '')} | {row.get('country', '')} | {row.get('source_tier', '')} | "
                f"{row.get('source_name', '')} | {row.get('market_fit_score', '')} | {row.get('recommended_next_action', '')} |"
            )
    else:
        lines.append("No demand research lanes have been generated yet.")

    lines.extend(["", "## Blocked Or Weak Buyer Leads"])
    if blocked:
        lines.extend(["| Case | Stage | Evidence | Missing evidence | Source |", "|---|---|---|---|---|"])
        for row in blocked:
            lines.append(
                f"| {row.get('case_id', '')} | {row.get('rfq_stage', '')} | {row.get('evidence_status', '')} | "
                f"{row.get('missing_evidence', '')} | {row.get('source_url', '')} |"
            )
    else:
        lines.append("No weak buyer leads are currently registered.")

    lines.append("")
    lines.append("No buyer contact, supplier contact, quote send, portal login, submission, payment, DSC use, or approval decision was performed.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_html(verified: list[dict], research: list[dict], blocked: list[dict], md_path: Path, date_str: str) -> Path:
    path = OUTPUT_DIR / f"buyer_demand_brief_{date_str}.html"

    def rfq_cards(rows: list[dict]) -> str:
        if not rows:
            return '<p class="muted">No RFQ-verified demand is currently available.</p>'
        return "\n".join(
            f"""<div class="card">
  <div class="kicker">{esc(row.get('case_id'))} | RFQ score {esc(row.get('rfq_score'))}</div>
  <h3>{esc(row.get('product_or_service'))}</h3>
  <p>{esc(row.get('buyer_country'))} | deadline {esc(row.get('deadline_date') or 'not stated')}</p>
  <a href="{esc(row.get('source_url'))}">source</a>
</div>"""
            for row in rows
        )

    def research_table(rows: list[dict]) -> str:
        if not rows:
            return '<p class="muted">No research lanes generated yet.</p>'
        body = "\n".join(
            f"<tr><td>{esc(row.get('category_name'))}</td><td>{esc(row.get('country'))}</td>"
            f"<td>{esc(row.get('source_tier'))}</td><td>{esc(row.get('source_name'))}</td>"
            f"<td>{esc(row.get('market_fit_score'))}</td><td>{esc(row.get('recommended_next_action'))}</td></tr>"
            for row in rows
        )
        return f"<table><thead><tr><th>Category</th><th>Country</th><th>Tier</th><th>Source</th><th>Fit</th><th>Next action</th></tr></thead><tbody>{body}</tbody></table>"

    def blocked_table(rows: list[dict]) -> str:
        if not rows:
            return '<p class="muted">No weak buyer leads are currently registered.</p>'
        body = "\n".join(
            f"<tr><td>{esc(row.get('case_id'))}</td><td>{esc(row.get('rfq_stage'))}</td>"
            f"<td>{esc(row.get('evidence_status'))}</td><td>{esc(row.get('missing_evidence'))}</td></tr>"
            for row in rows
        )
        return f"<table><thead><tr><th>Case</th><th>Stage</th><th>Evidence</th><th>Missing</th></tr></thead><tbody>{body}</tbody></table>"

    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Buyer Demand Brief {esc(date_str)}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
main {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px; }}
h1 {{ font-size: 30px; margin: 0 0 8px; }}
h2 {{ margin-top: 32px; }}
.muted {{ color: #64748b; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
.card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; }}
.kicker {{ color: #475569; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
table {{ border-collapse: collapse; width: 100%; background: white; border: 1px solid #e2e8f0; }}
th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid #e2e8f0; vertical-align: top; font-size: 13px; }}
th {{ background: #eef2f7; }}
</style></head><body><main>
<h1>Verified Buyer Demand Brief</h1>
<p class="muted">Public-source-only digest. Markdown source: {esc(md_path.name)}</p>
<h2>Verified RFQ Demand</h2><div class="grid">{rfq_cards(verified)}</div>
<h2>Promising Research Lanes</h2>{research_table(research)}
<h2>Blocked Or Weak Buyer Leads</h2>{blocked_table(blocked)}
<p class="muted">No buyer contact, supplier contact, quote send, portal login, submission, payment, DSC use, or approval decision was performed.</p>
</main></body></html>"""
    path.write_text(html_doc, encoding="utf-8")
    return path


def append_run_log(verified_count: int, blocked_count: int) -> None:
    path = DATA_DIR / "agent_run_log.csv"
    file_exists = path.exists()
    row = {
        "run_id": f"RUN-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-BUYER-BRIEF",
        "run_date": dt.date.today().isoformat(),
        "run_time": dt.datetime.now().strftime("%H:%M:%S"),
        "agent_name": "owner_briefing_agent",
        "trigger_type": "manual",
        "cases_processed": verified_count + blocked_count,
        "cases_created": 0,
        "cases_rejected": 0,
        "cases_updated": 0,
        "sources_checked": 0,
        "sources_failed": 0,
        "actions_taken": "generate_buyer_demand_brief",
        "approval_cards_created": 0,
        "receipts_created": 2,
        "errors": 0,
        "warnings": blocked_count,
        "runtime_seconds": 0,
        "status": "SUCCESS",
        "notes": f"Buyer demand brief generated; verified={verified_count}; weak_or_blocked={blocked_count}",
    }
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate verified buyer demand brief")
    parser.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"), help="Brief date YYYYMMDD")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing files")
    args = parser.parse_args()

    verified, research, blocked = split_rows(
        load_csv(DATA_DIR / "rfq_master.csv"),
        load_csv(DATA_DIR / "demand_research.csv"),
    )
    if args.dry_run:
        print(f"verified={len(verified)} research={len(research)} blocked={len(blocked)}")
        return 0
    md_path = write_markdown(verified, research, blocked, args.date)
    html_path = write_html(verified, research, blocked, md_path, args.date)
    append_run_log(len(verified), len(blocked))
    print(f"Buyer demand brief: {html_path}")
    print(f"Buyer demand markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
