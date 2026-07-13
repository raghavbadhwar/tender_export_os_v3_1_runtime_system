#!/usr/bin/env python3
"""Apply an approved learning proposal with checkpoint and rollback gates."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
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
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    proposals_path = Path(args.learning_proposals).expanduser().resolve()
    proposals = load_csv(proposals_path)
    proposal = next((row for row in proposals if clean(row.get("proposal_id")) == args.proposal_id), None)
    if proposal is None:
        errors = [f"proposal not found: {args.proposal_id}"]
    else:
        errors = validate_application(
            proposal=proposal,
            evaluation_report=load_json(Path(args.evaluation_report).expanduser()),
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
        outputs["event_id"] = str(event["event_id"])
    payload = {"status": "PASS" if not errors else "FAIL", "errors": errors, "write_applied": bool(args.write and not errors), "outputs": outputs}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else json.dumps(payload, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
