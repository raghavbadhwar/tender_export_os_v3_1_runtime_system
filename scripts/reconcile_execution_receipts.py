#!/usr/bin/env python3
"""Ingest bounded local execution receipts into the canonical event ledger.

This is an internal evidence reconciliation tool. It never sends, re-sends, or
otherwise performs an external action; it records already-existing receipts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

try:
    from event_ledger import append_event, relative
except ModuleNotFoundError:  # pragma: no cover - package import path used by pytest
    from scripts.event_ledger import append_event, relative

try:
    from execution_receipt_status import EXECUTED_VERIFIED, SAFETY_HELD_NOT_SENT
except ModuleNotFoundError:  # pragma: no cover - package import path used by pytest
    from scripts.execution_receipt_status import EXECUTED_VERIFIED, SAFETY_HELD_NOT_SENT


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APPROVALS_PATH = PROJECT_ROOT / "data" / "approvals_receipts.csv"
EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"
RECEIPTS_DIR = PROJECT_ROOT / "receipts" / "executions"
APPROVED_OUTBOX_ROOT = PROJECT_ROOT / "outputs" / "approved_execution_outbox"
ALLOWED_RECEIPT_ROOTS = (RECEIPTS_DIR.resolve(), APPROVED_OUTBOX_ROOT.resolve())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_approvals(path: Path = APPROVALS_PATH) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return {str(row.get("approval_id", "")).strip(): row for row in csv.DictReader(handle)}


def relative_to_root(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError as exc:
        raise ValueError(f"receipt must be inside the project root: {path}") from exc


def require_allowed_receipt_path(path: Path, allowed_roots: tuple[Path, ...] = ALLOWED_RECEIPT_ROOTS) -> None:
    """Reject staged JSON outside the two governed execution-receipt stores."""
    resolved = path.resolve()
    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return
        except ValueError:
            continue
    roots = ", ".join(str(root) for root in allowed_roots)
    raise ValueError(f"receipt must be under an approved execution-receipt store ({roots}): {path}")


def parse_receipt(
    path: Path,
    approvals: dict[str, dict[str, str]],
    *,
    allowed_roots: tuple[Path, ...] = ALLOWED_RECEIPT_ROOTS,
) -> dict[str, Any]:
    path = path.resolve()
    require_allowed_receipt_path(path, allowed_roots)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON execution receipt: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"execution receipt must be an object: {path}")
    receipt_id = str(payload.get("receipt_id", "")).strip()
    approval_id = str(payload.get("approval_id", "")).strip()
    case_id = str(payload.get("case_id", "")).strip()
    if not receipt_id or not approval_id or not case_id:
        raise ValueError(f"receipt_id, approval_id, and case_id are required: {path}")
    approval = approvals.get(approval_id)
    if approval is None or str(approval.get("case_id", "")).strip() != case_id:
        raise ValueError(f"receipt scope does not match the approval register: {path}")

    gmail_status = str((payload.get("gmail_result") or {}).get("status", "")).strip().lower()
    declared_external_action = payload.get("external_action_sent")
    if gmail_status == "sent":
        if declared_external_action is not None and declared_external_action is not True:
            raise ValueError(f"sent receipt contradicts external_action_sent metadata: {path}")
        execution_status = EXECUTED_VERIFIED
        external_action_sent = True
    elif (
        str(payload.get("execution_result", "")).strip() == SAFETY_HELD_NOT_SENT
        and payload.get("external_action_sent") is False
    ):
        execution_status = SAFETY_HELD_NOT_SENT
        external_action_sent = False
    else:
        raise ValueError(f"unsupported or unverified execution receipt state: {path}")

    return {
        "receipt_id": receipt_id,
        "approval_id": approval_id,
        "case_id": case_id,
        "receipt_path": relative_to_root(path),
        "evidence_sha256": sha256(path),
        "execution_status": execution_status,
        "external_action_sent": external_action_sent,
    }


def reconciliation_id(receipts: list[dict[str, Any]]) -> str:
    canonical = json.dumps(receipts, sort_keys=True, separators=(",", ":"))
    return f"RECON-EXECUTION-{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:16].upper()}"


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def reconcile(receipt_paths: list[Path], *, write: bool) -> dict[str, Any]:
    approvals = load_approvals()
    receipts = sorted((parse_receipt(path.resolve(), approvals) for path in receipt_paths), key=lambda item: item["receipt_id"])
    identifiers = [item["receipt_id"] for item in receipts]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate receipt_id supplied")
    reconcile_id = reconciliation_id(receipts)
    reconciliation_path = RECEIPTS_DIR / f"{reconcile_id}.json"
    report = {
        "schema_version": "execution_receipt_reconciliation.v1",
        "reconciliation_id": reconcile_id,
        "status": "PASS",
        "receipt_count": len(receipts),
        "receipts": receipts,
        "external_actions_executed": False,
        "safety_note": "Internal evidence ingestion only. No message, follow-up, submission, payment, DSC, price, delivery, classification, origin, or other external action was executed.",
    }
    event_ids: list[str] = []
    if write:
        write_json_atomic(reconciliation_path, report)
        reconciliation_relative = relative(reconciliation_path)
        for receipt in receipts:
            event = append_event(
                "execution.receipt_ingested",
                "execution_receipt_reconciler",
                case_id=receipt["case_id"],
                object_type="execution",
                object_id=receipt["receipt_id"],
                source="local_execution_receipt_reconciliation",
                payload={
                    **receipt,
                    "verification_status": "VERIFIED",
                    "reconciliation_receipt_path": reconciliation_relative,
                },
                citations=[receipt["receipt_path"], reconciliation_relative],
                correlation_id=reconcile_id,
                idempotency_key=f"execution-receipt-ingested:{receipt['receipt_id']}:{receipt['evidence_sha256']}",
                events_file=EVENTS_PATH,
            )
            event_ids.append(str(event["event_id"]))
    return {
        "status": "PASS",
        "mode": "write" if write else "dry_run",
        "reconciliation_id": reconcile_id,
        "reconciliation_receipt_path": relative(reconciliation_path),
        "receipt_count": len(receipts),
        "receipts": receipts,
        "event_ids": event_ids,
        "external_actions_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", action="append", required=True, help="Existing execution receipt path; repeat for each receipt")
    parser.add_argument("--write", action="store_true", help="Write reconciliation receipt and append canonical evidence events")
    args = parser.parse_args()
    paths = [Path(value) if Path(value).is_absolute() else PROJECT_ROOT / value for value in args.receipt]
    print(json.dumps(reconcile(paths, write=args.write), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
