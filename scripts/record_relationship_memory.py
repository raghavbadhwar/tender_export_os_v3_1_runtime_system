#!/usr/bin/env python3
"""Record compact, verified buyer-relationship memory without retaining raw communications."""

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

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event


DATA_DIR = PROJECT_ROOT / "data"
REGISTER_PATH = DATA_DIR / "relationship_memory.csv"
CASES_PATH = DATA_DIR / "master_cases.csv"
COMMUNICATIONS_PATH = DATA_DIR / "communication_log.csv"
POLICY_PATH = PROJECT_ROOT / "config" / "relationship_memory_policy.yaml"
RECEIPTS_DIR = PROJECT_ROOT / "receipts" / "relationship_memory"
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .()\-]{6,}\d)(?!\d)")
RAW_MARKERS = ("from:", "to:", "subject:", "body:", "raw email", "full thread", "message body")
FORBIDDEN_RECEIPT_KEYS = {"body", "body_text", "snippet", "raw", "raw_message", "message_content", "contact_list", "email_address", "phone"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"relationship memory policy must be an object: {path}")
    return value


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))


def stable_id(buyer_id: str, case_id: str, memory_type: str, summary: str, evidence_sha256: str) -> str:
    source = "|".join((buyer_id, case_id, memory_type, summary, evidence_sha256))
    return "REL-" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:16].upper()


