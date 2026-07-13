#!/usr/bin/env python3
"""Record an owner-approved, manually observed Computer Use read-only canary.

This utility never opens a browser, logs in, or invokes Computer Use.  It only
records evidence after an owner has manually observed the bounded canary.  A
receipt is deliberately impossible to create without a matching, case-scoped
approval record and local evidence file.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event  # noqa: E402


CASES_PATH = PROJECT_ROOT / "data" / "master_cases.csv"
APPROVALS_PATH = PROJECT_ROOT / "data" / "approvals_receipts.csv"
RUN_LOG_PATH = PROJECT_ROOT / "data" / "agent_run_log.csv"
CONFIG_PATH = PROJECT_ROOT / "config" / "computer_use_portal_assist.yaml"
RECEIPTS_DIR = PROJECT_ROOT / "receipts" / "computer_use_canaries"
REQUIRED_APPROVAL_ACTION = "computer_use_read_only_canary"
CANARY_ACTION = "PUBLIC_PAGE_OBSERVATION"


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def as_project_path(value: str, *, project_root: Path = PROJECT_ROOT) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else project_root / path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_timestamp(value: str, *, field: str) -> str:
    text = clean_text(value)
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.replace(microsecond=0).isoformat()


def approval_errors(
    approvals: list[dict[str, str]],
    *,
    case_id: str,
    approval_reference: str,
    observed_at: str,
    required_action: str = REQUIRED_APPROVAL_ACTION,
) -> list[str]:
    matching = [row for row in approvals if clean_text(row.get("approval_id")) == approval_reference]
    if not matching:
        return [f"approval reference {approval_reference!r} was not found"]
    approval = matching[0]
    errors: list[str] = []
    if clean_text(approval.get("case_id")) != case_id:
        errors.append("approval reference is not scoped to this case")
    if clean_text(approval.get("approval_status")).upper() != "APPROVED":
        errors.append("approval reference is not APPROVED")
    if clean_text(approval.get("action_approved")) != required_action:
        errors.append(f"approval action must be {required_action}")
    expires_at = clean_text(approval.get("approval_timeout_at"))
    if expires_at:
        try:
            expiry = dt.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            observed = dt.datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                errors.append("approval timeout must include a timezone")
            elif observed > expiry:
                errors.append("approval reference expired before the canary was observed")
        except ValueError:
            errors.append("approval timeout is not ISO-8601")
    return errors


def validate_canary(
    *,
    case_id: str,
    approval_reference: str,
    observed_by: str,
    observed_at: str,
    evidence_path: Path,
    cases: list[dict[str, str]],
    approvals: list[dict[str, str]],
    required_action: str = REQUIRED_APPROVAL_ACTION,
) -> dict[str, Any]:
    errors: list[str] = []
    normalized_case_id = clean_text(case_id)
    normalized_approval = clean_text(approval_reference)
    normalized_observer = clean_text(observed_by)
    if not normalized_case_id:
        errors.append("case_id is required")
    elif not any(clean_text(row.get("case_id")) == normalized_case_id for row in cases):
        errors.append("case_id was not found in master_cases.csv")
    if not normalized_approval:
        errors.append("approval_reference is required")
    if not normalized_observer:
        errors.append("observed_by is required")
    try:
        normalized_observed_at = parse_timestamp(observed_at, field="observed_at")
    except ValueError as exc:
        normalized_observed_at = ""
        errors.append(str(exc))
    if not evidence_path.is_file():
        errors.append(f"evidence file does not exist: {evidence_path}")
        evidence_sha256 = ""
    else:
        evidence_sha256 = sha256_file(evidence_path)
    if normalized_case_id and normalized_approval and normalized_observed_at:
        errors.extend(
            approval_errors(
                approvals,
                case_id=normalized_case_id,
                approval_reference=normalized_approval,
                observed_at=normalized_observed_at,
                required_action=required_action,
            )
        )
    return {
        "status": "PASS" if not errors else "BLOCKED",
        "errors": errors,
        "case_id": normalized_case_id,
        "approval_reference": normalized_approval,
        "approval_action": required_action,
        "observed_by": normalized_observer,
        "observed_at": normalized_observed_at,
        "evidence_path": str(evidence_path),
        "evidence_sha256": evidence_sha256,
    }


def canary_id(validation: dict[str, Any]) -> str:
    identity = "\x1f".join(
        [
            validation["case_id"],
            validation["approval_reference"],
            validation["evidence_sha256"],
        ]
    )
    return f"CU-CANARY-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16].upper()}"


def build_receipt(validation: dict[str, Any], *, receipt_path: Path) -> dict[str, Any]:
    identifier = canary_id(validation)
    evidence_path = Path(validation["evidence_path"])
    try:
        evidence_reference = str(evidence_path.relative_to(PROJECT_ROOT))
    except ValueError:
        evidence_reference = str(evidence_path)
    return {
        "schema_version": "computer_use_read_only_canary_receipt.v1",
        "status": "PASS",
        "canary_id": identifier,
        "case_id": validation["case_id"],
        "approval_reference": validation["approval_reference"],
        "approval_action": validation["approval_action"],
        "observed_by": validation["observed_by"],
        "observed_at": validation["observed_at"],
        "canary_action": CANARY_ACTION,
        "manual_observable_session": True,
        "login_performed": False,
        "form_submission_attempted": False,
        "file_upload_attempted": False,
        "payment_attempted": False,
        "dsc_or_esignature_attempted": False,
        "captcha_bypass_attempted": False,
        "external_actions_executed": False,
        "portal_assist_enabled": False,
        "evidence_path": evidence_reference,
        "evidence_sha256": validation["evidence_sha256"],
        "receipt_path": str(receipt_path),
        "safety_note": "Receipt only. The canary was a manual, observable public-page observation; this record does not enable portal assist or authorize submission, upload, payment, DSC, CAPTCHA bypass, or commitments.",
    }


def validate_canary_receipt(
    receipt: dict[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
    cases_path: Path = CASES_PATH,
    approvals_path: Path = APPROVALS_PATH,
) -> dict[str, Any]:
    errors: list[str] = []
    required = {
        "schema_version",
        "status",
        "canary_id",
        "case_id",
        "approval_reference",
        "approval_action",
        "observed_by",
        "observed_at",
        "canary_action",
        "manual_observable_session",
        "external_actions_executed",
        "portal_assist_enabled",
        "evidence_path",
        "evidence_sha256",
    }
    missing = sorted(field for field in required if receipt.get(field) in (None, ""))
    if missing:
        errors.append("missing receipt fields: " + ", ".join(missing))
    if receipt.get("schema_version") != "computer_use_read_only_canary_receipt.v1":
        errors.append("receipt schema_version is invalid")
    if receipt.get("status") != "PASS":
        errors.append("receipt status must be PASS")
    if receipt.get("canary_action") != CANARY_ACTION:
        errors.append(f"canary_action must be {CANARY_ACTION}")
    if receipt.get("manual_observable_session") is not True:
        errors.append("manual_observable_session must be true")
    if receipt.get("external_actions_executed") is not False:
        errors.append("external_actions_executed must be false")
    if receipt.get("portal_assist_enabled") is not False:
        errors.append("portal_assist_enabled must be false")
    for field in (
        "login_performed",
        "form_submission_attempted",
        "file_upload_attempted",
        "payment_attempted",
        "dsc_or_esignature_attempted",
        "captcha_bypass_attempted",
    ):
        if receipt.get(field) is not False:
            errors.append(f"{field} must be false")
    try:
        observed_at = parse_timestamp(clean_text(receipt.get("observed_at")), field="observed_at")
    except ValueError as exc:
        observed_at = ""
        errors.append(str(exc))
    evidence_path = as_project_path(clean_text(receipt.get("evidence_path")), project_root=project_root)
    if not evidence_path.is_file():
        errors.append(f"receipt evidence file does not exist: {evidence_path}")
    elif clean_text(receipt.get("evidence_sha256")) != sha256_file(evidence_path):
        errors.append("receipt evidence_sha256 does not match the evidence file")
    if observed_at:
        errors.extend(
            approval_errors(
                load_csv(approvals_path),
                case_id=clean_text(receipt.get("case_id")),
                approval_reference=clean_text(receipt.get("approval_reference")),
                observed_at=observed_at,
                required_action=clean_text(receipt.get("approval_action")) or REQUIRED_APPROVAL_ACTION,
            )
        )
    if not any(clean_text(row.get("case_id")) == clean_text(receipt.get("case_id")) for row in load_csv(cases_path)):
        errors.append("receipt case_id was not found in master_cases.csv")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "canary_id": clean_text(receipt.get("canary_id")),
        "case_id": clean_text(receipt.get("case_id")),
        "receipt_path": clean_text(receipt.get("receipt_path")),
    }


def append_run_log(path: Path, receipt: dict[str, Any]) -> None:
    fields = [
        "run_id", "run_date", "run_time", "agent_name", "trigger_type", "cases_processed", "cases_created",
        "cases_rejected", "cases_updated", "sources_checked", "sources_failed", "actions_taken",
        "approval_cards_created", "receipts_created", "errors", "warnings", "runtime_seconds", "status", "notes",
    ]
    existing_fields: list[str] | None = None
    if path.is_file():
        with path.open("r", newline="", encoding="utf-8") as handle:
            existing_fields = csv.DictReader(handle).fieldnames
    now = dt.datetime.now(dt.timezone.utc)
    row = {
        "run_id": f"RUN-COMPUTER-USE-CANARY-{now.strftime('%Y%m%d%H%M%S')}",
        "run_date": now.date().isoformat(),
        "run_time": now.strftime("%H:%M:%S"),
        "agent_name": "hermes_chief_operator",
        "trigger_type": "owner_observed_read_only_canary",
        "cases_processed": "1", "cases_created": "0", "cases_rejected": "0", "cases_updated": "0",
        "sources_checked": "0", "sources_failed": "0", "actions_taken": "computer_use_read_only_canary_recorded",
        "approval_cards_created": "0", "receipts_created": "1", "errors": "0", "warnings": "0",
        "runtime_seconds": "0", "status": "SUCCESS",
        "notes": f"{receipt['case_id']} read-only Computer Use canary receipt: {receipt['receipt_path']}",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=existing_fields or fields)
        if existing_fields is None:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in (existing_fields or fields)})


def record_canary(
    *,
    case_id: str,
    approval_reference: str,
    observed_by: str,
    observed_at: str,
    evidence: str,
    write: bool = False,
    cases_path: Path = CASES_PATH,
    approvals_path: Path = APPROVALS_PATH,
    receipts_dir: Path = RECEIPTS_DIR,
    events_path: Path | None = None,
    run_log_path: Path | None = None,
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    config = load_config(config_path)
    canary_contract = config.get("canary_contract") if isinstance(config.get("canary_contract"), dict) else {}
    required_action = clean_text(canary_contract.get("required_approval_action")) or REQUIRED_APPROVAL_ACTION
    validation = validate_canary(
        case_id=case_id,
        approval_reference=approval_reference,
        observed_by=observed_by,
        observed_at=observed_at,
        evidence_path=as_project_path(evidence),
        cases=load_csv(cases_path),
        approvals=load_csv(approvals_path),
        required_action=required_action,
    )
    if config.get("portal_assist_enabled") is not False:
        validation["errors"].append("portal_assist_enabled must remain false while recording a canary")
    if canary_contract.get("allowed_action") != CANARY_ACTION:
        validation["errors"].append(f"canary_contract.allowed_action must be {CANARY_ACTION}")
    for control in (
        "read_only_only",
        "public_or_owner_opened_page_only",
        "no_form_submit",
        "no_file_upload",
        "no_login_without_owner_present",
        "no_credential_storage",
        "receipt_required",
    ):
        if canary_contract.get(control) is not True:
            validation["errors"].append(f"canary_contract.{control} must be true")
    if validation["errors"]:
        validation["status"] = "BLOCKED"
    if validation["status"] != "PASS":
        return {
            "status": "BLOCKED",
            "mode": "write" if write else "dry_run",
            "validation": validation,
            "canonical_event_appended": False,
            "external_actions_executed": False,
            "portal_assist_enabled": False,
        }
    identifier = canary_id(validation)
    receipt_path = receipts_dir / f"{identifier}.json"
    receipt = build_receipt(validation, receipt_path=receipt_path)
    if not write:
        return {
            "status": "PASS",
            "mode": "dry_run",
            "receipt_preview": receipt,
            "validation": validation,
            "canonical_event_appended": False,
            "external_actions_executed": False,
            "portal_assist_enabled": False,
        }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    already_exists = receipt_path.is_file()
    if already_exists:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    else:
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    event = append_event(
        "computer_use.read_only_canary_recorded",
        "hermes_chief_operator",
        case_id=receipt["case_id"],
        object_type="computer_use_canary",
        object_id=receipt["canary_id"],
        source="owner_observed_computer_use_canary",
        payload={
            "receipt_path": str(receipt_path),
            "evidence_sha256": receipt["evidence_sha256"],
            "approval_reference": receipt["approval_reference"],
            "canary_action": receipt["canary_action"],
        },
        citations=[receipt["evidence_path"], str(receipt_path)],
        idempotency_key=f"computer-use-read-only-canary:{receipt['canary_id']}",
        events_file=events_path or PROJECT_ROOT / "data" / "events.jsonl",
    )
    if not already_exists and run_log_path is not None:
        append_run_log(run_log_path, receipt)
    return {
        "status": "PASS",
        "mode": "write",
        "receipt_path": str(receipt_path),
        "validation": validate_canary_receipt(
            receipt,
            project_root=PROJECT_ROOT,
            cases_path=cases_path,
            approvals_path=approvals_path,
        ),
        "event_id": event["event_id"],
        "canonical_event_appended": True,
        "external_actions_executed": False,
        "portal_assist_enabled": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--approval-reference", required=True)
    parser.add_argument("--observed-by", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--write", action="store_true", help="Write a receipt after the manually observed canary has already occurred.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = record_canary(
        case_id=args.case_id,
        approval_reference=args.approval_reference,
        observed_by=args.observed_by,
        observed_at=args.observed_at,
        evidence=args.evidence,
        write=args.write,
        run_log_path=RUN_LOG_PATH,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else result["status"])
    return 0 if result["status"] in {"PASS", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
