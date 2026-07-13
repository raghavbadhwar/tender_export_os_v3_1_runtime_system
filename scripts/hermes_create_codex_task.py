#!/usr/bin/env python3
"""Create a fallback Codex task file for manual/app-server-unavailable flows."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INBOX = PROJECT_ROOT / "runtime" / "codex_inbox"


def build_gov_bid_pack_task(case_id: str, input_artifacts: list[str]) -> dict[str, Any]:
    """Build a bounded, approval-safe packet for Codex artifact production."""
    pack_root = f"outputs/bid_packs/{case_id}"
    receipt_path = f"receipts/plugin_runs/{case_id}_bid_pack.json"
    packet = {
        "schema_version": "codex_bid_pack_task.v1",
        "task_type": "GOV_BID_PACK",
        "case_id": case_id,
        "workflow_type": "GOV",
        "task": "Build an internal draft bid pack only; do not submit, upload, contact, pay, use DSC, or make final commitments.",
        "input_artifacts": input_artifacts,
        "output_root": pack_root,
        "required_artifact_kinds": [
            "bid_cover",
            "boq",
            "compliance_matrix",
            "eligibility_declaration",
            "supplier_summary",
            "emd_security_plan",
            "delivery_plan",
            "risk_register",
            "missing_items_list",
        ],
        "required_outputs": [
            f"{pack_root}/artifact_manifest.json",
            f"{pack_root}/missing_items.md",
            f"{pack_root}/verification_receipt.json",
            receipt_path,
        ],
        "verification_required": ["open", "render", "parse", "manifest", "missing_items", "plugin_receipt"],
        "approval_boundary": "No approval card may be created until codex_task_runner verifies the completed pack.",
        "external_actions_executed": False,
    }
    packet["input_fingerprint"] = hashlib.sha256(
        json.dumps(packet, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return packet


def build_export_quote_pack_task(case_id: str, input_artifacts: list[str]) -> dict[str, Any]:
    """Build a bounded internal EXPORT quote-pack packet for Codex."""
    pack_root = f"outputs/export_quote_packs/{case_id}"
    receipt_path = f"receipts/plugin_runs/{case_id}_export_quote_pack.json"
    packet = {
        "schema_version": "codex_export_quote_pack_task.v1",
        "task_type": "EXPORT_QUOTE_PACK",
        "case_id": case_id,
        "workflow_type": "EXPORT",
        "task": "Build an internal draft export quote pack only; do not send, contact, quote externally, accept an order, ship, invoice, pay, or make final price, classification, origin, or delivery commitments.",
        "input_artifacts": input_artifacts,
        "output_root": pack_root,
        "required_artifact_kinds": [
            "proforma_invoice_draft", "product_specification", "supplier_summary", "pricing_waterfall",
            "compliance_caveats", "incoterm_payment_proposal", "validity_delivery_assumptions", "missing_items_list",
        ],
        "required_outputs": [
            f"{pack_root}/artifact_manifest.json", f"{pack_root}/missing_items.md", f"{pack_root}/verification_receipt.json", receipt_path,
        ],
        "verification_required": ["open", "render", "parse", "commercial_readiness", "manifest", "missing_items", "plugin_receipt"],
        "approval_boundary": "No export quotation approval card may be created until codex_task_runner verifies the completed pack.",
        "external_actions_executed": False,
        "final_claims_approved": False,
    }
    packet["input_fingerprint"] = hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Create fallback Codex task")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--bid-pack", action="store_true", help="Create the governed GOV bid-pack task packet")
    parser.add_argument("--export-quote-pack", action="store_true", help="Create the governed EXPORT quote-pack task packet")
    parser.add_argument("--input-artifact", action="append", default=[], help="Input artifact path for --bid-pack; may be repeated")
    parser.add_argument("--reason", default="Codex App-Server Runtime unavailable or not selected.")
    args = parser.parse_args()

    if sum(bool(value) for value in (args.bid_pack, args.export_quote_pack)) > 1:
        parser.error("Choose only one governed pack type.")
    if not args.bid_pack and not args.export_quote_pack and not args.task:
        parser.error("Provide --task, --bid-pack, or --export-quote-pack.")
    timestamp = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    path = INBOX / f"{timestamp}_{args.case_id}.json"
    INBOX.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "case_id": args.case_id,
        "task": args.task or "Build governed internal Codex pack.",
        "reason": args.reason,
        "approval_boundary": "No external, financial, legal, DSC, final quote, HSN/ITC-HS, origin, or delivery commitment action.",
        "status": "PENDING_CODEX_FALLBACK",
    }
    if args.bid_pack:
        payload.update(build_gov_bid_pack_task(args.case_id, args.input_artifact))
        payload["status"] = "PENDING_CODEX_BID_PACK"
    if args.export_quote_pack:
        payload.update(build_export_quote_pack_task(args.case_id, args.input_artifact))
        payload["status"] = "PENDING_CODEX_EXPORT_QUOTE_PACK"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