def parse_json_receipt(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"evidence_receipt_path must be readable JSON metadata: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("evidence receipt must be a JSON object")
    keys = {str(key).casefold() for key in value}
    forbidden = sorted(keys & FORBIDDEN_RECEIPT_KEYS)
    if forbidden:
        raise ValueError("evidence receipt contains prohibited raw/private content keys: " + ", ".join(forbidden))
    return value


def validate_evidence_receipt(path_value: str, expected_sha256: str, policy: dict[str, Any]) -> dict[str, str]:
    candidate = Path(path_value).expanduser()
    path = candidate.resolve() if candidate.is_absolute() else (PROJECT_ROOT / candidate).resolve()
    try:
        path.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("evidence receipt must remain within the Tender Export OS workspace") from exc
    suffixes = {str(item).casefold() for item in policy.get("allowed_evidence_reference_extensions", [])}
    if path.suffix.casefold() not in suffixes:
        raise ValueError("evidence_receipt_path must reference an allowed metadata-only receipt type")
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError(f"evidence_receipt_path is missing or empty: {path}")
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if expected_sha256 and expected_sha256.casefold() != digest:
        raise ValueError("evidence_sha256 does not match evidence_receipt_path")
    parse_json_receipt(path)
    return {"path": relative(path), "sha256": digest}


def validate_summary(value: str, *, label: str, policy: dict[str, Any]) -> str:
    text = clean(value)
    if not text:
        raise ValueError(f"{label} is required")
    if "\n" in text or "\r" in text:
        raise ValueError(f"{label} must be a single-line compact operating fact")
    max_characters = int((policy.get("summary_rules") or {}).get("max_characters") or 500)
    if len(text) > max_characters:
        raise ValueError(f"{label} exceeds the {max_characters}-character privacy limit")
    if EMAIL_RE.search(text) or PHONE_RE.search(text):
        raise ValueError(f"{label} must not contain direct contact identifiers")
    lowered = text.casefold()
    if any(marker in lowered for marker in RAW_MARKERS):
        raise ValueError(f"{label} appears to contain raw communication content")
    return text


def validate_memory(
    value: dict[str, Any],
    *,
    cases: list[dict[str, str]],
    communications: list[dict[str, str]],
    existing: list[dict[str, str]],
) -> dict[str, Any]:
    policy = load_policy()
    required = ("memory_id", "buyer_id", "memory_type", "summary", "evidence_receipt_path", "evidence_sha256", "verification_status", "status", "recorded_by", "recorded_at")
    missing = [field for field in required if not clean(value.get(field))]
    if missing:
        raise ValueError("required relationship-memory fields are blank: " + ", ".join(missing))
    memory_type = clean(value["memory_type"])
    if memory_type not in set(policy.get("allowed_memory_types") or []):
        raise ValueError("memory_type is not allowed by relationship-memory policy")
    if clean(value["verification_status"]) != clean(policy.get("required_verification_status")):
        raise ValueError("relationship memory may be retained only after VERIFIED evidence")
    status = clean(value["status"])
    if status not in {"ACTIVE", "SUPERSEDED", "EXPIRED"}:
        raise ValueError("relationship memory status is not allowed")
    if memory_type == "OPT_OUT" and status != "ACTIVE":
        raise ValueError("verified OPT_OUT memory must remain ACTIVE until a verified superseding correction")
    summary = validate_summary(clean(value["summary"]), label="summary", policy=policy)
    notes = clean(value.get("notes"))
    if notes:
        validate_summary(notes, label="notes", policy=policy)
    evidence = validate_evidence_receipt(clean(value["evidence_receipt_path"]), clean(value["evidence_sha256"]), policy)
    case_id = clean(value.get("case_id"))
    if case_id:
        case = next((row for row in cases if clean(row.get("case_id")) == case_id), None)
        if case is None or clean(case.get("workflow_type")).upper() != "EXPORT":
            raise ValueError("case_id must reference an existing EXPORT case")
    communication_id = clean(value.get("source_communication_id"))
    if communication_id and not any(clean(row.get("communication_id")) == communication_id for row in communications):
        raise ValueError("source_communication_id does not exist in communication_log.csv")
    supersedes = clean(value.get("supersedes_memory_id"))
    if supersedes and not any(clean(row.get("memory_id")) == supersedes for row in existing):
        raise ValueError("supersedes_memory_id does not exist")
    if supersedes == clean(value["memory_id"]):
        raise ValueError("relationship memory cannot supersede itself")
    return {"policy": policy, "summary": summary, "notes": notes, "evidence": evidence}


def write_register(path: Path, value: dict[str, Any]) -> bool:
    fields, rows = load_csv(path)
    if not fields:
        raise ValueError(f"relationship-memory register missing: {path}")
    normalized = {field: clean(value.get(field)) for field in fields}
    created = True
    for index, row in enumerate(rows):
        if clean(row.get("memory_id")) == normalized["memory_id"]:
            if any(clean(row.get(field)) != normalized[field] for field in fields):
                raise ValueError("memory_id collision with different content")
            created = False
            break
    if created:
        rows.append(normalized)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    return created


def write_receipt(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def record_memory(
    value: dict[str, Any],
    *,
    register_path: Path = REGISTER_PATH,
    cases_path: Path = CASES_PATH,
    communications_path: Path = COMMUNICATIONS_PATH,
    events_path: Path = PROJECT_ROOT / "data" / "events.jsonl",
    receipts_dir: Path = RECEIPTS_DIR,
    actor: str,
) -> dict[str, Any]:
    _, existing = load_csv(register_path)
    _, cases = load_csv(cases_path)
    _, communications = load_csv(communications_path)
    validation = validate_memory(value, cases=cases, communications=communications, existing=existing)
    receipt_path = receipts_dir / f"{value['memory_id']}.json"
    created = write_register(register_path, value)
    receipt = {
        "schema_version": "relationship_memory_receipt.v1",
        "memory_id": value["memory_id"], "buyer_id": value["buyer_id"], "case_id": value.get("case_id", ""),
        "memory_type": value["memory_type"], "summary": validation["summary"], "verification_status": "VERIFIED",
        "status": value["status"], "evidence_receipt_path": validation["evidence"]["path"], "evidence_sha256": validation["evidence"]["sha256"],
        "source_communication_id": value.get("source_communication_id", ""), "external_actions_executed": False,
        "privacy_note": "Metadata-only relationship memory; no raw message content or direct contact identifier was retained.",
    }
    write_receipt(receipt_path, receipt)
    event = append_event(
        "relationship_memory.recorded", actor, case_id=clean(value.get("case_id")), object_type="relationship_memory", object_id=clean(value["memory_id"]),
        source="relationship_memory_policy", payload={"memory_id": clean(value["memory_id"]), "memory_type": clean(value["memory_type"]), "verification_status": "VERIFIED", "status": clean(value["status"]), "receipt_path": relative(receipt_path)},
        citations=[validation["evidence"]["path"], relative(receipt_path)],
        idempotency_key=f"relationship-memory:{value['memory_id']}", events_file=events_path,
    )
    return {"created": created, "receipt_path": str(receipt_path), "event_id": event["event_id"], "external_actions_executed": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--buyer-id", required=True)
    parser.add_argument("--memory-type", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--evidence-receipt", required=True)
    parser.add_argument("--evidence-sha256", default="")
    parser.add_argument("--recorded-by", required=True)
    parser.add_argument("--case-id", default="")
    parser.add_argument("--source-communication-id", default="")
    parser.add_argument("--status", default="ACTIVE")
    parser.add_argument("--review-after", default="")
    parser.add_argument("--supersedes-memory-id", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--memory-id", default="")
    parser.add_argument("--recorded-at", default="")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    policy = load_policy()
    evidence = validate_evidence_receipt(args.evidence_receipt, args.evidence_sha256, policy)
    summary = validate_summary(args.summary, label="summary", policy=policy)
    value = {
        "memory_id": args.memory_id or stable_id(args.buyer_id, args.case_id, args.memory_type, summary, evidence["sha256"]),
        "buyer_id": args.buyer_id, "case_id": args.case_id, "memory_type": args.memory_type, "summary": summary,
        "evidence_receipt_path": evidence["path"], "evidence_sha256": evidence["sha256"], "verification_status": "VERIFIED",
        "source_communication_id": args.source_communication_id, "status": args.status, "recorded_by": args.recorded_by,
        "recorded_at": args.recorded_at or now_iso(), "review_after": args.review_after,
        "supersedes_memory_id": args.supersedes_memory_id, "notes": args.notes,
    }
    _, existing = load_csv(REGISTER_PATH)
    _, cases = load_csv(CASES_PATH)
    _, communications = load_csv(COMMUNICATIONS_PATH)
    validation = validate_memory(value, cases=cases, communications=communications, existing=existing)
    payload: dict[str, Any] = {"status": "PASS", "mode": "write" if args.write else "dry_run", "memory": value, "evidence": validation["evidence"], "external_actions_executed": False}
    if args.write:
        payload.update(record_memory(value, actor=args.recorded_by))
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
