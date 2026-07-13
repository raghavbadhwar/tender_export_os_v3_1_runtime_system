#!/usr/bin/env python3
"""Inspect fallback Codex tasks and verify completed internal GOV bid packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.codex_bid_pack_contract import verify_bid_pack, write_verification_receipt
    from scripts.codex_export_quote_pack_contract import verify_export_quote_pack as verify_export_quote_pack_contract, write_verification_receipt as write_export_quote_receipt
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from codex_bid_pack_contract import verify_bid_pack, write_verification_receipt  # type: ignore
    from codex_export_quote_pack_contract import verify_export_quote_pack as verify_export_quote_pack_contract, write_verification_receipt as write_export_quote_receipt  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INBOX = PROJECT_ROOT / "runtime" / "codex_inbox"


def resolve_project_path(value: str) -> Path:
    candidate = Path(value).expanduser()
    path = candidate.resolve() if candidate.is_absolute() else (PROJECT_ROOT / candidate).resolve()
    try:
        path.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"Path escapes project root: {value}") from exc
    return path


def list_inbox_tasks() -> int:
    INBOX.mkdir(parents=True, exist_ok=True)
    tasks = sorted(INBOX.glob("*.json"))
    if not tasks:
        print("No fallback Codex tasks found.")
        return 0
    for path in tasks:
        payload = json.loads(path.read_text(encoding="utf-8"))
        print(f"{path.name}: {payload.get('case_id')} | {payload.get('status')} | {payload.get('task')}")
    print("Use Codex App-Server Runtime when available. This runner intentionally does not execute external actions.")
    return 0


def verify_gov_bid_pack(args: argparse.Namespace) -> int:
    if not args.case_id:
        raise ValueError("--case-id is required with --verify-bid-pack")
    pack_dir = resolve_project_path(args.pack_dir or f"outputs/bid_packs/{args.case_id}")
    manifest = resolve_project_path(args.manifest) if args.manifest else pack_dir / "artifact_manifest.json"
    report = verify_bid_pack(manifest, expected_case_id=args.case_id)
    receipt_path = resolve_project_path(args.receipt) if args.receipt else pack_dir / "verification_receipt.json"
    if args.write_receipt:
        event_result = write_verification_receipt(
            report,
            output_path=receipt_path,
            events_path=resolve_project_path(args.events),
        )
        report["verification_receipt_path"] = event_result["receipt_path"]
        report["verification_event_id"] = event_result["event_id"]
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.json:
        print(payload)
    else:
        print(f"GOV bid-pack verification for {args.case_id}: {report['status']}")
        for error in report.get("errors", []):
            print(f"  ERROR: {error}")
        if args.write_receipt:
            print(f"  Receipt: {receipt_path}")
    return 0 if report["status"] == "PASS" else 1


def verify_export_quote_pack(args: argparse.Namespace) -> int:
    if not args.case_id:
        raise ValueError("--case-id is required with --verify-export-quote-pack")
    pack_dir = resolve_project_path(args.pack_dir or f"outputs/export_quote_packs/{args.case_id}")
    manifest = resolve_project_path(args.manifest) if args.manifest else pack_dir / "artifact_manifest.json"
    report = verify_export_quote_pack_contract(manifest, expected_case_id=args.case_id)
    receipt_path = resolve_project_path(args.receipt) if args.receipt else pack_dir / "verification_receipt.json"
    if args.write_receipt:
        event_result = write_export_quote_receipt(report, output_path=receipt_path, events_path=resolve_project_path(args.events))
        report["verification_receipt_path"] = event_result["receipt_path"]
        report["verification_event_id"] = event_result["event_id"]
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"EXPORT quote-pack verification for {args.case_id}: {report['status']}")
        for error in report.get("errors", []):
            print(f"  ERROR: {error}")
        if args.write_receipt:
            print(f"  Receipt: {receipt_path}")
    return 0 if report["status"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-bid-pack", action="store_true", help="Verify a completed internal GOV bid pack")
    parser.add_argument("--verify-export-quote-pack", action="store_true", help="Verify a completed internal EXPORT quote pack")
    parser.add_argument("--case-id", default="")
    parser.add_argument("--pack-dir", default="")
    parser.add_argument("--manifest", default="")
    parser.add_argument("--receipt", default="")
    parser.add_argument("--events", default="data/events.jsonl")
    parser.add_argument("--write-receipt", action="store_true", help="Persist the verification receipt and canonical audit event")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.verify_bid_pack and args.verify_export_quote_pack:
        parser.error("Choose only one pack verification type.")
    if args.verify_bid_pack:
        try:
            return verify_gov_bid_pack(args)
        except ValueError as exc:
            parser.error(str(exc))
    if args.verify_export_quote_pack:
        try:
            return verify_export_quote_pack(args)
        except ValueError as exc:
            parser.error(str(exc))
    return list_inbox_tasks()


if __name__ == "__main__":
    raise SystemExit(main())
