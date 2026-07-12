#!/usr/bin/env python3
"""Generate the daily operating-desk report for Tender Export OS.

This report is an internal COO/Hermes queue view. It reads ledgers and
produces JSON/HTML artifacts, but it does not send messages, submit bids,
approve actions, or mutate cases.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
from pathlib import Path
from typing import Any

try:
    from quote_proof import strict_quote_proofs
except ModuleNotFoundError:  # pragma: no cover - package import path used by pytest
    from scripts.quote_proof import strict_quote_proofs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "operating_desk"
RUN_LOG_FILE = DATA_DIR / "agent_run_log.csv"

RUN_LOG_HEADERS = [
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

TERMINAL_CASE_STATUSES = {"REJECTED", "WON", "LOST", "ARCHIVED"}
HEALTHY_STATUSES = {"WORKING", "ACTIVE", "OK", "HEALTHY"}
PROOF_REQUIRED_STATUSES = {"SUPPLIER_SEARCH", "PRICING_READY", "ARTIFACT_PRODUCTION", "APPROVAL_REQUIRED"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_latest_json(directory: Path, pattern: str) -> dict[str, Any]:
    candidates = sorted(directory.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            payload["report_path"] = str(path)
            return payload
    return {}


def hermes_runtime_health(project_root: Path) -> dict[str, Any]:
    report = read_latest_json(project_root / "outputs" / "cron_gateway", "cron_gateway_reliability_*.json")
    cron = report.get("hermes_cron_status", {}) if isinstance(report.get("hermes_cron_status"), dict) else {}
    return {
        "status": report.get("status", "NOT_CHECKED"),
        "profile": cron.get("profile", "tender-export-os"),
        "gateway_running": cron.get("gateway_running"),
        "active_jobs": cron.get("active_jobs", 0),
        "generated_at": report.get("generated_at", ""),
        "finding_count": len(report.get("findings", [])) if isinstance(report.get("findings"), list) else 0,
        "report_path": report.get("report_path", ""),
        "next_action": "Restore supervised gateway/cron before relying on automation." if report.get("status") == "BLOCKED" else "Monitor the next scheduled receipt.",
    }


def prediction_health(project_root: Path) -> dict[str, Any]:
    report = read_latest_json(project_root / "outputs" / "demand_forecasting", "forecast_calibration_*.json")
    return {
        "status": report.get("status", "NOT_EVALUATED"),
        "review_date": report.get("review_date", ""),
        "mature_sample_size": int(report.get("mature_sample_size") or 0),
        "minimum_mature_sample": int(report.get("minimum_mature_sample") or 30),
        "brier_score": report.get("brier_score"),
        "report_path": report.get("report_path", ""),
        "next_action": (
            "Keep collecting time-separated outcomes; do not claim calibrated probability yet."
            if report.get("status") != "CALIBRATION_MEASURED"
            else "Review Brier score and calibration bins before changing the model."
        ),
    }


def buyer_acquisition_health(
    project_root: Path,
    signals: list[dict[str, str]],
    outreach: list[dict[str, str]],
    communications: list[dict[str, str]],
) -> dict[str, Any]:
    latest_monitor = read_latest_json(project_root / "outputs" / "buyer_replies", "buyer_reply_monitor_*.json")
    targets = sorted(
        [
            {
                "signal_id": row.get("signal_id", ""),
                "case_id": row.get("case_id", ""),
                "company_name": row.get("company_name", ""),
                "country": row.get("country", ""),
                "category_name": row.get("category_name", ""),
                "market_fit_score": row.get("market_fit_score", ""),
                "demand_confidence": row.get("demand_confidence", ""),
                "contact_status": row.get("contact_status", ""),
                "next_action": row.get("next_safe_action", ""),
            }
            for row in signals
        ],
        key=lambda row: int(row["market_fit_score"] or 0),
        reverse=True,
    )
    drafts = [
        {
            "outreach_id": row.get("outreach_id", ""),
            "case_id": row.get("case_id", ""),
            "subject": row.get("subject", ""),
            "approval_id": row.get("approval_id", ""),
            "approval_status": row.get("approval_status", ""),
            "send_status": row.get("send_status", ""),
            "reply_status": row.get("reply_status", ""),
            "next_action": (
                "Owner decision required before first contact."
                if row.get("approval_status") == "PENDING"
                else "Track only the approved scope and preserve send/reply receipts."
            ),
        }
        for row in outreach
        if row.get("send_status") in {"DRAFT_ONLY", "READY_AFTER_APPROVAL"}
    ]
    replies = [
        {
            "communication_id": row.get("communication_id", ""),
            "outreach_id": row.get("outreach_id", ""),
            "case_id": row.get("case_id", ""),
            "subject": row.get("subject", ""),
            "classification": row.get("classification", ""),
            "occurred_at": row.get("occurred_at", ""),
            "requires_owner_action": row.get("requires_owner_action", "") == "TRUE",
            "content_path": row.get("content_path", ""),
            "next_action": row.get("recommended_next_action", ""),
        }
        for row in communications
        if row.get("direction") == "INBOUND"
    ]
    replies.sort(key=lambda row: row["occurred_at"], reverse=True)
    owner_action_replies = [row for row in replies if row["requires_owner_action"]]
    return {
        "connector_status": latest_monitor.get("connector_status", "NOT_CHECKED"),
        "target_count": len(targets),
        "outreach_draft_count": len(drafts),
        "reply_count": len(replies),
        "owner_action_reply_count": len(owner_action_replies),
        "targets": targets,
        "outreach_drafts": drafts,
        "replies": replies,
        "owner_action_replies": owner_action_replies,
        "next_action": (
            "Connect the Gmail plugin inbox automation; do not substitute gws/IMAP/Himalaya for Gmail."
            if latest_monitor.get("connector_status") in {"PLUGIN_INSTALLED_AWAITING_AUTOMATION", "NOT_CHECKED", "GMAIL_PLUGIN_NOT_INSTALLED"}
            else "Monitor classified replies and route every response draft through owner approval."
        ),
    }


def parse_date(value: str) -> dt.date | None:
    if not value:
        return None
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text[:8], fmt).date()
        except ValueError:
            continue
    return None


def parse_run_datetime(row: dict[str, str]) -> dt.datetime | None:
    run_date = row.get("run_date", "")
    run_time = row.get("run_time", "") or "00:00:00"
    try:
        return dt.datetime.fromisoformat(f"{run_date}T{run_time[:8]}")
    except ValueError:
        return None


def approval_status(row: dict[str, str]) -> str:
    return (row.get("approval_status") or "").upper()


def case_status(row: dict[str, str]) -> str:
    return (row.get("status") or "").upper()


def health_status(row: dict[str, str]) -> str:
    return (row.get("health_status") or "").upper()


def compact_case(row: dict[str, str]) -> dict[str, str]:
    return {
        "case_id": row.get("case_id", ""),
        "workflow_type": row.get("workflow_type", ""),
        "title": row.get("opportunity_title", ""),
        "buyer": row.get("buyer_name", ""),
        "status": row.get("status", ""),
        "deadline_date": row.get("deadline_date", ""),
        "next_owner": next_owner_for_case(row),
        "next_action": next_action_for_case(row),
    }


def compact_approval(row: dict[str, str]) -> dict[str, str]:
    return {
        "approval_id": row.get("approval_id", ""),
        "case_id": row.get("case_id", ""),
        "workflow_type": row.get("workflow_type", ""),
        "action": row.get("action_approved") or row.get("proposed_action") or "approval_required",
        "status": row.get("approval_status", ""),
        "card_path": row.get("approval_card_path", ""),
        "external_effect": row.get("external_effect", ""),
        "next_owner": "owner",
        "next_action": approval_next_action(row),
    }


def approval_next_action(row: dict[str, str]) -> str:
    status = approval_status(row)
    if status == "PENDING":
        return "Approve, reject, or ask changes. No external action proceeds before this decision."
    notes = (row.get("notes") or "").lower()
    if any(marker in notes for marker in ("safety_held", "raw_lead", "blocked_missing", "blocked by", "blocked_")):
        return "Keep held; resolve proof/contact/scope blockers and create a fresh approval if execution method changes."
    return "Review current gates before execution; execute only the approved scope and save receipts."


def compact_health(row: dict[str, str], owner: str, *, stale: bool = False) -> dict[str, Any]:
    return {
        "name": row.get("source_name") or row.get("plugin_or_tool") or row.get("name") or "",
        "health_status": row.get("health_status", ""),
        "blocker": row.get("blocker", ""),
        "last_checked": row.get("last_checked_date") or row.get("last_checked_at", ""),
        "next_owner": owner,
        "stale": stale,
        "next_action": health_next_action(row, stale=stale),
        "notes": row.get("notes", ""),
    }


def next_owner_for_case(row: dict[str, str]) -> str:
    status = case_status(row)
    if (row.get("source_name") or "").lower() == "foreign retailer catalogue research":
        return "sales_followup_agent"
    if status == "SUPPLIER_SEARCH":
        return "supplier_engine_agent"
    if status == "WATCHLIST":
        return "fast_kill_agent"
    if status == "DEEP_READ":
        return "deep_read_agent"
    if status == "PRICING_READY":
        return "pack_builder_agent"
    if status == "APPROVAL_REQUIRED":
        return "approval_desk_agent"
    if status == "APPROVED":
        return "execution_tracker_agent"
    return "hermes_chief_operator"


def next_action_for_case(row: dict[str, str]) -> str:
    status = case_status(row)
    if (row.get("source_name") or "").lower() == "foreign retailer catalogue research":
        return "Review the catalogue-fit evidence and outreach approval; do not treat this target as an RFQ."
    if status == "SUPPLIER_SEARCH":
        return "Complete 5-3-2 supplier proof and stop before external outreach unless approved."
    if status == "WATCHLIST":
        return "Resolve missing evidence into reject, manual source check, or deep read."
    if status == "DEEP_READ":
        return "Extract all source documents and flag ambiguous clauses."
    if status == "PRICING_READY":
        return "Build internal pack and approval-ready missing-items list."
    if status == "APPROVAL_REQUIRED":
        return "Keep blocked until owner decision is recorded."
    if status == "APPROVED":
        return "Execute only the approved action and save receipts."
    return "Review case state and assign the next specialist."


def health_next_action(row: dict[str, str], *, stale: bool = False) -> str:
    if stale:
        return "Refresh this health probe before relying on its previous healthy status."
    status = health_status(row)
    if status in {"PAYWALLED", "NEEDS LOGIN", "LOGIN REQUIRED"}:
        return "Skip automated scan; route to manual/approved access path."
    if status in {"BROKEN", "FAILED"}:
        return "Repair source/plugin or replace it before relying on output."
    if row.get("blocker"):
        return "Clear blocker or downgrade route before production use."
    if not status:
        return "Fill health_status so routing does not depend on guesswork."
    return "Monitor on next scheduled health review."


def get_deadline_risks(cases: list[dict[str, str]], today: dt.date, window_days: int) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for case in cases:
        if case_status(case) in TERMINAL_CASE_STATUSES:
            continue
        deadline = parse_date(case.get("deadline_date", ""))
        if not deadline:
            continue
        days_left = (deadline - today).days
        if days_left <= window_days:
            item = compact_case(case)
            item["days_left"] = days_left
            item["next_owner"] = "hermes_chief_operator"
            item["next_action"] = "Escalate deadline risk, then route to the owning specialist."
            risks.append(item)
    return sorted(risks, key=lambda row: int(row["days_left"]))


def health_row_is_stale(row: dict[str, str], today: dt.date, stale_days: int) -> bool:
    checked = parse_date(row.get("last_checked_date") or row.get("last_checked_at", ""))
    return checked is None or checked < today - dt.timedelta(days=stale_days)


def get_source_blockers(
    rows: list[dict[str, str]],
    today: dt.date,
    stale_days: int,
) -> list[dict[str, Any]]:
    blockers = []
    for row in rows:
        status = health_status(row)
        failures = row.get("consecutive_failures", "")
        has_failures = failures.isdigit() and int(failures) > 0
        stale = health_row_is_stale(row, today, stale_days)
        if status not in HEALTHY_STATUSES or row.get("blocker") or has_failures or stale:
            blockers.append(compact_health(row, "source_health_agent", stale=stale))
    return blockers


def get_plugin_blockers(
    rows: list[dict[str, str]],
    today: dt.date,
    stale_days: int,
) -> list[dict[str, Any]]:
    return [
        compact_health(
            row,
            "codex_plugin_factory_agent",
            stale=health_row_is_stale(row, today, stale_days),
        )
        for row in rows
        if health_status(row) not in HEALTHY_STATUSES
        or row.get("blocker")
        or health_row_is_stale(row, today, stale_days)
    ]


def get_quote_proof_gaps(
    cases: list[dict[str, str]],
    quotes: list[dict[str, str]],
    required_proofs: int = 2,
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for case in cases:
        case_id = (case.get("case_id") or "").strip()
        if not case_id or case_status(case) not in PROOF_REQUIRED_STATUSES:
            continue
        proof_count = len(strict_quote_proofs(case_id, quotes))
        gap = max(0, required_proofs - proof_count)
        if not gap:
            continue
        item = compact_case(case)
        item.update(
            {
                "strict_quote_proof_count": proof_count,
                "required_quote_proof_count": required_proofs,
                "proof_gap": gap,
                "next_owner": "supplier_engine_agent",
                "next_action": "Obtain supplier-specific written quote proof; marketplace/public listings do not satisfy the gate.",
            }
        )
        gaps.append(item)
    return gaps


def get_stale_or_failed_runs(
    runs: list[dict[str, str]],
    today: dt.date,
    stale_days: int,
) -> list[dict[str, str]]:
    failed = [
        row for row in runs
        if (row.get("status") or "").upper() not in {"", "SUCCESS"}
    ]
    latest_by_agent: dict[str, dict[str, str]] = {}
    for row in runs:
        agent = row.get("agent_name", "")
        if not agent:
            continue
        current = latest_by_agent.get(agent)
        if current is None:
            latest_by_agent[agent] = row
            continue
        if (parse_run_datetime(row) or dt.datetime.min) > (parse_run_datetime(current) or dt.datetime.min):
            latest_by_agent[agent] = row

    stale = []
    threshold = today - dt.timedelta(days=stale_days)
    for row in latest_by_agent.values():
        run_day = parse_date(row.get("run_date", ""))
        if run_day and run_day < threshold:
            stale.append(row)

    seen = set()
    result = []
    for row in failed + stale:
        key = row.get("run_id") or f"{row.get('agent_name')}:{row.get('run_date')}:{row.get('run_time')}"
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "run_id": row.get("run_id", ""),
            "agent_name": row.get("agent_name", ""),
            "run_date": row.get("run_date", ""),
            "run_time": row.get("run_time", ""),
            "status": row.get("status", ""),
            "next_owner": "hermes_chief_operator",
            "next_action": "Review failure/staleness and reroute if this agent owns an active queue.",
            "notes": row.get("notes", ""),
        })
    return result[:30]


def choose_owner_action(report: dict[str, Any]) -> str:
    if report.get("hermes_runtime_health", {}).get("status") == "BLOCKED":
        return "Restore the supervised Hermes gateway and cron before relying on scheduled operations."
    owner_replies = report.get("buyer_acquisition", {}).get("owner_action_replies", [])
    if owner_replies:
        first = owner_replies[0]
        return f"Review buyer reply {first['communication_id']} for {first['case_id']}: {first['next_action']}"
    if report["pending_approvals"]:
        first = report["pending_approvals"][0]
        return f"Review approval {first['approval_id']} for {first['case_id']} and decide approve/reject/ask changes."
    if report["approved_actions_awaiting_execution"]:
        first = report["approved_actions_awaiting_execution"][0]
        return f"Review approved action {first['approval_id']} for {first['case_id']}: {first['next_action']}"
    if report["quote_proof_gaps"]:
        first = report["quote_proof_gaps"][0]
        return f"Close the strict supplier quote-proof gap for {first['case_id']} ({first['strict_quote_proof_count']}/{first['required_quote_proof_count']})."
    if report["deadline_risks"]:
        first = report["deadline_risks"][0]
        return f"Resolve deadline risk for {first['case_id']} before lower-priority work."
    if report["supplier_search_cases"]:
        first = report["supplier_search_cases"][0]
        return f"Finish supplier proof gate for {first['case_id']}."
    if report["watchlist_triage"]:
        first = report["watchlist_triage"][0]
        return f"Triage watchlist case {first['case_id']} into reject, manual check, or deep read."
    if report["source_blockers"] or report["plugin_blockers"]:
        return "Clear the highest-impact source/plugin blocker before production work."
    return "No urgent queue found; run the next scheduled radar and learning review."


def build_employee_queues(report: dict[str, Any]) -> list[dict[str, Any]]:
    queue_specs = [
        ("approval_desk_agent", "approval decisions", report["pending_approvals"]),
        ("execution_tracker_agent", "approved execution", report["approved_actions_awaiting_execution"]),
        ("supplier_engine_agent", "supplier proof", report["quote_proof_gaps"]),
        ("fast_kill_agent", "watchlist triage", report["watchlist_triage"]),
        ("hermes_chief_operator", "deadline and run health", report["deadline_risks"] + report["stale_or_failed_agent_runs"]),
        ("source_health_agent", "source blockers", report["source_blockers"]),
        ("codex_plugin_factory_agent", "plugin blockers", report["plugin_blockers"]),
        (
            "sales_followup_agent",
            "buyer targets, outreach, and replies",
            report.get("buyer_acquisition", {}).get("owner_action_replies", [])
            + report.get("buyer_acquisition", {}).get("outreach_drafts", []),
        ),
    ]
    return [
        {
            "agent": agent,
            "desk": desk,
            "open_items": len(items),
            "next_action": items[0]["next_action"] if items else "No open queue.",
        }
        for agent, desk, items in queue_specs
    ]


def build_report(
    *,
    project_root: Path = PROJECT_ROOT,
    today: dt.date | None = None,
    deadline_window_days: int = 14,
    stale_days: int = 1,
) -> dict[str, Any]:
    today = today or dt.date.today()
    data_dir = project_root / "data"
    cases = read_csv(data_dir / "master_cases.csv")
    approvals = read_csv(data_dir / "approvals_receipts.csv")
    source_health = read_csv(data_dir / "source_health.csv")
    plugin_health = read_csv(data_dir / "plugin_health.csv")
    quotes = read_csv(data_dir / "quote_master.csv")
    runs = read_csv(data_dir / "agent_run_log.csv")
    buyer_signals = read_csv(data_dir / "buyer_demand_signals.csv")
    outreach = read_csv(data_dir / "outreach_queue.csv")
    communications = read_csv(data_dir / "communication_log.csv")

    pending_approvals = [compact_approval(row) for row in approvals if approval_status(row) == "PENDING"]
    approved_waiting = [
        compact_approval(row) for row in approvals
        if approval_status(row) == "APPROVED"
        and (row.get("external_effect") == "PENDING_APPROVED_EXECUTION" or not row.get("receipt_path"))
    ]

    report: dict[str, Any] = {
        "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "report_date": today.strftime("%Y%m%d"),
        "project_root": str(project_root),
        "sources": [
            "data/master_cases.csv",
            "data/approvals_receipts.csv",
            "data/source_health.csv",
            "data/plugin_health.csv",
            "data/quote_master.csv",
            "data/agent_run_log.csv",
            "data/buyer_demand_signals.csv",
            "data/outreach_queue.csv",
            "data/communication_log.csv",
            "outputs/cron_gateway/cron_gateway_reliability_*.json",
            "outputs/demand_forecasting/forecast_calibration_*.json",
        ],
        "hermes_runtime_health": hermes_runtime_health(project_root),
        "prediction_health": prediction_health(project_root),
        "buyer_acquisition": buyer_acquisition_health(project_root, buyer_signals, outreach, communications),
        "pending_approvals": pending_approvals,
        "approved_actions_awaiting_execution": approved_waiting,
        "supplier_search_cases": [compact_case(row) for row in cases if case_status(row) == "SUPPLIER_SEARCH"],
        "quote_proof_gaps": get_quote_proof_gaps(cases, quotes),
        "watchlist_triage": [
            compact_case(row)
            for row in cases
            if case_status(row) == "WATCHLIST"
            and (row.get("source_name") or "").lower() != "foreign retailer catalogue research"
        ],
        "deadline_risks": get_deadline_risks(cases, today, deadline_window_days),
        "stale_or_failed_agent_runs": get_stale_or_failed_runs(runs, today, stale_days),
        "source_blockers": get_source_blockers(source_health, today, stale_days),
        "plugin_blockers": get_plugin_blockers(plugin_health, today, stale_days),
        "safety_note": (
            "Internal report only. No external send, submission, payment, DSC, final price, "
            "classification, origin, or delivery commitment was executed."
        ),
    }
    report["employee_queues"] = build_employee_queues(report)
    report["one_smallest_owner_action"] = choose_owner_action(report)
    report["summary"] = {
        "pending_approvals": len(report["pending_approvals"]),
        "approved_actions_awaiting_execution": len(report["approved_actions_awaiting_execution"]),
        "supplier_search_cases": len(report["supplier_search_cases"]),
        "quote_proof_gaps": len(report["quote_proof_gaps"]),
        "watchlist_triage": len(report["watchlist_triage"]),
        "deadline_risks": len(report["deadline_risks"]),
        "source_blockers": len(report["source_blockers"]),
        "plugin_blockers": len(report["plugin_blockers"]),
        "active_cron_jobs": report["hermes_runtime_health"]["active_jobs"],
        "mature_forecast_outcomes": report["prediction_health"]["mature_sample_size"],
        "buyer_targets": report["buyer_acquisition"]["target_count"],
        "outreach_drafts": report["buyer_acquisition"]["outreach_draft_count"],
        "buyer_replies": report["buyer_acquisition"]["reply_count"],
        "buyer_replies_needing_owner": report["buyer_acquisition"]["owner_action_reply_count"],
    }
    return report


def render_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "<p>No open items.</p>"
    head = "".join(f"<th>{html.escape(column)}</th>" for column in columns)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{html.escape(str(row.get(column, '')))}</td>" for column in columns) + "</tr>"
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def render_html(report: dict[str, Any]) -> str:
    css = """
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:24px;color:#172033;background:#f8fafc}
h1,h2{margin-bottom:8px}.metrics{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.metric{border:1px solid #d8dee9;background:white;padding:10px 12px;border-radius:6px;min-width:150px}
.metric strong{display:block;font-size:22px}table{border-collapse:collapse;width:100%;background:white;margin:10px 0 22px}
td,th{border:1px solid #d8dee9;padding:7px;text-align:left;vertical-align:top}th{background:#eef2f7}
.action{background:#fff7ed;border:1px solid #fed7aa;padding:12px;border-radius:6px}
.note{color:#52606d}
"""
    metrics = "".join(
        f"<div class='metric'><span>{html.escape(key.replace('_', ' ').title())}</span><strong>{value}</strong></div>"
        for key, value in report["summary"].items()
    )
    sections = [
        ("Hermes Runtime Health", [report["hermes_runtime_health"]], ["status", "profile", "gateway_running", "active_jobs", "generated_at", "next_action"]),
        ("Prediction Calibration Health", [report["prediction_health"]], ["status", "review_date", "mature_sample_size", "minimum_mature_sample", "brier_score", "next_action"]),
        ("Employee Queues", report["employee_queues"], ["agent", "desk", "open_items", "next_action"]),
        ("Buyer Acquisition Health", [report["buyer_acquisition"]], ["connector_status", "target_count", "outreach_draft_count", "reply_count", "owner_action_reply_count", "next_action"]),
        ("Foreign Buyer Targets", report["buyer_acquisition"]["targets"], ["signal_id", "case_id", "company_name", "country", "category_name", "market_fit_score", "demand_confidence", "contact_status", "next_action"]),
        ("Buyer Outreach Drafts", report["buyer_acquisition"]["outreach_drafts"], ["outreach_id", "case_id", "subject", "approval_id", "approval_status", "send_status", "reply_status", "next_action"]),
        ("Buyer Replies", report["buyer_acquisition"]["replies"], ["communication_id", "case_id", "subject", "classification", "occurred_at", "requires_owner_action", "next_action", "content_path"]),
        ("Pending Approvals", report["pending_approvals"], ["approval_id", "case_id", "workflow_type", "action", "card_path", "next_action"]),
        ("Approved Actions Awaiting Execution", report["approved_actions_awaiting_execution"], ["approval_id", "case_id", "action", "external_effect", "next_action"]),
        ("Supplier Search Cases", report["supplier_search_cases"], ["case_id", "workflow_type", "title", "buyer", "deadline_date", "next_action"]),
        ("Strict Quote-proof Gaps", report["quote_proof_gaps"], ["case_id", "workflow_type", "title", "strict_quote_proof_count", "required_quote_proof_count", "proof_gap", "next_action"]),
        ("Watchlist Triage", report["watchlist_triage"], ["case_id", "workflow_type", "title", "buyer", "deadline_date", "next_action"]),
        ("Deadline Risks", report["deadline_risks"], ["case_id", "workflow_type", "title", "deadline_date", "days_left", "next_action"]),
        ("Stale Or Failed Agent Runs", report["stale_or_failed_agent_runs"], ["run_id", "agent_name", "run_date", "status", "next_action"]),
        ("Source Blockers", report["source_blockers"], ["name", "health_status", "blocker", "last_checked", "next_action"]),
        ("Plugin Blockers", report["plugin_blockers"], ["name", "health_status", "blocker", "last_checked", "next_action"]),
    ]
    body = f"""
<h1>Tender Export OS Operating Desk</h1>
<p class='note'>Generated {html.escape(report['generated_at'])} from internal ledgers.</p>
<div class='action'><strong>One smallest owner action:</strong> {html.escape(report['one_smallest_owner_action'])}</div>
<div class='metrics'>{metrics}</div>
"""
    for title, rows, columns in sections:
        body += f"<h2>{html.escape(title)}</h2>{render_table(rows, columns)}"
    body += f"<p class='note'>{html.escape(report['safety_note'])}</p>"
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Operating Desk</title><style>{css}</style></head><body>{body}</body></html>"


def write_report(report: dict[str, Any], output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"operating_desk_{report['report_date']}"
    json_path = output_dir / f"{stem}.json"
    html_path = output_dir / f"{stem}.html"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    return json_path, html_path


def append_run_log(
    report: dict[str, Any],
    json_path: Path,
    html_path: Path,
    run_log_file: Path = RUN_LOG_FILE,
    project_root: Path = PROJECT_ROOT,
) -> None:
    now = dt.datetime.now().replace(microsecond=0)
    run_log_file.parent.mkdir(parents=True, exist_ok=True)
    write_header = not run_log_file.exists() or run_log_file.stat().st_size == 0
    row = {
        "run_id": f"RUN-{now.strftime('%Y%m%d%H%M%S')}-OPERATING-DESK",
        "run_date": now.date().isoformat(),
        "run_time": now.time().isoformat(),
        "agent_name": "hermes_chief_operator",
        "trigger_type": "manual_or_cron",
        "cases_processed": (
            len(report["supplier_search_cases"])
            + len(report["watchlist_triage"])
            + len(report["deadline_risks"])
        ),
        "cases_created": 0,
        "cases_rejected": 0,
        "cases_updated": 0,
        "sources_checked": len(report["source_blockers"]),
        "sources_failed": len(report["source_blockers"]),
        "actions_taken": "generate_operating_desk_report",
        "approval_cards_created": 0,
        "receipts_created": 0,
        "errors": 0,
        "warnings": len(report["source_blockers"]) + len(report["plugin_blockers"]),
        "runtime_seconds": 0,
        "status": "SUCCESS",
        "notes": f"Operating desk report generated: {json_path.relative_to(project_root)} and {html_path.relative_to(project_root)}; no external actions.",
    }
    with run_log_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RUN_LOG_HEADERS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Tender Export OS operating desk report")
    parser.add_argument("--date", help="Report date as YYYYMMDD or YYYY-MM-DD")
    parser.add_argument("--deadline-window-days", type=int, default=14)
    parser.add_argument("--stale-days", type=int, default=1)
    parser.add_argument("--no-log", action="store_true", help="Do not append data/agent_run_log.csv")
    args = parser.parse_args()

    today = parse_date(args.date or "") or dt.date.today()
    project_root = PROJECT_ROOT
    report = build_report(
        project_root=project_root,
        today=today,
        deadline_window_days=args.deadline_window_days,
        stale_days=args.stale_days,
    )
    json_path, html_path = write_report(report, project_root / "outputs" / "operating_desk")
    if not args.no_log:
        append_run_log(report, json_path, html_path, project_root / "data" / "agent_run_log.csv", project_root)
    print(f"Operating desk report: {json_path}")
    print(f"Operating desk HTML: {html_path}")
    print(f"One smallest owner action: {report['one_smallest_owner_action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
