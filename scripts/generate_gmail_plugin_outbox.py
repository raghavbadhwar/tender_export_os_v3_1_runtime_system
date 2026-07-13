#!/usr/bin/env python3
"""Prepare owner-approved buyer outreach handoffs for the Gmail plugin."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any
import yaml

try:
    from event_ledger import append_event
    from stage_buyer_market_research import read_csv
except ModuleNotFoundError:  # pragma: no cover
    from scripts.event_ledger import append_event
    from scripts.stage_buyer_market_research import read_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTBOX = PROJECT_ROOT / "runtime" / "gmail_plugin_outbox"
PREVIEW_DIR = PROJECT_ROOT / "outputs" / "gmail_plugin_outbox"
EXPECTED_ACTION = "send_buyer_introductory_outreach"
PREFLIGHT_CONFIG = PROJECT_ROOT / "config" / "gmail_send_preflight.yaml"


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def eligibility(outreach: dict[str, str], approval: dict[str, str] | None) -> list[str]:
    blockers: list[str] = []
    if not approval:
        return ["approval record missing"]
    if outreach.get("approval_status") != "APPROVED":
        blockers.append("outreach approval_status is not APPROVED")
    if approval.get("approval_status") != "APPROVED":
        blockers.append("approval record is not APPROVED")
    if approval.get("action_approved") != EXPECTED_ACTION:
        blockers.append("approval action does not authorize introductory outreach")
    if approval.get("case_id") != outreach.get("case_id"):
        blockers.append("approval case_id does not match outreach")
    if not approval.get("receipt_path") or not approval.get("scope_hash"):
        blockers.append("approval receipt or scope hash missing")
    if outreach.get("send_status") != "READY_AFTER_APPROVAL":
        blockers.append("outreach send_status is not READY_AFTER_APPROVAL")
    if outreach.get("channel") != "EMAIL":
        blockers.append("channel is not EMAIL")
    if "@" not in (outreach.get("verified_contact") or ""):
        blockers.append("verified public email contact missing")
    if not outreach.get("draft_path"):
        blockers.append("draft path missing")
    return blockers


def load_preflight_policy(path: Path = PREFLIGHT_CONFIG) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def build_packet(
    outreach: dict[str, str],
    approval: dict[str, str],
    *,
    body: str,
    sender_account: str = "raghavbadhwar7@gmail.com",
) -> dict[str, Any]:
    content_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    idempotency = hashlib.sha256(
        f"{outreach['outreach_id']}|{approval['scope_hash']}|{outreach['subject']}|{body}".encode("utf-8")
    ).hexdigest()
    return {
        "connector": "GMAIL_PLUGIN",
        "operation": "SEND_APPROVED_BUYER_OUTREACH",
        "sender_account": sender_account,
        "outreach_id": outreach["outreach_id"],
        "case_id": outreach["case_id"],
        "buyer_id": outreach["buyer_id"],
        "recipient": outreach["verified_contact"],
        "subject": outreach["subject"],
        "body_text": body,
        "content_sha256": content_sha256,
        "attachments": [],
        "approval_id": approval["approval_id"],
        "approval_receipt": approval["receipt_path"],
        "approval_scope_hash": approval["scope_hash"],
        "idempotency_key": idempotency,
        "send_authorized_by_owner": True,
        "fresh_approval_required_for_followup": True,
        "external_action_executed": False,
    }


def _hash_file(path_value: str) -> str:
    path = Path(path_value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prior_receipt_exists(
    *,
    outreach: dict[str, str],
    approval: dict[str, str],
    communication_rows: list[dict[str, str]],
) -> bool:
    if approval.get("external_effect") == "EXECUTED_AFTER_APPROVAL":
        return True
    if outreach.get("send_status") == "SENT" or outreach.get("external_message_id"):
        return True
    outreach_id = outreach.get("outreach_id", "")
    approval_id = approval.get("approval_id", "")
    return any(
        row.get("outreach_id") == outreach_id
        or (approval_id and approval_id in (row.get("source_receipt", "") + row.get("recommended_next_action", "")))
        for row in communication_rows
    )


def preflight_packet(
    packet: dict[str, Any],
    *,
    outreach: dict[str, str],
    approval: dict[str, str],
    communication_rows: list[dict[str, str]] | None = None,
    policy: dict[str, Any] | None = None,
    connector_status: str = "CONNECTED_GMAIL_PLUGIN",
) -> dict[str, Any]:
    policy = policy or load_preflight_policy()
    communication_rows = communication_rows or []
    blockers: list[str] = []
    required_fields = [str(value) for value in policy.get("required_packet_fields") or []]
    missing = [field for field in required_fields if field not in packet or packet.get(field) in ("", None)]
    if missing:
        blockers.append(f"missing packet fields: {', '.join(missing)}")
    if packet.get("connector") != policy.get("required_connector", "GMAIL_PLUGIN"):
        blockers.append("unsupported connector")
    if packet.get("sender_account") != policy.get("required_sender_account"):
        blockers.append("sender account mismatch")
    if connector_status != "CONNECTED_GMAIL_PLUGIN":
        blockers.append("ambiguous or disconnected Gmail plugin state")
    if packet.get("recipient") != outreach.get("verified_contact") or "@" not in str(packet.get("recipient", "")):
        blockers.append("recipient does not match verified outreach contact")
    if packet.get("approval_id") != approval.get("approval_id"):
        blockers.append("approval_id mismatch")
    if packet.get("approval_receipt") != approval.get("receipt_path"):
        blockers.append("approval receipt mismatch")
    if packet.get("approval_scope_hash") != approval.get("scope_hash") or not approval.get("scope_hash"):
        blockers.append("approval scope hash mismatch or missing")
    body = str(packet.get("body_text") or "")
    if hashlib.sha256(body.encode("utf-8")).hexdigest() != packet.get("content_sha256"):
        blockers.append("content hash mismatch")
    attachments = packet.get("attachments")
    if not isinstance(attachments, list):
        blockers.append("attachments must be a list")
    else:
        for index, item in enumerate(attachments):
            if not isinstance(item, dict):
                blockers.append(f"attachment[{index}] is not an object")
                continue
            path = str(item.get("path") or "")
            expected = str(item.get("sha256") or "")
            if not path or not expected:
                blockers.append(f"attachment[{index}] path or sha256 missing")
                continue
            try:
                if _hash_file(path) != expected:
                    blockers.append(f"attachment[{index}] hash mismatch")
            except OSError:
                blockers.append(f"attachment[{index}] cannot be read")
    if not packet.get("idempotency_key"):
        blockers.append("idempotency key missing")
    if _prior_receipt_exists(outreach=outreach, approval=approval, communication_rows=communication_rows):
        blockers.append("prior sent receipt or executed approval exists")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "connector": packet.get("connector"),
        "sender_account": packet.get("sender_account"),
        "recipient": packet.get("recipient"),
        "content_sha256": packet.get("content_sha256"),
        "idempotency_key": packet.get("idempotency_key"),
        "external_action_executed": False,
    }


def draft_body(path_value: str) -> str:
    path = Path(path_value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    text = path.read_text(encoding="utf-8")
    if text.startswith("# "):
        _, _, text = text.partition("\n\n")
    text = text.split("\n---\n", 1)[0]
    return text.strip() + "\n"


def generate_outbox(*, write_outbox: bool) -> dict[str, Any]:
    _, outreach_rows = read_csv(DATA_DIR / "outreach_queue.csv")
    _, approval_rows = read_csv(DATA_DIR / "approvals_receipts.csv")
    _, communication_rows = read_csv(DATA_DIR / "communication_log.csv")
    approvals = {row.get("approval_id", ""): row for row in approval_rows}
    policy = load_preflight_policy()
    packets = []
    blocked = []
    target_dir = OUTBOX if write_outbox else PREVIEW_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    for outreach in outreach_rows:
        if outreach.get("send_status") not in {"READY_AFTER_APPROVAL", "DRAFT_ONLY"}:
            continue
        approval = approvals.get(outreach.get("approval_id", ""))
        blockers = eligibility(outreach, approval)
        if blockers:
            blocked.append({"outreach_id": outreach.get("outreach_id", ""), "blockers": blockers})
            continue
        assert approval is not None
        body = draft_body(outreach["draft_path"])
        packet = build_packet(
            outreach,
            approval,
            body=body,
            sender_account=str(policy.get("required_sender_account") or ""),
        )
        preflight = preflight_packet(
            packet,
            outreach=outreach,
            approval=approval,
            communication_rows=communication_rows,
            policy=policy,
        )
        if not preflight["ok"]:
            blocked.append(
                {
                    "outreach_id": outreach.get("outreach_id", ""),
                    "blockers": preflight["blockers"],
                    "preflight": preflight,
                }
            )
            continue
        packet["preflight"] = preflight
        path = target_dir / f"gmail_send_{outreach['outreach_id']}.json"
        path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        packets.append({"outreach_id": outreach["outreach_id"], "path": relative(path), "idempotency_key": packet["idempotency_key"]})
        if write_outbox:
            append_event(
                "outreach.gmail_handoff_prepared",
                "gmail_plugin_outbox_generator",
                case_id=outreach["case_id"],
                object_type="outreach",
                object_id=outreach["outreach_id"],
                source="gmail_plugin_outbox",
                payload={
                    "outreach_id": outreach["outreach_id"],
                    "approval_id": approval["approval_id"],
                    "outbox_path": relative(path),
                    "external_action_executed": False,
                },
                citations=[relative(path), outreach["draft_path"], approval["receipt_path"]],
                idempotency_key=f"gmail-outbox:{packet['idempotency_key']}",
            )
    return {
        "mode": "OUTBOX_WRITTEN" if write_outbox else "PREVIEW",
        "packet_count": len(packets),
        "blocked_count": len(blocked),
        "packets": packets,
        "blocked": blocked,
        "external_action_executed": False,
        "safety": "Handoff generation only. The Gmail plugin must perform and receipt any approved send.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Gmail-plugin handoffs for approved buyer outreach")
    parser.add_argument("--write-outbox", action="store_true")
    args = parser.parse_args()
    result = generate_outbox(write_outbox=args.write_outbox)
    report = PREVIEW_DIR / f"outbox_report_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"mode": result["mode"], "packets": result["packet_count"], "blocked": result["blocked_count"], "report": relative(report)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
