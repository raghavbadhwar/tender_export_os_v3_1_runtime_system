#!/usr/bin/env python3
"""Generate the approval-safe Tender Export OS intra-day monitor.

The monitor is deliberately read-only with respect to business state. It
reviews approval expiry, strict supplier quote proof, and approved actions,
then writes an internal report, one audit event, and one agent run-log row.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import tempfile
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows development fallback
    fcntl = None  # type: ignore[assignment]

try:
    from approval_lifecycle import classify_approval
    from event_ledger import append_event
    from execution_receipt_status import dispositions_by_approval, is_pending_execution
    from quote_proof import strict_quote_proofs
except ModuleNotFoundError:  # pragma: no cover - package import path used by pytest
    from scripts.approval_lifecycle import classify_approval
    from scripts.event_ledger import append_event
    from scripts.execution_receipt_status import dispositions_by_approval, is_pending_execution
    from scripts.quote_proof import strict_quote_proofs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_ID = "intra_day_monitor"
PROOF_REQUIRED_STATUSES = {
    "SUPPLIER_SEARCH",
    "PRICING_READY",
    "ARTIFACT_PRODUCTION",
    "APPROVAL_REQUIRED",
}
RUN_LOG_HEADERS = [
    "run_id", "run_date", "run_time", "agent_name", "trigger_type", "cases_processed",
    "cases_created", "cases_rejected", "cases_updated", "sources_checked", "sources_failed",
    "actions_taken", "approval_cards_created", "receipts_created", "errors", "warnings",
    "runtime_seconds", "status", "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def utc_timestamp(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc).replace(microsecond=0)


def build_report(
    *,
    project_root: Path = PROJECT_ROOT,
    now: dt.datetime | None = None,
    required_quote_proofs: int = 2,
) -> dict[str, Any]:
    generated_at = utc_timestamp(now or dt.datetime.now(dt.timezone.utc))
    data_dir = project_root / "data"
    cases = read_csv(data_dir / "master_cases.csv")
    approvals = read_csv(data_dir / "approvals_receipts.csv")
    quotes = read_csv(data_dir / "quote_master.csv")
    execution_dispositions = dispositions_by_approval(approvals, events_path=data_dir / "events.jsonl")

    pending_approvals: list[dict[str, Any]] = []
    for approval in approvals:
        if (approval.get("approval_status") or "").upper() != "PENDING":
            continue
        normalized = dict(approval)
        normalized["approval_status"] = "PENDING"
        lifecycle = classify_approval(normalized, now=generated_at)
        pending_approvals.append(
            {
                "approval_id": approval.get("approval_id", ""),
                "case_id": approval.get("case_id", ""),
                "state": lifecycle["state"],
                "timeout_at": lifecycle.get("timeout_at", ""),
                "requires_reissue": lifecycle.get("requires_reissue", False),
                "next_action": (
                    "Reissue a timestamped approval card; do not infer approval from silence."
                    if lifecycle.get("requires_reissue")
                    else "Owner must approve, reject, or ask changes before any external action."
                ),
            }
        )

    quote_proof_gaps: list[dict[str, Any]] = []
    for case in cases:
        status = (case.get("status") or "").upper()
        case_id = (case.get("case_id") or "").strip()
        if status not in PROOF_REQUIRED_STATUSES or not case_id:
            continue
        strict_count = len(strict_quote_proofs(case_id, quotes))
        gap = max(0, required_quote_proofs - strict_count)
        if gap:
            quote_proof_gaps.append(
                {
                    "case_id": case_id,
                    "workflow_type": case.get("workflow_type", ""),
                    "title": case.get("opportunity_title", ""),
                    "status": status,
                    "strict_quote_proof_count": strict_count,
                    "required_quote_proof_count": required_quote_proofs,
                    "proof_gap": gap,
                    "next_action": "Collect supplier-specific written proof under the 5-3-2 gate; marketplace listings do not count.",
                }
            )

    approved_actions: list[dict[str, Any]] = []
    for approval in approvals:
        if (approval.get("approval_status") or "").upper() != "APPROVED":
            continue
        if (
            (approval.get("external_effect") or "").upper() != "PENDING_APPROVED_EXECUTION"
            and (approval.get("receipt_path") or "").strip()
        ):
            continue
        disposition = execution_dispositions.get(approval.get("approval_id", ""), {})
        approved_actions.append(
            {
                "approval_id": approval.get("approval_id", ""),
                "case_id": approval.get("case_id", ""),
                "action": approval.get("action_approved") or approval.get("proposed_action") or "approved_action",
                "approval_external_effect": approval.get("external_effect", ""),
                "external_effect": disposition.get("external_effect", approval.get("external_effect", "")),
                "receipt_path": approval.get("receipt_path", ""),
                "execution_receipt_paths": disposition.get("execution_receipt_paths", []),
                "execution_receipt_count": disposition.get("execution_receipt_count", 0),
                "next_action": disposition.get(
                    "next_action",
                    "Track only the approved scope; no resend, resubmit, or escalation without a new owner command.",
                ),
            }
        )

    blockers: list[dict[str, str]] = []
    blockers.extend(
        {
            "type": "approval",
            "reference": item["approval_id"],
            "detail": item["next_action"],
        }
        for item in pending_approvals
    )
    blockers.extend(
        {
            "type": "quote_proof",
            "reference": item["case_id"],
            "detail": f"Missing {item['proof_gap']} of {required_quote_proofs} strict supplier quote proofs.",
        }
        for item in quote_proof_gaps
    )
    blockers.extend(
        {
            "type": "approved_execution",
            "reference": item["approval_id"],
            "detail": "Approved action is awaiting a verified execution receipt.",
        }
        for item in approved_actions
        if is_pending_execution(item)
    )

    run_id = f"MON-{generated_at.strftime('%Y%m%dT%H%M%SZ')}"
    return {
        "run_id": run_id,
        "schedule_id": SCHEDULE_ID,
        "generated_at": generated_at.isoformat(),
        "project_root": str(project_root.resolve()),
        "sources": [
            "data/master_cases.csv",
            "data/approvals_receipts.csv",
            "data/quote_master.csv",
        ],
        "pending_approvals": pending_approvals,
        "quote_proof_gaps": quote_proof_gaps,
        "approved_actions_tracked": approved_actions,
        "owner_decision_blockers": blockers,
        "summary": {
            "pending_approvals_checked": len(pending_approvals),
            "quote_proof_gap_cases": len(quote_proof_gaps),
            "approved_actions_tracked": len(approved_actions),
            "receipts_created": 0,
            "owner_decision_blockers": len(blockers),
        },
        "status": "SUCCESS",
        "external_business_actions": False,
        "safety_note": (
            "Internal monitoring only. No reminder, quote request, buyer reply, submission, payment, DSC, "
            "price, classification, origin, or delivery commitment was executed."
        ),
    }


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"# Tender Export OS Intra-day Monitor — {report['generated_at']}",
        "",
        report["safety_note"],
        "",
        "## Summary",
        "",
        f"- Pending approvals checked: {summary['pending_approvals_checked']}",
        f"- Quote-proof gap cases: {summary['quote_proof_gap_cases']}",
        f"- Approved actions tracked: {summary['approved_actions_tracked']}",
        f"- Receipts created: {summary['receipts_created']}",
        f"- Owner-decision blockers: {summary['owner_decision_blockers']}",
        "",
        "## Pending approvals",
        "",
    ]
    lines.extend(
        f"- {item['approval_id']} / {item['case_id']}: {item['state']} — {item['next_action']}"
        for item in report["pending_approvals"]
    )
    if not report["pending_approvals"]:
        lines.append("- None.")
    lines.extend(["", "## Strict quote-proof gaps", ""])
    lines.extend(
        f"- {item['case_id']}: {item['strict_quote_proof_count']}/{item['required_quote_proof_count']} proven; gap {item['proof_gap']}."
        for item in report["quote_proof_gaps"]
    )
    if not report["quote_proof_gaps"]:
        lines.append("- None.")
    lines.extend(["", "## Approved actions tracked", ""])
    lines.extend(
        f"- {item['approval_id']} / {item['case_id']}: {item['action']} [{item['external_effect']}] — {item['next_action']}"
        for item in report["approved_actions_tracked"]
    )
    if not report["approved_actions_tracked"]:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    timestamp = utc_timestamp(dt.datetime.fromisoformat(report["generated_at"]))
    stem = f"intraday_monitor_{timestamp.strftime('%Y%m%dT%H%M%SZ')}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    atomic_write(json_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def append_run_log(path: Path, report: dict[str, Any], report_path: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = dt.datetime.fromisoformat(report["generated_at"])
    with path.open("a+", newline="", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.seek(0, os.SEEK_END)
            writer = csv.DictWriter(handle, fieldnames=RUN_LOG_HEADERS)
            if handle.tell() == 0:
                writer.writeheader()
            writer.writerow(
                {
                    "run_id": report["run_id"],
                    "run_date": generated_at.date().isoformat(),
                    "run_time": generated_at.time().isoformat(),
                    "agent_name": "intraday_monitor",
                    "trigger_type": "scheduled_internal_monitor",
                    "cases_processed": len(report["quote_proof_gaps"]),
                    "cases_created": 0,
                    "cases_rejected": 0,
                    "cases_updated": 0,
                    "sources_checked": 0,
                    "sources_failed": 0,
                    "actions_taken": "approval_quote_execution_monitor",
                    "approval_cards_created": 0,
                    "receipts_created": 0,
                    "errors": 0,
                    "warnings": len(report["owner_decision_blockers"]),
                    "runtime_seconds": 0,
                    "status": report["status"],
                    "notes": f"report={report_path}; external_business_actions=false",
                }
            )
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def record_completion(
    report: dict[str, Any],
    *,
    json_path: Path,
    markdown_path: Path,
    project_root: Path = PROJECT_ROOT,
    events_file: Path | None = None,
    run_log_file: Path | None = None,
) -> None:
    json_relative = relative(json_path, project_root)
    markdown_relative = relative(markdown_path, project_root)
    append_event(
        "intraday_monitor.completed",
        "intraday_monitor",
        object_type="monitor_run",
        object_id=report["run_id"],
        payload={
            "schedule_id": report["schedule_id"],
            "report_path": json_relative,
            "status": report["status"],
            "summary": report["summary"],
        },
        citations=[json_relative, markdown_relative, *report["sources"]],
        correlation_id=report["run_id"],
        idempotency_key=f"intraday-monitor:{report['run_id']}",
        events_file=events_file or project_root / "data" / "events.jsonl",
    )
    append_run_log(
        run_log_file or project_root / "data" / "agent_run_log.csv",
        report,
        json_relative,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-record", action="store_true", help="Write report only; do not append event or run log")
    parser.add_argument("--json", action="store_true", help="Print the full report JSON")
    args = parser.parse_args()

    report = build_report(project_root=PROJECT_ROOT)
    json_path, markdown_path = write_report(report, PROJECT_ROOT / "outputs" / "intraday_monitor")
    if not args.no_record:
        record_completion(report, json_path=json_path, markdown_path=markdown_path)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Intra-day monitor: {json_path}")
        print(f"Owner-decision blockers: {report['summary']['owner_decision_blockers']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
