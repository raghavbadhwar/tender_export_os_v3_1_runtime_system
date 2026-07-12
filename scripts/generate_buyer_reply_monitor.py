#!/usr/bin/env python3
"""Generate the owner-facing buyer reply monitor from connector-ingested state."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    from event_ledger import append_event
    from generate_gmail_plugin_outbox import generate_outbox
    from ingest_gmail_send_receipts import ingest as ingest_send_receipts
    from ingest_buyer_replies import ingest_payload
    from stage_buyer_market_research import event_for_row, upsert_csv
except ModuleNotFoundError:  # pragma: no cover
    from scripts.event_ledger import append_event
    from scripts.generate_gmail_plugin_outbox import generate_outbox
    from scripts.ingest_gmail_send_receipts import ingest as ingest_send_receipts
    from scripts.ingest_buyer_replies import ingest_payload
    from scripts.stage_buyer_market_research import event_for_row, upsert_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
INBOX = PROJECT_ROOT / "runtime" / "gmail_plugin_inbox"
SEND_RECEIPTS_INBOX = PROJECT_ROOT / "runtime" / "gmail_plugin_send_receipts"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "buyer_replies"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def connector_status(inbox: Path = INBOX) -> str:
    status_path = inbox / "connector_status.json"
    if status_path.is_file():
        try:
            if json.loads(status_path.read_text(encoding="utf-8")).get("connected") is True:
                return "CONNECTED_GMAIL_PLUGIN"
        except (json.JSONDecodeError, OSError):
            return "CONNECTOR_STATUS_INVALID"
    gmail_plugin = Path.home() / ".codex" / "plugins" / "cache" / "openai-curated-remote" / "gmail"
    return "PLUGIN_INSTALLED_AWAITING_AUTOMATION" if gmail_plugin.exists() else "GMAIL_PLUGIN_NOT_INSTALLED"


def apply_approval_state(outreach: dict[str, str], approval: dict[str, str]) -> dict[str, str]:
    updated = dict(outreach)
    status = (approval.get("approval_status") or "PENDING").upper()
    updated["approval_status"] = status
    if status == "APPROVED" and updated.get("send_status") not in {"SENT", "STOPPED"}:
        updated["send_status"] = "READY_AFTER_APPROVAL"
    elif status in {"REJECTED", "SUPERSEDED"}:
        updated["send_status"] = "STOPPED"
        updated["stop_reason"] = f"APPROVAL_{status}"
        updated["next_follow_up_at"] = ""
    elif status == "CHANGES_REQUESTED" and updated.get("send_status") != "STOPPED":
        updated["send_status"] = "DRAFT_ONLY"
        updated["stop_reason"] = "APPROVAL_CHANGES_REQUESTED"
    updated["updated_at"] = dt.datetime.now(dt.timezone.utc).date().isoformat()
    return updated


def sync_outreach_approvals() -> int:
    approvals = {row.get("approval_id", ""): row for row in read_csv(DATA_DIR / "approvals_receipts.csv")}
    changed = 0
    for outreach in read_csv(DATA_DIR / "outreach_queue.csv"):
        approval = approvals.get(outreach.get("approval_id", ""))
        if not approval:
            continue
        updated = apply_approval_state(outreach, approval)
        if updated == outreach:
            continue
        upsert_csv(DATA_DIR / "outreach_queue.csv", "outreach_id", updated)
        event_for_row(
            "outreach",
            updated["outreach_id"],
            updated,
            False,
            ["data/approvals_receipts.csv", "data/outreach_queue.csv", approval.get("receipt_path", "")],
            case_id=updated.get("case_id", ""),
        )
        changed += 1
    return changed


def process_inbox(inbox: Path = INBOX) -> list[dict[str, Any]]:
    processed_dir = inbox / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted(inbox.glob("*.json")):
        if path.name == "connector_status.json":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = ingest_payload(payload, input_path=path, persist=True)
        results.append({"input": relative(path), **result})
        path.replace(processed_dir / path.name)
    return results


def process_send_receipt_inbox(inbox: Path = SEND_RECEIPTS_INBOX) -> list[dict[str, Any]]:
    processed_dir = inbox / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted(inbox.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = ingest_send_receipts(payload, input_path=path, persist=True)
        results.append({"input": relative(path), **result})
        path.replace(processed_dir / path.name)
    return results


def build_report(*, now: dt.datetime | None = None, connector: str | None = None) -> dict[str, Any]:
    generated_at = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc).replace(microsecond=0)
    communications = read_csv(DATA_DIR / "communication_log.csv")
    outreach = {row.get("outreach_id", ""): row for row in read_csv(DATA_DIR / "outreach_queue.csv")}
    buyers = {row.get("buyer_id", ""): row for row in read_csv(DATA_DIR / "buyer_master.csv")}
    cutoff = generated_at - dt.timedelta(days=7)
    replies = []
    for row in communications:
        if row.get("direction") != "INBOUND":
            continue
        try:
            occurred = dt.datetime.fromisoformat(row.get("occurred_at", "").replace("Z", "+00:00"))
            if occurred.tzinfo is None:
                occurred = occurred.replace(tzinfo=dt.timezone.utc)
            if occurred < cutoff:
                continue
        except ValueError:
            pass
        outreach_row = outreach.get(row.get("outreach_id", ""), {})
        buyer = buyers.get(row.get("buyer_id", ""), {})
        replies.append(
            {
                "communication_id": row.get("communication_id", ""),
                "outreach_id": row.get("outreach_id", ""),
                "case_id": row.get("case_id", ""),
                "buyer_name": buyer.get("buyer_name", ""),
                "subject": row.get("subject", ""),
                "classification": row.get("classification", ""),
                "occurred_at": row.get("occurred_at", ""),
                "requires_owner_action": row.get("requires_owner_action") == "TRUE",
                "recommended_next_action": row.get("recommended_next_action", ""),
                "content_path": row.get("content_path", ""),
                "stop_reason": outreach_row.get("stop_reason", ""),
            }
        )
    replies.sort(key=lambda item: item["occurred_at"], reverse=True)
    owner_actions = [item for item in replies if item["requires_owner_action"]]
    return {
        "run_id": f"REPLYMON-{generated_at.strftime('%Y%m%dT%H%M%SZ')}",
        "generated_at": generated_at.isoformat(),
        "connector_status": connector or connector_status(),
        "new_reply_count": len(replies),
        "owner_action_count": len(owner_actions),
        "replies": replies,
        "owner_actions": owner_actions,
        "external_action_executed": False,
        "safety": "Reply monitor only. It never sends, follows up, quotes, or makes commitments.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Buyer Reply Monitor — {report['generated_at']}",
        "",
        f"Connector: {report['connector_status']}",
        f"Replies in last 7 days: {report['new_reply_count']}",
        f"Owner actions: {report['owner_action_count']}",
        "",
        report["safety"],
        "",
    ]
    if not report["replies"]:
        lines.append("No ingested buyer replies in the last 7 days.")
    for reply in report["replies"]:
        lines.extend(
            [
                f"## {reply['buyer_name'] or reply['case_id']} — {reply['classification']}",
                "",
                f"- Case: {reply['case_id']}",
                f"- Subject: {reply['subject']}",
                f"- Received: {reply['occurred_at']}",
                f"- Owner action: {'yes' if reply['requires_owner_action'] else 'no'}",
                f"- Next: {reply['recommended_next_action']}",
                f"- Private content: `{reply['content_path']}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Process Gmail-plugin reply exports and generate owner monitor")
    parser.add_argument("--process-inbox", action="store_true")
    parser.add_argument("--record-event", action="store_true")
    args = parser.parse_args()
    approval_sync_count = sync_outreach_approvals()
    current_connector_status = connector_status()
    outbox_result = generate_outbox(write_outbox=current_connector_status == "CONNECTED_GMAIL_PLUGIN")
    send_receipt_results = process_send_receipt_inbox() if args.process_inbox else []
    inbox_results = process_inbox() if args.process_inbox else []
    report = build_report(connector=current_connector_status)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"buyer_reply_monitor_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    json_path = OUTPUT_DIR / f"{stem}.json"
    md_path = OUTPUT_DIR / f"{stem}.md"
    json_path.write_text(
        json.dumps(
            {
                **report,
                "approval_sync_count": approval_sync_count,
                "outbox_result": outbox_result,
                "send_receipt_results": send_receipt_results,
                "inbox_results": inbox_results,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    if args.record_event:
        append_event(
            "buyer_reply.monitor_completed",
            "buyer_reply_monitor",
            object_type="reply_monitor",
            object_id=report["run_id"],
            source="gmail_plugin_reply_inbox",
            payload={
                "run_id": report["run_id"],
                "report_path": relative(json_path),
                "new_reply_count": report["new_reply_count"],
                "connector_status": report["connector_status"],
                "owner_action_count": report["owner_action_count"],
            },
            citations=[relative(json_path), relative(md_path), "data/communication_log.csv", "data/outreach_queue.csv"],
            idempotency_key=f"buyer-reply-monitor:{report['run_id']}",
        )
    print(json.dumps({"connector_status": report["connector_status"], "replies": report["new_reply_count"], "owner_actions": report["owner_action_count"], "report": relative(json_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
