#!/usr/bin/env python3
"""Validate and record evidence-backed case outcomes; dry-run by default."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event, build_event


CASES_PATH = PROJECT_ROOT / "data" / "master_cases.csv"
OUTCOMES_PATH = PROJECT_ROOT / "data" / "case_outcomes.csv"
EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"
SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "case_outcomes.schema.json"
COLUMNS = [
    "outcome_id",
    "case_id",
    "workflow_type",
    "outcome_type",
    "outcome_value",
    "occurred_at",
    "evidence_path",
    "evidence_sha256",
    "verification_status",
    "recorded_by",
    "recorded_at",
    "supersedes_outcome_id",
    "notes",
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_timestamp(value: str, field: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def validate_evidence(path: Path | str, expected_sha256: str = "") -> dict[str, Any]:
    evidence = Path(path).expanduser()
    if not evidence.is_absolute():
        evidence = PROJECT_ROOT / evidence
    if not evidence.is_file():
        raise ValueError(f"evidence_path does not exist: {evidence}")
    if evidence.stat().st_size <= 0:
        raise ValueError(f"evidence_path is empty: {evidence}")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    if expected_sha256 and digest.lower() != expected_sha256.lower():
        raise ValueError(f"evidence_sha256 mismatch for {evidence}")
    return {"path": str(evidence), "sha256": digest, "size_bytes": evidence.stat().st_size}


def _contract() -> tuple[set[str], set[str]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return set(schema["enums"]["outcome_type"]), set(schema["enums"]["verification_status"])


def validate_outcome(
    outcome: dict[str, Any],
    *,
    cases: list[dict[str, Any]],
    existing: list[dict[str, Any]],
) -> dict[str, Any]:
    missing = [field for field in COLUMNS[:11] if not str(outcome.get(field) or "").strip()]
    if missing:
        raise ValueError(f"required outcome fields are blank: {', '.join(missing)}")
    case_id = str(outcome.get("case_id") or "")
    case = next((row for row in cases if str(row.get("case_id") or "") == case_id), None)
    if case is None:
        raise ValueError(f"unknown case_id: {case_id}")
    workflow = str(outcome.get("workflow_type") or "").upper()
    if workflow not in {"GOV", "EXPORT"} or workflow != str(case.get("workflow_type") or "").upper():
        raise ValueError("workflow_type does not match the canonical case")
    allowed_outcomes, allowed_verification = _contract()
    if outcome.get("outcome_type") not in allowed_outcomes:
        raise ValueError(f"outcome_type is not allowed: {outcome.get('outcome_type')!r}")
    if outcome.get("verification_status") not in allowed_verification:
        raise ValueError(f"verification_status is not explicit or allowed: {outcome.get('verification_status')!r}")
    occurred = _parse_timestamp(str(outcome.get("occurred_at") or ""), "occurred_at")
    recorded = _parse_timestamp(str(outcome.get("recorded_at") or ""), "recorded_at")
    if occurred > recorded:
        raise ValueError("occurred_at cannot be after recorded_at")
    evidence = validate_evidence(str(outcome.get("evidence_path") or ""), str(outcome.get("evidence_sha256") or ""))
    outcome_id = str(outcome.get("outcome_id") or "")
    collision = next((row for row in existing if row.get("outcome_id") == outcome_id), None)
    if collision and any(str(collision.get(field) or "") != str(outcome.get(field) or "") for field in COLUMNS):
        raise ValueError(f"outcome_id collision with different content: {outcome_id}")
    supersedes = str(outcome.get("supersedes_outcome_id") or "")
    if supersedes:
        prior_ids = {str(row.get("outcome_id") or "") for row in existing}
        if supersedes not in prior_ids:
            raise ValueError(f"supersedes_outcome_id does not exist: {supersedes}")
        if supersedes == outcome_id:
            raise ValueError("an outcome cannot supersede itself")
    return {
        "ok": True,
        "case_id": case_id,
        "outcome_id": outcome_id,
        "evidence": evidence,
        "occurred_at_utc": occurred.isoformat(),
        "recorded_at_utc": recorded.isoformat(),
        "duplicate": collision is not None,
    }


def build_outcome_event(outcome: dict[str, Any], *, actor: str) -> dict[str, Any]:
    return build_event(
        "case.outcome_recorded",
        actor,
        case_id=str(outcome.get("case_id") or ""),
        object_type="case_outcome",
        object_id=str(outcome.get("outcome_id") or ""),
        source="verified_business_outcome",
        payload={"row": {column: str(outcome.get(column) or "") for column in COLUMNS}},
        citations=[str(outcome.get("evidence_path") or "")],
        idempotency_key=f"case-outcome:{outcome.get('outcome_id')}",
    )


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: str(row.get(column) or "") for column in COLUMNS})
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def append_outcome(
    outcome: dict[str, Any],
    *,
    outcomes_path: Path = OUTCOMES_PATH,
    events_path: Path = EVENTS_PATH,
    actor: str,
) -> dict[str, Any]:
    existing = load_csv(outcomes_path)
    collision = next((row for row in existing if row.get("outcome_id") == outcome.get("outcome_id")), None)
    normalized = {column: str(outcome.get(column) or "") for column in COLUMNS}
    if collision and any(str(collision.get(column) or "") != normalized[column] for column in COLUMNS):
        raise ValueError(f"outcome_id collision with different content: {outcome.get('outcome_id')}")
    event = append_event(
        "case.outcome_recorded",
        actor,
        case_id=normalized["case_id"],
        object_type="case_outcome",
        object_id=normalized["outcome_id"],
        source="verified_business_outcome",
        payload={"row": normalized},
        citations=[normalized["evidence_path"]],
        idempotency_key=f"case-outcome:{normalized['outcome_id']}",
        events_file=events_path,
    )
    if collision is None:
        _write_rows(outcomes_path, existing + [normalized])
    return event


def supersede_outcome(existing: dict[str, Any], replacement: dict[str, Any]) -> dict[str, Any]:
    existing_id = str(existing.get("outcome_id") or "")
    replacement_id = str(replacement.get("outcome_id") or "")
    if not existing_id or not replacement_id:
        raise ValueError("both existing and replacement outcome_id are required")
    if existing_id == replacement_id:
        raise ValueError("replacement outcome_id must differ from the superseded outcome")
    value = dict(replacement)
    value["supersedes_outcome_id"] = existing_id
    return value


def _slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--outcome-type", required=True)
    parser.add_argument("--outcome-value", default="")
    parser.add_argument("--occurred-at", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--evidence-sha256", default="")
    parser.add_argument("--verification-status", required=True)
    parser.add_argument("--recorded-by", required=True)
    parser.add_argument("--outcome-id")
    parser.add_argument("--supersedes-outcome-id", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    cases = load_csv(CASES_PATH)
    case = next((row for row in cases if row.get("case_id") == args.case_id), None)
    if case is None:
        raise SystemExit(f"unknown case_id: {args.case_id}")
    proof = validate_evidence(args.evidence, args.evidence_sha256)
    recorded_at = now_iso()
    outcome_id = args.outcome_id or (
        f"OUT-{_slug(args.case_id)}-{_slug(args.outcome_type)}-"
        f"{hashlib.sha256((args.occurred_at + proof['sha256']).encode()).hexdigest()[:10]}"
    )
    row = {
        "outcome_id": outcome_id,
        "case_id": args.case_id,
        "workflow_type": case.get("workflow_type", ""),
        "outcome_type": args.outcome_type,
        "outcome_value": args.outcome_value,
        "occurred_at": args.occurred_at,
        "evidence_path": proof["path"],
        "evidence_sha256": proof["sha256"],
        "verification_status": args.verification_status,
        "recorded_by": args.recorded_by,
        "recorded_at": recorded_at,
        "supersedes_outcome_id": args.supersedes_outcome_id,
        "notes": args.notes,
    }
    validation = validate_outcome(row, cases=cases, existing=load_csv(OUTCOMES_PATH))
    event = build_outcome_event(row, actor=args.recorded_by)
    report: dict[str, Any] = {
        "status": "PASS",
        "mode": "write" if args.write else "dry_run",
        "outcome": row,
        "validation": validation,
        "event_preview": event,
        "canonical_event_appended": False,
        "projection_updated": False,
        "external_actions_executed": False,
    }
    if args.write:
        written = append_outcome(row, actor=args.recorded_by)
        report.update(
            {
                "event_id": written["event_id"],
                "canonical_event_appended": True,
                "projection_updated": True,
            }
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
