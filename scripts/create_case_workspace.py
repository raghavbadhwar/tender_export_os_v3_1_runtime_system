#!/usr/bin/env python3
"""Create per-case workspace folders, context, and evidence bundle stubs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path

from event_ledger import append_event

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CASES_DIR = PROJECT_ROOT / "cases"

SUBDIRS = [
    "evidence/downloaded_docs",
    "evidence/extracted_text",
    "evidence/hashes",
    "supplier",
    "pricing",
    "compliance",
    "artifacts",
    "approvals",
    "followup",
]


def load_cases() -> list[dict[str, str]]:
    with (DATA_DIR / "master_cases.csv").open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def find_case(case_id: str) -> dict[str, str]:
    for row in load_cases():
        if row.get("case_id") == case_id:
            return row
    raise SystemExit(f"Unknown case_id: {case_id}")


def safe_text(value: str | None, fallback: str = "") -> str:
    return (value or fallback).strip()


def render_case_context(case: dict[str, str]) -> str:
    case_id = case.get("case_id", "")
    workflow = case.get("workflow_type", "UNKNOWN")
    status = case.get("status", "")
    approval = case.get("approval_status", "")
    risks = []
    if workflow == "EXPORT" and case.get("hsn_itchs_candidate"):
        risks.append("HSN/ITC-HS is candidate-only until expert/owner approval.")
    if workflow == "EXPORT" and not case.get("buyer_credibility_score"):
        risks.append("Buyer verification score is missing or incomplete.")
    if case.get("kill_reason"):
        risks.append(f"Kill/risk reason recorded: {case['kill_reason']}")
    if not case.get("source_url"):
        risks.append("Source URL/evidence is missing; do not rely on this case externally.")
    if approval == "PENDING" or status == "APPROVAL_REQUIRED":
        risks.append("Owner approval is pending before any gated action.")
    risk_lines = "\n".join(f"- {item}" for item in risks) or "- No specific risk notes beyond standard approval policy."
    return f"""# Case {case_id}

Workflow: {workflow}
Current status: {status}
Opportunity: {safe_text(case.get('opportunity_title'), 'Untitled opportunity')}
Buyer: {safe_text(case.get('buyer_name'), 'Unknown / not verified')}
Source: {safe_text(case.get('source_name'), 'Unknown')} — {safe_text(case.get('source_url'), 'no source URL recorded')}
Deadline: {safe_text(case.get('deadline_date'), 'unknown')}
Approval status: {safe_text(approval, 'unknown')}

## Known risks
{risk_lines}

## Allowed internal actions
- Read and summarize local case files.
- Capture source evidence and hashes.
- Draft supplier, pricing, compliance, and artifact notes.
- Create approval cards and internal reports.
- Update event ledger, projections, and Kanban comments.

## Standing-authorized execution
- Supplier quote/availability requests, supplier clarifications, supplier follow-ups, and portal login/signup for research are allowed under the owner's 2026-06-30 standing authorization.
- Write receipts for any such external supplier/portal action and never log credential values.

## Forbidden until separate explicit owner approval and receipt
- Send buyer messages, buyer RFQ replies, export quotations, or invoices.
- Submit bids or upload tender documents.
- Use DSC.
- Pay EMD/security/advance or buy paid portal plans/credits.
- Commit final price, delivery, payment terms, HSN/ITC-HS, or origin.
- Place supplier purchase orders or permanently blacklist suppliers.

## Source-of-truth rule
`data/events.jsonl` is canonical. This case folder is a working/evidence view keyed by `{case_id}`.
"""


def render_case_md(case: dict[str, str]) -> str:
    lines = [
        f"# {case.get('case_id', '')} — {case.get('opportunity_title', 'Untitled')}",
        "",
        f"- Workflow: {case.get('workflow_type', '')}",
        f"- Status: {case.get('status', '')}",
        f"- Buyer: {case.get('buyer_name', '')}",
        f"- Product/service: {case.get('product_or_service', '')}",
        f"- Quantity: {case.get('quantity', '')} {case.get('unit', '')}",
        f"- Deadline: {case.get('deadline_date', '')}",
        f"- Source: {case.get('source_name', '')} {case.get('source_url', '')}",
        "",
        "## Next action",
        case.get("notes", "Route through the v4.1 task graph."),
    ]
    return "\n".join(lines) + "\n"


def create_workspace(case: dict[str, str], *, record_event: bool = False) -> Path:
    case_id = case.get("case_id", "")
    root = CASES_DIR / case_id
    root.mkdir(parents=True, exist_ok=True)
    for subdir in SUBDIRS:
        (root / subdir).mkdir(parents=True, exist_ok=True)
    (root / "HERMES.md").write_text(render_case_context(case), encoding="utf-8")
    (root / "case.md").write_text(render_case_md(case), encoding="utf-8")
    metadata = {
        "case_id": case_id,
        "workflow_type": case.get("workflow_type", ""),
        "created_or_refreshed_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_name": case.get("source_name", ""),
        "source_url": case.get("source_url", ""),
        "evidence_items": [],
        "hash_manifest": f"cases/{case_id}/evidence/hashes/sha256sums.txt",
        "notes": "Populate evidence_items when source pages, PDFs, screenshots, or extracted text are captured.",
    }
    (root / "evidence" / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    hash_file = root / "evidence" / "hashes" / "sha256sums.txt"
    if not hash_file.exists():
        hash_file.write_text("", encoding="utf-8")
    if record_event:
        append_event(
            "case.workspace_created",
            "create_case_workspace",
            case_id=case_id,
            object_type="case_workspace",
            object_id=rel(root),
            payload={"workspace": rel(root), "workflow_type": case.get("workflow_type", "")},
            citations=["data/master_cases.csv", rel(root / "HERMES.md")],
        )
        append_event(
            "evidence.bundle_created",
            "create_case_workspace",
            case_id=case_id,
            object_type="evidence",
            object_id=rel(root / "evidence"),
            payload={"evidence_dir": rel(root / "evidence"), "metadata": rel(root / "evidence" / "metadata.json")},
            citations=[rel(root / "evidence" / "metadata.json")],
        )
    return root


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Tender Export OS case workspace folders")
    parser.add_argument("--case-id", action="append", help="Case ID to create/refresh. Repeatable.")
    parser.add_argument("--all-active", action="store_true", help="Create workspaces for all non-archived/non-rejected cases")
    parser.add_argument("--record-event", action="store_true", help="Append workspace/evidence events")
    args = parser.parse_args()
    cases = load_cases()
    selected: list[dict[str, str]] = []
    if args.all_active:
        selected.extend(case for case in cases if case.get("status") not in {"REJECTED", "ARCHIVED", "WON", "LOST"})
    for case_id in args.case_id or []:
        selected.append(find_case(case_id))
    unique = {case.get("case_id"): case for case in selected if case.get("case_id")}
    if not unique:
        print("No cases selected. Use --case-id or --all-active.")
        return 2
    for case in unique.values():
        root = create_workspace(case, record_event=args.record_event)
        print(f"Created/refreshed {rel(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
