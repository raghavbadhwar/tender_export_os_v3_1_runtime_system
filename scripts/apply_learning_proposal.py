#!/usr/bin/env python3
"""Apply an approved learning proposal with checkpoint and rollback gates."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEARNING_PROPOSALS = PROJECT_ROOT / "data" / "learning_proposals.csv"
EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"
PROPOSAL_COLUMNS = [
    "proposal_id",
    "proposal_type",
    "proposal_target",
    "evidence_event_ids",
    "affected_workflows",
    "evidence_summary",
    "current_version",
    "proposed_version",
    "fixtures",
    "evaluation_report_path",
    "rollback_artifact_path",
    "status",
    "approval_id",
    "staged_by",
    "staged_at",
    "evaluated_at",
    "applied_at",
    "notes",
]


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def upper(value: Any) -> str:
    return clean(value).upper()


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROPOSAL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in PROPOSAL_COLUMNS})


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON report must be an object")
    return value


def path_exists(path_text: str) -> bool:
    if not path_text:
        return False
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.exists()


def file_sha256(path_text: str) -> str:
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_promotion_receipt(
    *,
    proposal: dict[str, Any],
    evaluation_report_path: str,
    checkpoint_path: str,
    artifact_hash: str,
    event_id: str,
    promoted_at: str,
) -> dict[str, Any]:
    """Build an immutable, content-minimized receipt for an approved promotion."""
    if not path_exists(evaluation_report_path):
        raise ValueError("evaluation report path must exist")
    if not path_exists(checkpoint_path):
        raise ValueError("checkpoint path must exist")
    proposal_type = clean(proposal.get("proposal_type")).lower()
    proposal_type = {"source": "source_adapter", "routing": "rule", "evaluation": "test"}.get(proposal_type, proposal_type or "test")
    return {
        "schema_version": "learning_promotion_receipt.v1",
        "proposal_id": clean(proposal.get("proposal_id")),
        "proposal_type": proposal_type,
        "proposal_target": clean(proposal.get("proposal_target")),
        "proposed_version": clean(proposal.get("proposed_version")),
        "approval_id": clean(proposal.get("approval_id")),
        "evaluation_report_path": evaluation_report_path,
        "evaluation_report_sha256": file_sha256(evaluation_report_path),
        "checkpoint_path": checkpoint_path,
        "rollback_artifact_path": clean(proposal.get("rollback_artifact_path")),
        "artifact_hash": artifact_hash,
        "event_id": event_id,
        "promoted_at": promoted_at,
        "external_actions_executed": False,
        "raw_content_persisted": False,
    }


def validate_promotion_receipt(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema_version") != "learning_promotion_receipt.v1":
        errors.append("schema_version must be learning_promotion_receipt.v1")
    for field in ("proposal_id", "proposal_target", "proposed_version", "approval_id", "evaluation_report_path", "checkpoint_path", "rollback_artifact_path", "artifact_hash", "event_id", "promoted_at"):
        if not clean(receipt.get(field)):
            errors.append(f"{field} is required")
    if not path_exists(clean(receipt.get("rollback_artifact_path"))):
        errors.append("rollback artifact must exist")
    if not path_exists(clean(receipt.get("evaluation_report_path"))):
        errors.append("evaluation report must exist")
    if not path_exists(clean(receipt.get("checkpoint_path"))):
        errors.append("checkpoint must exist")
    if receipt.get("external_actions_executed") is not False:
        errors.append("external_actions_executed must be false")
    if receipt.get("raw_content_persisted") is not False:
        errors.append("raw_content_persisted must be false")
    digest = clean(receipt.get("evaluation_report_sha256"))
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.lower()):
        errors.append("evaluation_report_sha256 must be a SHA-256 digest")
    elif path_exists(clean(receipt.get("evaluation_report_path"))) and digest != file_sha256(clean(receipt.get("evaluation_report_path"))):
        errors.append("evaluation_report_sha256 does not match evaluation report")
    return errors


def validate_application(
    *,
    proposal: dict[str, Any],
    evaluation_report: dict[str, Any],
    approval_scope: str,
    target: str,
    version: str,
    artifact_hash: str,
    checkpoint_path: str,
) -> list[str]:
    errors: list[str] = []
    proposal_id = clean(proposal.get("proposal_id"))
    scope_blob = " ".join(
        clean(proposal.get(field))
        for field in ("proposal_target", "affected_workflows", "current_version", "proposed_version", "fixtures", "notes")
    )
    if upper(proposal.get("status")) != "APPROVED":
        errors.append(f"{proposal_id}.status must be APPROVED")
    if not clean(proposal.get("approval_id")):
        errors.append(f"{proposal_id}.approval_id is required")
    for required in (approval_scope, target, version, artifact_hash):
        if required and required not in scope_blob:
            errors.append(f"approval scope mismatch: {required}")
    if clean(evaluation_report.get("proposal_id")) != proposal_id:
        errors.append("evaluation_report.proposal_id mismatch")
    if upper(evaluation_report.get("evaluation_status")) != "PASS":
        errors.append("evaluation status must be PASS")
    evaluation_rows = evaluation_report.get("rows")
    if not isinstance(evaluation_rows, list) or len(evaluation_rows) != 3 or any(row.get("status") != "PASS" for row in evaluation_rows if isinstance(row, dict)):
        errors.append("evaluation must contain three passing repeated runs")
    if not isinstance(evaluation_rows, list) or any(not isinstance(row, dict) for row in evaluation_rows):
        errors.append("evaluation rows must be objects")
    rollback_path = clean(proposal.get("rollback_artifact_path"))
    if not path_exists(rollback_path):
        errors.append("rollback artifact must exist")
    if not path_exists(checkpoint_path):
        errors.append("checkpoint path must exist")
    return errors


def apply_rows(rows: list[dict[str, Any]], proposal_id: str, applied_at: str) -> list[dict[str, Any]]:
    updated = []
    for row in rows:
        new_row = dict(row)
        if clean(row.get("proposal_id")) == proposal_id:
            new_row["status"] = "APPLIED"
            new_row["applied_at"] = applied_at
        updated.append(new_row)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-id", required=True)
    parser.add_argument("--evaluation-report", required=True)
    parser.add_argument("--approval-scope", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--artifact-hash", required=True)
    parser.add_argument("--checkpoint-path", required=True)
    parser.add_argument("--learning-proposals", default=str(LEARNING_PROPOSALS))
    parser.add_argument("--events", default=str(EVENTS_PATH))
    parser.add_argument("--promotion-receipt", default="", help="Output path for the immutable promotion receipt")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    proposals_path = Path(args.learning_proposals).expanduser().resolve()
    proposals = load_csv(proposals_path)
    proposal = next((row for row in proposals if clean(row.get("proposal_id")) == args.proposal_id), None)
    evaluation_report_path = Path(args.evaluation_report).expanduser().resolve()
    evaluation_report = load_json(evaluation_report_path)
    if proposal is None:
        errors = [f"proposal not found: {args.proposal_id}"]
    else:
        errors = validate_application(
            proposal=proposal,
            evaluation_report=evaluation_report,
            approval_scope=args.approval_scope,
            target=args.target,
            version=args.version,
            artifact_hash=args.artifact_hash,
            checkpoint_path=args.checkpoint_path,
        )
    outputs: dict[str, str] = {}
    if args.write and not errors and proposal is not None:
        applied_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        write_csv(proposals_path, apply_rows(proposals, args.proposal_id, applied_at))
        event = append_event(
            "learning.promoted",
            "learning_application",
            object_type="learning_proposal",
            object_id=args.proposal_id,
            source="apply_learning_proposal",
            payload={
                "proposal_id": args.proposal_id,
                "approval_id": proposal["approval_id"],
                "rollback_artifact_path": proposal["rollback_artifact_path"],
                "checkpoint_path": args.checkpoint_path,
                "artifact_hash": args.artifact_hash,
            },
            citations=[proposal["rollback_artifact_path"], args.checkpoint_path, args.evaluation_report],
            idempotency_key=f"learning.promoted:{args.proposal_id}:{args.artifact_hash}",
            events_file=Path(args.events).expanduser().resolve(),
        )
        event_id = str(event["event_id"])
        receipt_path = Path(args.promotion_receipt or (PROJECT_ROOT / "outputs" / "learning_evaluations" / f"promotion_receipt_{args.proposal_id}.json")).expanduser().resolve()
        receipt = build_promotion_receipt(
            proposal=proposal,
            evaluation_report_path=str(evaluation_report_path),
            checkpoint_path=args.checkpoint_path,
            artifact_hash=args.artifact_hash,
            event_id=event_id,
            promoted_at=applied_at,
        )
        receipt_errors = validate_promotion_receipt(receipt)
        if receipt_errors:
            raise ValueError("promotion receipt validation failed: " + "; ".join(receipt_errors))
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        serialized_receipt = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
        if receipt_path.exists():
            if receipt_path.read_text(encoding="utf-8") != serialized_receipt:
                raise ValueError("promotion receipt path already exists with different content")
        else:
            receipt_path.write_text(serialized_receipt, encoding="utf-8")
        outputs["event_id"] = event_id
        outputs["promotion_receipt"] = str(receipt_path)
    payload = {"status": "PASS" if not errors else "FAIL", "errors": errors, "write_applied": bool(args.write and not errors), "outputs": outputs}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else json.dumps(payload, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
