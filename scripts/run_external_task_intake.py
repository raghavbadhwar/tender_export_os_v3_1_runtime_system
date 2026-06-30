#!/usr/bin/env python3
"""Safe external task/source intake for Tender Export OS cron jobs.

This script performs only safe external reads:
- public HTTP GET/HEAD style page probes for non-login, non-paywalled sources
- external task inbox CSV review
- local report/event/run-log writing

It never sends supplier/buyer messages, submits tenders/RFQs, logs in, pays,
uses DSC, commits prices/terms, or confirms HSN/ITC-HS/origin claims.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup

from event_ledger import append_event

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "external_intake"
INBOX = DATA_DIR / "external_task_inbox.csv"
AGENT_RUN_LOG = DATA_DIR / "agent_run_log.csv"

INBOX_FIELDS = [
    "task_id",
    "received_at",
    "source_channel",
    "source_reference",
    "request_text",
    "case_id",
    "priority",
    "status",
    "approval_required",
    "notes",
    "citations",
]

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

BLOCKED_PATTERNS = re.compile(
    r"captcha|access denied|forbidden|login|sign in|enable javascript|cloudflare|unusual traffic",
    re.IGNORECASE,
)

USER_AGENT = (
    "TenderExportOS-SafeProbe/1.0 "
    "(+internal owner cron; public GET only; no login/no submit)"
)


def now_local() -> dt.datetime:
    return dt.datetime.now().astimezone()


def run_id(prefix: str = "RUN") -> str:
    return f"{prefix}-{now_local().strftime('%Y%m%d%H%M%S')}"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def load_sources() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for workflow, filename in [("GOV", "sources.gov.yaml"), ("EXPORT", "sources.export.yaml")]:
        path = CONFIG_DIR / filename
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for item in data.get("sources", []):
            item = dict(item)
            item.setdefault("workflow", workflow)
            item["config_file"] = rel(path)
            rows.append(item)
    return rows


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def public_probe_candidates(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for source in sources:
        if truthy(source.get("login_required")) or truthy(source.get("paywalled")):
            continue
        if str(source.get("health_status", "")).lower() not in {"working", "untested", "manual check required"}:
            continue
        url = str(source.get("api_url") or source.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue
        source = dict(source)
        source["probe_url"] = url
        candidates.append(source)
    return candidates


def page_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("title")
    if title and title.get_text(strip=True):
        return title.get_text(" ", strip=True)[:220]
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(" ", strip=True)[:220]
    text = soup.get_text(" ", strip=True)
    return text[:220]


def probe_source(source: dict[str, Any], timeout: int) -> dict[str, Any]:
    started = time.time()
    url = source["probe_url"]
    result: dict[str, Any] = {
        "source_name": source.get("name", ""),
        "workflow": source.get("workflow", ""),
        "source_type": source.get("type", ""),
        "url": url,
        "config_file": source.get("config_file", ""),
        "status": "UNKNOWN",
        "http_status": None,
        "final_url": "",
        "title": "",
        "content_sha256_16": "",
        "elapsed_ms": 0,
        "notes": "",
    }
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"},
            timeout=timeout,
            allow_redirects=True,
        )
        body = response.text[:250_000]
        result["http_status"] = response.status_code
        result["final_url"] = response.url
        result["content_sha256_16"] = hashlib.sha256(body.encode("utf-8", "ignore")).hexdigest()[:16]
        result["title"] = page_title(body)
        if response.status_code >= 500:
            result["status"] = "SOURCE_ERROR"
        elif response.status_code in {401, 403}:
            result["status"] = "BLOCKED"
        elif BLOCKED_PATTERNS.search(body[:20_000]):
            result["status"] = "BLOCKED_OR_LOGIN_WALL"
        elif response.status_code >= 400:
            result["status"] = "HTTP_ERROR"
        else:
            result["status"] = "REACHABLE"
        result["notes"] = f"Public read-only probe; no login, form submit, download purchase, or external business action. Domain={urlparse(response.url).netloc}"
    except Exception as exc:  # noqa: BLE001 - diagnostic script should record all probe failures
        result["status"] = "PROBE_FAILED"
        result["notes"] = f"{type(exc).__name__}: {exc}"
    finally:
        result["elapsed_ms"] = int((time.time() - started) * 1000)
    return result


def ensure_inbox() -> list[dict[str, str]]:
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    if not INBOX.exists():
        with INBOX.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=INBOX_FIELDS).writeheader()
        return []
    with INBOX.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # Normalize missing columns without discarding unknown data.
    if reader.fieldnames != INBOX_FIELDS:
        normalized = [{field: row.get(field, "") for field in INBOX_FIELDS} for row in rows]
        with INBOX.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=INBOX_FIELDS)
            writer.writeheader()
            writer.writerows(normalized)
        rows = normalized
    return rows


def intake_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    actionable_statuses = {"NEW", "OPEN", "PENDING", "APPROVAL_REQUIRED", ""}
    pending = [r for r in rows if r.get("status", "").strip().upper() in actionable_statuses]
    gated = [r for r in pending if str(r.get("approval_required", "")).strip().lower() in {"true", "yes", "1"}]
    return {
        "inbox_path": rel(INBOX),
        "total_tasks": len(rows),
        "pending_tasks": len(pending),
        "approval_gated_pending_tasks": len(gated),
        "pending_preview": pending[:10],
    }


def write_agent_run(row: dict[str, Any]) -> None:
    AGENT_RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    exists = AGENT_RUN_LOG.exists()
    with AGENT_RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RUN_LOG_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in RUN_LOG_FIELDS})


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        f"# External Intake Report — {report['generated_at']}",
        "",
        "Safety: public read-only/source-intake only. No supplier/buyer messages, submissions, payments, DSC, final classification/origin claims, or price commitments.",
        "",
        "## Source probe summary",
        f"- Sources checked: {report['summary']['sources_checked']}",
        f"- Reachable: {report['summary']['reachable']}",
        f"- Blocked/login/CAPTCHA-like: {report['summary']['blocked']}",
        f"- Failed/errors: {report['summary']['failed']}",
        "",
        "| Source | Workflow | Status | HTTP | Title / Notes |",
        "|---|---|---:|---:|---|",
    ]
    for p in report["source_probes"]:
        title = (p.get("title") or p.get("notes") or "").replace("|", "-")[:140]
        lines.append(f"| {p.get('source_name','')} | {p.get('workflow','')} | {p.get('status','')} | {p.get('http_status') or ''} | {title} |")
    lines.extend([
        "",
        "## External task inbox",
        f"- Inbox: `{report['task_intake']['inbox_path']}`",
        f"- Total tasks: {report['task_intake']['total_tasks']}",
        f"- Pending tasks: {report['task_intake']['pending_tasks']}",
        f"- Approval-gated pending tasks: {report['task_intake']['approval_gated_pending_tasks']}",
        "",
        "Recommended action: Review pending inbox tasks and approval-gated blockers before any external execution.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe external task/source intake")
    parser.add_argument("--limit", type=int, default=8, help="Max public sources to probe")
    parser.add_argument("--timeout", type=int, default=12, help="HTTP timeout seconds")
    parser.add_argument("--record-event", action="store_true", help="Append schema-valid event ledger rows")
    parser.add_argument("--no-agent-log", action="store_true", help="Do not append agent_run_log row")
    args = parser.parse_args()

    started = time.time()
    stamp = now_local().strftime("%Y%m%d_%H%M%S")
    rid = run_id()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sources = load_sources()
    candidates = public_probe_candidates(sources)[: max(0, args.limit)]
    probes = [probe_source(source, args.timeout) for source in candidates]
    inbox_rows = ensure_inbox()
    summary = {
        "sources_checked": len(probes),
        "reachable": sum(p["status"] == "REACHABLE" for p in probes),
        "blocked": sum("BLOCKED" in p["status"] for p in probes),
        "failed": sum(p["status"] in {"PROBE_FAILED", "SOURCE_ERROR", "HTTP_ERROR"} for p in probes),
    }
    report = {
        "run_id": rid,
        "generated_at": now_local().isoformat(timespec="seconds"),
        "safety": "public_read_only_no_external_business_action",
        "summary": summary,
        "source_probes": probes,
        "task_intake": intake_summary(inbox_rows),
    }

    json_path = OUTPUT_DIR / f"external_intake_report_{stamp}.json"
    md_path = OUTPUT_DIR / f"external_intake_report_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(report, md_path)

    events = []
    if args.record_event:
        events.append(
            append_event(
                "source_adapter.external_probe_ran",
                "external_task_intake",
                object_type="source_adapter",
                object_id="public_safe_probe",
                source="public_web_read_only",
                payload={
                    "run_id": rid,
                    "sources_checked": summary["sources_checked"],
                    "reachable": summary["reachable"],
                    "blocked": summary["blocked"],
                    "failed": summary["failed"],
                    "report": rel(json_path),
                },
                citations=[rel(json_path), rel(md_path), "config/sources.gov.yaml", "config/sources.export.yaml"],
            )
        )
        events.append(
            append_event(
                "external_task.intake_checked",
                "external_task_intake",
                object_type="external_task",
                object_id="external_task_inbox",
                source="local_inbox_csv",
                payload={
                    "run_id": rid,
                    "total_tasks": report["task_intake"]["total_tasks"],
                    "pending_tasks": report["task_intake"]["pending_tasks"],
                    "approval_gated_pending_tasks": report["task_intake"]["approval_gated_pending_tasks"],
                    "inbox": rel(INBOX),
                    "report": rel(json_path),
                },
                citations=[rel(INBOX), rel(json_path), rel(md_path)],
            )
        )

    warnings = summary["blocked"] + summary["failed"]
    if not args.no_agent_log:
        n = now_local()
        write_agent_run(
            {
                "run_id": rid,
                "run_date": n.strftime("%Y-%m-%d"),
                "run_time": n.strftime("%H:%M:%S"),
                "agent_name": "external_task_intake",
                "trigger_type": "cron_or_manual_safe_external_intake",
                "cases_processed": 0,
                "cases_created": 0,
                "cases_rejected": 0,
                "cases_updated": 0,
                "sources_checked": summary["sources_checked"],
                "sources_failed": summary["failed"],
                "actions_taken": "public_source_probes;external_task_inbox_review;local_reports;schema_valid_events" if args.record_event else "public_source_probes;external_task_inbox_review;local_reports",
                "approval_cards_created": 0,
                "receipts_created": 1,
                "errors": 0,
                "warnings": warnings,
                "runtime_seconds": int(time.time() - started),
                "status": "SUCCESS_WITH_WARNINGS" if warnings else "SUCCESS",
                "notes": f"Safe external intake report={rel(md_path)}; inbox_pending={report['task_intake']['pending_tasks']}; no supplier/buyer/submission/payment/DSC/final classification/origin/price action.",
            }
        )

    print(json.dumps({
        "run_id": rid,
        "status": "SUCCESS_WITH_WARNINGS" if warnings else "SUCCESS",
        "summary": summary,
        "task_intake": report["task_intake"],
        "json_report": rel(json_path),
        "markdown_report": rel(md_path),
        "events_recorded": len(events),
        "safety": report["safety"],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
