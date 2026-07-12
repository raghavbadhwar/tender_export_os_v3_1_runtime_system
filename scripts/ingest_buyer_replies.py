#!/usr/bin/env python3
"""Ingest structured buyer replies exported by the Gmail plugin.

This script never reads Gmail directly and never sends a reply. The connector
contract deliberately rejects gws, IMAP, and Himalaya exports for Gmail.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from stage_buyer_market_research import blank_row, event_for_row, read_csv, upsert_csv
except ModuleNotFoundError:  # pragma: no cover
    from scripts.stage_buyer_market_research import blank_row, event_for_row, read_csv, upsert_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPLY_RECEIPTS = PROJECT_ROOT / "receipts" / "buyer_replies"
ALLOWED_CONNECTOR = "GMAIL_PLUGIN"


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def stable_id(value: str, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length].upper()


def validate_connector_payload(payload: dict[str, Any]) -> None:
    if payload.get("connector") != ALLOWED_CONNECTOR:
        raise ValueError("buyer reply ingestion accepts only connector=GMAIL_PLUGIN; gws/IMAP/Himalaya are not permitted for Gmail operations")
    if not isinstance(payload.get("messages"), list):
        raise ValueError("messages must be a list")


def classify_reply(text: str) -> dict[str, Any]:
    normalized = " ".join(str(text or "").lower().split())
    if any(marker in normalized for marker in ("unsubscribe", "remove me", "remove us", "do not contact", "stop emailing")):
        return {
            "classification": "OPT_OUT",
            "requires_owner_action": False,
            "recommended_next_action": "Stop all outreach to this contact and preserve the opt-out receipt.",
        }
    if any(marker in normalized for marker in ("delivery status notification", "address not found", "undeliverable", "mail delivery failed", "550 5.")):
        return {
            "classification": "BOUNCE",
            "requires_owner_action": False,
            "recommended_next_action": "Stop this address and verify a different public business contact before requesting fresh approval.",
        }
    if any(marker in normalized for marker in ("automatic reply", "auto reply", "out of office", "away from the office")):
        return {
            "classification": "AUTO_REPLY",
            "requires_owner_action": False,
            "recommended_next_action": "Wait for the stated return window; do not auto-follow up.",
        }
    if any(marker in normalized for marker in ("not interested", "not a fit", "no requirement", "we are not looking")):
        return {
            "classification": "NOT_INTERESTED",
            "requires_owner_action": False,
            "recommended_next_action": "Close or cool the target; do not follow up unless the buyer explicitly reopens the conversation.",
        }
    if any(marker in normalized for marker in ("quote", "price", "pricing", "fob", "cif", "incoterm", "payment term", "discount", "ex works")):
        return {
            "classification": "NEGOTIATION",
            "requires_owner_action": True,
            "recommended_next_action": "Review commercially; prepare a draft only after supplier proof, pricing, compliance, and owner approval gates.",
        }
    if any(marker in normalized for marker in ("interested", "please send", "send the catalogue", "send catalogue", "send details", "would like to see", "open to reviewing")):
        return {
            "classification": "POSITIVE_INTEREST",
            "requires_owner_action": True,
            "recommended_next_action": "Review the request, verify the requested products, and prepare a factual response draft for owner approval.",
        }
    if "?" in normalized or normalized.startswith(("can you", "could you", "who ", "what ", "when ", "where ", "how ")):
        return {
            "classification": "QUESTION",
            "requires_owner_action": True,
            "recommended_next_action": "Answer only with verified facts in a new owner-approved response draft.",
        }
    return {
        "classification": "NEEDS_REVIEW",
        "requires_owner_action": True,
        "recommended_next_action": "Read the reply and choose the next action; no automatic response is allowed.",
    }


def resolve_outreach(message: dict[str, Any], outreach_rows: list[dict[str, str]]) -> dict[str, str] | None:
    outreach_id = str(message.get("outreach_id") or "").strip()
    if outreach_id:
        for row in outreach_rows:
            if row.get("outreach_id") == outreach_id:
                return row
    thread_id = str(message.get("external_thread_id") or "").strip()
    if thread_id:
        for row in outreach_rows:
            if row.get("external_thread_id") == thread_id:
                return row
    return None


def message_text(message: dict[str, Any]) -> str:
    return str(message.get("body_text") or message.get("snippet") or "").strip()


def valid_message(message: dict[str, Any]) -> list[str]:
    missing = [field for field in ("external_message_id", "received_at", "subject") if not str(message.get(field) or "").strip()]
    if not message_text(message):
        missing.append("body_text or snippet")
    return missing


def ingest_payload(payload: dict[str, Any], *, input_path: Path, persist: bool) -> dict[str, Any]:
    validate_connector_payload(payload)
    _, outreach_rows = read_csv(DATA_DIR / "outreach_queue.csv")
    _, communication_rows = read_csv(DATA_DIR / "communication_log.csv")
    existing_ids = {row.get("external_message_id") for row in communication_rows if row.get("external_message_id")}
    ingested: list[dict[str, Any]] = []
    duplicates: list[str] = []
    unmatched: list[str] = []
    invalid: list[dict[str, Any]] = []

    for message in payload["messages"]:
        if not isinstance(message, dict):
            invalid.append({"message": "non-object message", "missing": ["message object"]})
            continue
        external_id = str(message.get("external_message_id") or "").strip()
        missing = valid_message(message)
        if missing:
            invalid.append({"external_message_id": external_id, "missing": missing})
            continue
        if external_id in existing_ids:
            duplicates.append(external_id)
            continue
        outreach = resolve_outreach(message, outreach_rows)
        if outreach is None:
            unmatched.append(external_id)
            continue
        text = message_text(message)
        classification = classify_reply(f"{message.get('subject', '')}\n{text}")
        communication_id = f"COM-{stable_id(external_id)}"
        content_path = REPLY_RECEIPTS / f"{communication_id}.txt"
        source_receipt = REPLY_RECEIPTS / f"{communication_id}.json"
        if persist:
            REPLY_RECEIPTS.mkdir(parents=True, exist_ok=True)
            content_path.write_text(text + "\n", encoding="utf-8")
            source_receipt.write_text(
                json.dumps(
                    {
                        "communication_id": communication_id,
                        "connector": ALLOWED_CONNECTOR,
                        "input_path": relative(input_path),
                        "external_message_id": external_id,
                        "external_thread_id": message.get("external_thread_id", ""),
                        "received_at": message["received_at"],
                        "classification": classification["classification"],
                        "external_action_executed": False,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

        communication = blank_row(DATA_DIR / "communication_log.csv")
        communication.update(
            {
                "communication_id": communication_id,
                "outreach_id": outreach["outreach_id"],
                "case_id": outreach["case_id"],
                "buyer_id": outreach["buyer_id"],
                "direction": "INBOUND",
                "channel": "EMAIL",
                "external_message_id": external_id,
                "external_thread_id": message.get("external_thread_id", ""),
                "occurred_at": message["received_at"],
                "subject": message["subject"],
                "content_path": relative(content_path),
                "classification": classification["classification"],
                "requires_owner_action": "TRUE" if classification["requires_owner_action"] else "FALSE",
                "recommended_next_action": classification["recommended_next_action"],
                "source_connector": ALLOWED_CONNECTOR,
                "source_receipt": relative(source_receipt),
                "created_at": today(),
            }
        )
        updated_outreach = dict(outreach)
        updated_outreach["external_message_id"] = external_id
        updated_outreach["external_thread_id"] = str(message.get("external_thread_id") or outreach.get("external_thread_id") or "")
        updated_outreach["reply_status"] = {
            "OPT_OUT": "OPTED_OUT",
            "BOUNCE": "BOUNCED",
        }.get(classification["classification"], "REPLIED")
        updated_outreach["last_reply_at"] = str(message["received_at"])
        updated_outreach["updated_at"] = today()
        if classification["classification"] in {"OPT_OUT", "BOUNCE", "NOT_INTERESTED"}:
            updated_outreach["send_status"] = "STOPPED"
            updated_outreach["stop_reason"] = classification["classification"]
            updated_outreach["next_follow_up_at"] = ""

        if persist:
            citations = [relative(input_path), relative(content_path), relative(source_receipt)]
            created = upsert_csv(DATA_DIR / "communication_log.csv", "communication_id", communication)
            event_for_row("communication", communication_id, communication, created, citations, case_id=outreach["case_id"])
            upsert_csv(DATA_DIR / "outreach_queue.csv", "outreach_id", updated_outreach)
            event_for_row("outreach", outreach["outreach_id"], updated_outreach, False, citations, case_id=outreach["case_id"])
        ingested.append(
            {
                "communication_id": communication_id,
                "outreach_id": outreach["outreach_id"],
                "case_id": outreach["case_id"],
                "classification": classification["classification"],
                "requires_owner_action": classification["requires_owner_action"],
                "recommended_next_action": classification["recommended_next_action"],
                "persisted": persist,
            }
        )
        existing_ids.add(external_id)

    return {
        "connector": ALLOWED_CONNECTOR,
        "mode": "INGESTED" if persist else "DRY_RUN",
        "ingested_count": len(ingested),
        "duplicate_count": len(duplicates),
        "unmatched_count": len(unmatched),
        "invalid_count": len(invalid),
        "messages": ingested,
        "duplicates": duplicates,
        "unmatched": unmatched,
        "invalid": invalid,
        "external_action_executed": False,
        "safety": "Reply metadata was classified locally. No reply or follow-up was sent.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest buyer replies exported by the Gmail plugin")
    parser.add_argument("--input", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--ingest", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    result = ingest_payload(payload, input_path=input_path, persist=args.ingest)
    output = Path(args.output) if args.output else PROJECT_ROOT / "outputs" / "buyer_replies" / f"ingest_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"mode": result["mode"], "ingested": result["ingested_count"], "unmatched": result["unmatched_count"], "output": relative(output), "external_action_executed": False}, indent=2))
    return 0 if not result["invalid_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
