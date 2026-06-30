#!/usr/bin/env python3
"""Generate an HTML report from deep source run outputs."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
import uuid
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "deep_source_reports"
SOURCE_RUNS = PROJECT_ROOT / "outputs" / "source_runs"


def latest_source_run() -> Path | None:
    if not SOURCE_RUNS.exists():
        return None
    candidates = sorted(SOURCE_RUNS.glob("*/deep_results.json")) + sorted(SOURCE_RUNS.glob("*/scan_results.json"))
    return candidates[-1] if candidates else None


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def status_bucket(result: dict[str, Any]) -> str:
    workflow = (result.get("extracted", {}).get("workflow_type") or result.get("shallow", {}).get("workflow_type") or "").upper()
    if workflow == "EXPORT":
        return "Export buyer/RFQ opportunities"
    if workflow == "SUPPLIER":
        return "Supplier mapping opportunities"
    return "New tender opportunities"


def opportunity_card(result: dict[str, Any]) -> str:
    shallow = result.get("shallow", {})
    extracted = result.get("extracted", {})
    missing = ", ".join(extracted.get("missing_fields", []) or [])
    risks = ", ".join(extracted.get("risk_flags", []) or [])
    docs = result.get("documents", []) or []
    score = extracted.get("confidence_score", "")
    decision = "Approval gate before external action"
    if result.get("blocker_status"):
        decision = f"Manual action required: {result.get('blocker_status')}"
    elif int(score or 0) < 55:
        decision = "Do not promote until evidence improves"
    return f"""
    <article class="card">
      <h3>{esc(extracted.get('title') or shallow.get('opportunity_title'))}</h3>
      <dl>
        <dt>Candidate</dt><dd>{esc(shallow.get('external_reference'))}</dd>
        <dt>Source</dt><dd>{esc(shallow.get('source_name'))}</dd>
        <dt>Buyer</dt><dd>{esc(extracted.get('buyer_organisation') or shallow.get('buyer_name'))}</dd>
        <dt>Deadline</dt><dd>{esc(extracted.get('bid_end_date') or shallow.get('deadline_date'))}</dd>
        <dt>Tender value</dt><dd>{esc(extracted.get('tender_value_inr') or shallow.get('estimated_value_inr'))}</dd>
        <dt>EMD</dt><dd>{esc(extracted.get('emd_amount_inr'))}</dd>
        <dt>Eligibility</dt><dd>{esc(extracted.get('turnover_requirement') or extracted.get('past_experience_requirement') or 'Missing or not confirmed')}</dd>
        <dt>BOQ</dt><dd>{esc(len(extracted.get('boq_items', []) or []))} item(s) extracted</dd>
        <dt>Documents</dt><dd>{esc(len(docs))} downloaded/parsed document(s)</dd>
        <dt>Confidence</dt><dd>{esc(score)}</dd>
        <dt>Decision</dt><dd>{esc(decision)}</dd>
        <dt>Risk flags</dt><dd>{esc(risks or 'None captured')}</dd>
        <dt>Missing fields</dt><dd>{esc(missing or 'None captured')}</dd>
        <dt>Evidence</dt><dd>{esc(result.get('evidence_dir'))}</dd>
        <dt>Source URL</dt><dd><a href="{esc(shallow.get('source_url'))}">{esc(shallow.get('source_url'))}</a></dd>
        <dt>Next action</dt><dd>{esc('Fast Kill review, then supplier matching if still viable')}</dd>
      </dl>
    </article>
    """


def render_report(data: dict[str, Any]) -> str:
    run_id = data.get("run_id", "")
    results = []
    for item in data.get("results", []):
        results.extend(item.get("deep_results", []))
    scan_results = []
    for item in data.get("results", []):
        scan_results.extend(item.get("opportunities", []))

    buckets: dict[str, list[dict[str, Any]]] = {
        "New tender opportunities": [],
        "Beginner-friendly tender opportunities": [],
        "High-margin tender opportunities": [],
        "Export buyer/RFQ opportunities": [],
        "Supplier mapping opportunities": [],
    }
    for result in results:
        bucket = status_bucket(result)
        buckets.setdefault(bucket, []).append(result)
        risk_flags = set(result.get("extracted", {}).get("risk_flags", []) or [])
        missing = set(result.get("extracted", {}).get("missing_fields", []) or [])
        if not {"PAST_EXPERIENCE_REQUIRED", "DSC_REQUIRED"} & risk_flags and len(missing) <= 4:
            buckets["Beginner-friendly tender opportunities"].append(result)
        if result.get("extracted", {}).get("tender_value_inr") and "PENALTY_CLAUSE" not in risk_flags:
            buckets["High-margin tender opportunities"].append(result)

    blocked = [item for item in results if item.get("blocker_status")] + [item for item in scan_results if item.get("blocker_status")]
    documents = [doc for result in results for doc in result.get("documents", [])]
    missing_fields = [result for result in results if result.get("extracted", {}).get("missing_fields")]
    risks = [result for result in results if result.get("extracted", {}).get("risk_flags")]
    source_names = sorted({item.get("adapter", "") for item in data.get("results", []) if item.get("adapter")})

    sections = [
        ("Executive summary", f"<p>Run {esc(run_id)} scanned {len(source_names)} source(s), produced {len(scan_results)} listing opportunity record(s), and deep-read {len(results)} opportunity record(s).</p>"),
        ("Sources scanned", "<ul>" + "".join(f"<li>{esc(name)}</li>" for name in source_names) + "</ul>"),
        ("Sources blocked", "<ul>" + "".join(f"<li>{esc(item.get('blocker_status') or item.get('shallow', {}).get('blocker_status'))}: {esc(item.get('source_url') or item.get('shallow', {}).get('source_url'))}</li>" for item in blocked) + "</ul>" if blocked else "<p>No blockers recorded in this report.</p>"),
    ]
    for title in [
        "New tender opportunities",
        "Beginner-friendly tender opportunities",
        "High-margin tender opportunities",
        "Export buyer/RFQ opportunities",
        "Supplier mapping opportunities",
    ]:
        cards = "".join(opportunity_card(result) for result in buckets.get(title, []))
        sections.append((title, cards or "<p>No records in this section.</p>"))
    sections.extend(
        [
            ("Documents downloaded", "<ul>" + "".join(f"<li>{esc(doc.get('document_name'))} — {esc(doc.get('local_path'))}</li>" for doc in documents) + "</ul>" if documents else "<p>No documents downloaded.</p>"),
            ("Deep extraction confidence", "<ul>" + "".join(f"<li>{esc(result.get('shallow', {}).get('external_reference'))}: {esc(result.get('extracted', {}).get('confidence_score'))}</li>" for result in results) + "</ul>"),
            ("Missing critical fields", "<ul>" + "".join(f"<li>{esc(result.get('shallow', {}).get('external_reference'))}: {esc(', '.join(result.get('extracted', {}).get('missing_fields', [])))}</li>" for result in missing_fields) + "</ul>" if missing_fields else "<p>No missing critical fields recorded.</p>"),
            ("Risk flags", "<ul>" + "".join(f"<li>{esc(result.get('shallow', {}).get('external_reference'))}: {esc(', '.join(result.get('extracted', {}).get('risk_flags', [])))}</li>" for result in risks) + "</ul>" if risks else "<p>No risk flags recorded.</p>"),
            ("Recommended next actions", "<ol><li>Review blockers and login/CAPTCHA/manual source notes.</li><li>Run Fast Kill on viable candidates.</li><li>Trigger supplier matching only for shortlisted tenders.</li><li>Create approval cards before any external action.</li></ol>"),
            ("Evidence links", "<ul>" + "".join(f"<li>{esc(result.get('evidence_dir'))}</li>" for result in results if result.get("evidence_dir")) + "</ul>"),
            ("Source health", "<p>Source health updates are written as source_health.updated events and reflected in data/source_health.csv helper updates.</p>"),
            ("Approval gates reached", "<p>No bid submission, upload, payment, DSC, buyer quote, legal declaration, final price, HSN/ITC-HS, origin, or delivery commitment is executed by this report.</p>"),
        ]
    )

    body = "\n".join(f"<section><h2>{esc(title)}</h2>{content}</section>" for title, content in sections)
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Deep Source Report {esc(run_id)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #17202a; margin: 32px; line-height: 1.45; }}
    h1 {{ margin-bottom: 4px; }}
    section {{ border-top: 1px solid #d9dee5; padding: 18px 0; }}
    .card {{ border: 1px solid #cfd6df; border-radius: 6px; padding: 14px; margin: 12px 0; }}
    dl {{ display: grid; grid-template-columns: 180px 1fr; gap: 6px 12px; }}
    dt {{ font-weight: 700; }}
    dd {{ margin: 0; }}
  </style>
</head>
<body>
  <h1>Deep Source Report</h1>
  <p>Generated {esc(dt.datetime.now().isoformat(timespec='seconds'))}</p>
  {body}
</body>
</html>
"""


def generate_report(input_path: Path | None = None) -> Path:
    source = input_path or latest_source_run()
    if source is None:
        raise FileNotFoundError("No source run output found under outputs/source_runs")
    if not source.is_absolute():
        source = PROJECT_ROOT / source
    data = json.loads(source.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.html"
    path.write_text(render_report(data), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deep source HTML report")
    parser.add_argument("--input", default="", help="Path to scan_results.json or deep_results.json")
    args = parser.parse_args()
    path = generate_report(Path(args.input) if args.input else None)
    print(f"Wrote deep source report: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
