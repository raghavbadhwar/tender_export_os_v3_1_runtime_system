#!/usr/bin/env python3
"""Record Gmail-plugin send receipts without performing an email operation."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from stage_buyer_market_research import blank_row, event_for_row, read_csv, upsert_csv
except ModuleNotFoundError:  # pragma: no cover
    from scripts.stage_buyer_market_research import blank_row, event_for_row, read_csv, upsert_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("connector") != "GMAIL_PLUGIN":
        raise ValueError("send receipt ingestion accepts only connector=GMAIL_PLUGIN")
    if not isinstance(payload.get("sends"), list):
        raise ValueError("sends must be a list")


def ingest(payload: dict[str, Any], *, input_path: Path, persist: bool) -> dict[str, Any]:
    validate_payload(payload)
    _, outreach_rows = read_csv(DATA_DIR / "outreach_queue.csv")
    outreach_by_id = {row.get("outreach_id", ""): row for row in outreach_rows}
    _, approval_rows = read_csv(DATA_DIR / "approvals_receipts.csv")
    approvals = {row.get("approval_id", ""): row for row in approval_rows}
    _, case_rows = read_csv(DATA_DIR / "master_cases.csv")
    cases = {row.get("case_id", ""): row for row in case_rows}
    _, signal_rows = read_csv(DATA_DIR / "buyer_demand_signals.csv")
    signals_by_case = {
        row.get("case_id", ""): row for row in signal_rows if row.get("case_id")
    }
    _, communication_rows = read_csv(DATA_DIR / "communication_log.csv")
    communication_ids = {
        row.get("communication_id", "") for row in communication_rows if row.get("communication_id")
    }
    recorded = []
    invalid = []
    duplicate_count = 0
    for item in payload["sends"]:
        if not isinstance(item, dict):
            invalid.append("send item is not an object")
            continue
        outreach = outreach_by_id.get(str(item.get("outreach_id") or ""))
        if not outreach:
            invalid.append(f"unknown outreach_id {item.get('outreach_id', '')}")
            continue
        approval = approvals.get(outreach.get("approval_id", ""), {})
        if approval.get("approval_status") != "APPROVED":
            invalid.append(f"outreach {outreach['outreach_id']} has no current approved receipt")
            continue
        case = cases.get(outreach.get("case_id", ""))
        if not case:
            invalid.append(f"outreach {outreach['outreach_id']} references a missing case")
            continue
        status = str(item.get("status") or "").upper()
        if status not in {"SENT", "FAILED"}:
            invalid.append(f"outreach {outreach['outreach_id']} has unsupported status {status}")
            continue
        if status == "SENT" and not all(item.get(field) for field in ("external_message_id", "external_thread_id", "sent_at")):
            invalid.append(f"outreach {outreach['outreach_id']} SENT receipt is missing message/thread/time")
            continue
        updated = dict(outreach)
        updated["send_status"] = status
        updated["sent_at"] = str(item.get("sent_at") or "")
        updated["external_message_id"] = str(item.get("external_message_id") or "")
        updated["external_thread_id"] = str(item.get("external_thread_id") or "")
        updated["updated_at"] = dt.datetime.now(dt.timezone.utc).date().isoformat()
        if status == "FAILED":
            updated["stop_reason"] = str(item.get("error") or "GMAIL_PLUGIN_SEND_FAILED")
        communication_id = f"COM-{hashlib.sha256(str(item.get('external_message_id') or outreach['outreach_id']).encode()).hexdigest()[:16].upper()}"
        is_duplicate = False
        if persist:
            citations = [relative(input_path), approval.get("receipt_path", ""), outreach.get("draft_path", "")]
            upsert_csv(DATA_DIR / "outreach_queue.csv", "outreach_id", updated)
            event_for_row("outreach", updated["outreach_id"], updated, False, citations, case_id=updated["case_id"])
            if status == "SENT":
                execution_receipt = relative(input_path)
                updated_approval = dict(approval)
                updated_approval["external_effect"] = "EXECUTED_AFTER_APPROVAL"
                execution_note = f"Gmail execution receipt: {execution_receipt}"
                if execution_note not in (updated_approval.get("notes") or ""):
                    updated_approval["notes"] = "; ".join(
                        value for value in (updated_approval.get("notes", ""), execution_note) if value
                    )
                upsert_csv(DATA_DIR / "approvals_receipts.csv", "approval_id", updated_approval)
                event_for_row(
                    "approval",
                    updated_approval["approval_id"],
                    updated_approval,
                    False,
                    citations,
                    case_id=updated["case_id"],
                )
                approvals[updated_approval["approval_id"]] = updated_approval

                updated_case = dict(case)
                if updated_case.get("status") == "APPROVED":
                    updated_case["status"] = "SENT_OR_SUBMITTED"
                if "submitted_at" in updated_case:
                    updated_case["submitted_at"] = updated["sent_at"]
                updated_case["updated_at"] = dt.datetime.now(dt.timezone.utc).date().isoformat()
                upsert_csv(DATA_DIR / "master_cases.csv", "case_id", updated_case)
                event_for_row(
                    "case",
                    updated_case["case_id"],
                    updated_case,
                    False,
                    citations,
                    case_id=updated["case_id"],
                )
                cases[updated_case["case_id"]] = updated_case

                signal = signals_by_case.get(updated["case_id"])
                if signal:
                    updated_signal = dict(signal)
                    updated_signal["next_safe_action"] = "AWAIT_BUYER_REPLY"
                    updated_signal["updated_at"] = dt.datetime.now(dt.timezone.utc).date().isoformat()
                    upsert_csv(DATA_DIR / "buyer_demand_signals.csv", "signal_id", updated_signal)
                    event_for_row(
                        "buyer_demand_signal",
                        updated_signal["signal_id"],
                        updated_signal,
                        False,
                        citations,
                        case_id=updated["case_id"],
                    )
                    signals_by_case[updated["case_id"]] = updated_signal

                communication = blank_row(DATA_DIR / "communication_log.csv")
                communication.update(
                    {
                        "communication_id": communication_id,
                        "outreach_id": updated["outreach_id"],
                        "case_id": updated["case_id"],
                        "buyer_id": updated["buyer_id"],
                        "direction": "OUTBOUND",
                        "channel": "EMAIL",
                        "external_message_id": updated["external_message_id"],
                        "external_thread_id": updated["external_thread_id"],
                        "occurred_at": updated["sent_at"],
                        "subject": updated["subject"],
                        "content_path": updated["draft_path"],
                        "classification": "OUTREACH_SENT",
                        "requires_owner_action": "FALSE",
                        "recommended_next_action": "Wait for a reply; any follow-up requires a fresh owner approval.",
                        "source_connector": "GMAIL_PLUGIN",
                        "source_receipt": relative(input_path),
                        "created_at": dt.datetime.now(dt.timezone.utc).date().isoformat(),
                    }
                )
                if communication_id in communication_ids:
                    # Gmail receipt replay is expected when the monitor moves
                    # an already-ingested packet into processed/.  Keep the
                    # first immutable communication row and emit no update
                    # event, so a replay cannot duplicate or rewrite history.
                    duplicate_count += 1
                    is_duplicate = True
                else:
                    upsert_csv(DATA_DIR / "communication_log.csv", "communication_id", communication)
                    event_for_row(
                        "communication",
                        communication_id,
                        communication,
                        True,
                        citations,
                        case_id=updated["case_id"],
                    )
                    communication_ids.add(communication_id)
        recorded.append(
            {
                "outreach_id": updated["outreach_id"],
                "status": status,
                "communication_id": communication_id if status == "SENT" else "",
                "persisted": persist,
                "duplicate": is_duplicate,
            }
        )
    return {
        "connector": "GMAIL_PLUGIN",
        "mode": "INGESTED" if persist else "DRY_RUN",
        "recorded_count": len(recorded),
        "duplicate_count": duplicate_count,
        "invalid_count": len(invalid),
        "recorded": recorded,
        "invalid": invalid,
        "external_action_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Gmail-plugin buyer outreach send receipts")
    parser.add_argument("--input", required=True)
    parser.add_argument("--ingest", action="store_true")
    args = parser.parse_args()
    path = Path(args.input)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    result = ingest(json.loads(path.read_text(encoding="utf-8")), input_path=path, persist=args.ingest)
    print(json.dumps(result, indent=2))
    return 0 if not result["invalid_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
