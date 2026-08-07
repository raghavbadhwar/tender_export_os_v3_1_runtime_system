#!/usr/bin/env python3
"""Validate a bounded, evidence-backed export buyer account record."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "buyer_account_verification.schema.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"


def load_contract(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Buyer account verification contract must be an object: {path}")
    return value


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def evidence_digest(path_value: str, expected_sha256: str) -> dict[str, str]:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    try:
        path.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("evidence path must remain inside the project root") from exc
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError(f"public evidence file is missing or empty: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_sha256 and digest.lower() != expected_sha256.lower():
        raise ValueError("public evidence SHA-256 does not match")
    return {"path": str(path), "sha256": digest}


def parse_date(value: str) -> None:
    try:
        dt.date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ValueError("source_observed_at must be an ISO date or timestamp") from exc


def status_value(value: Any) -> str:
    return clean(value).upper()


def validate_evidence_record(record: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in contract["required_fields"]:
        if field not in record or record.get(field) in (None, ""):
            errors.append(f"missing {field}")
    if record.get("external_actions_executed") is not False:
        errors.append("external_actions_executed must be false")
    if status_value(record.get("product_category_fit")) not in set(contract["product_category_fit_values"]):
        errors.append("product_category_fit is not allowed")
    duplicate = record.get("duplicate_check") if isinstance(record.get("duplicate_check"), dict) else {}
    if status_value(duplicate.get("status")) not in set(contract["duplicate_statuses"]):
        errors.append("duplicate_check.status is not allowed")
    sanctions = record.get("sanctions_review") if isinstance(record.get("sanctions_review"), dict) else {}
    if status_value(sanctions.get("status")) not in set(contract["sanctions_statuses"]):
        errors.append("sanctions_review.status is not allowed")
    proof_gaps = record.get("proof_gaps")
    if not isinstance(proof_gaps, list) or any(not clean(item) for item in proof_gaps):
        errors.append("proof_gaps must be a list of explicit non-empty gaps")
    try:
        confidence = int(record.get("confidence_score"))
        if not 0 <= confidence <= 100:
            errors.append("confidence_score must be between 0 and 100")
    except (TypeError, ValueError):
        errors.append("confidence_score must be an integer")
    if clean(record.get("official_domain")) not in {"", "UNKNOWN"} and not clean(record.get("official_domain")).startswith("https://"):
        errors.append("official_domain must use HTTPS when known")
    try:
        parse_date(clean(record.get("source_observed_at")))
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def buyer_specific_evidence(record: dict[str, Any]) -> tuple[dict[str, str] | None, list[str]]:
    value = record.get("buyer_specific_demand_evidence")
    if value in (None, ""):
        return None, []
    if not isinstance(value, dict):
        return None, ["buyer_specific_demand_evidence must be an object"]
    demand_type = status_value(value.get("type"))
    if demand_type not in {"RFQ", "BUYER_MESSAGE"}:
        return None, ["buyer_specific_demand_evidence.type must be RFQ or BUYER_MESSAGE"]
    try:
        proof = evidence_digest(clean(value.get("path")), clean(value.get("sha256")))
    except ValueError as exc:
        return None, [str(exc)]
    return {"type": demand_type, **proof}, []


def classify_account(record: dict[str, Any], contract: dict[str, Any]) -> tuple[str, list[str], dict[str, str] | None]:
    errors = validate_evidence_record(record, contract)
    if errors:
        return "BLOCKED", errors, None
    public_evidence = evidence_digest(clean(record["public_evidence_path"]), clean(record["public_evidence_sha256"]))
    demand_evidence, demand_errors = buyer_specific_evidence(record)
    if demand_errors:
        return "BLOCKED", demand_errors, public_evidence
    gaps = [clean(item) for item in record["proof_gaps"]]
    legal_identity = clean(record["legal_entity_name"]).upper() not in {"", "UNKNOWN"}
    official_domain = clean(record["official_domain"]).upper() not in {"", "UNKNOWN"}
    contact_path = clean(record["procurement_contact_path"]).upper() not in {"", "UNKNOWN"}
    duplicate_clear = status_value(record["duplicate_check"].get("status")) == "CLEAR"
    sanctions_status = status_value(record["sanctions_review"].get("status"))
    sanctions_clear = sanctions_status in {"NOT_APPLICABLE", "CLEAR_PUBLIC_SCREEN"}
    if sanctions_status in {"HIT_OR_AMBIGUOUS", "MANUAL_REVIEW_REQUIRED"}:
        return "BLOCKED", gaps + ["sanctions or restricted-party review requires human resolution"], public_evidence
    if not (legal_identity and official_domain and duplicate_clear):
        return "CATALOGUE_HYPOTHESIS", gaps, public_evidence
    if not (contact_path and sanctions_clear):
        return "IDENTITY_VERIFIED", gaps, public_evidence
    if demand_evidence and status_value(record["product_category_fit"]) == "RFQ_MATCHED":
        return "RFQ_VERIFIED", gaps, public_evidence
    return "CONTACT_PATH_VERIFIED", gaps, public_evidence


def validate_account(record: dict[str, Any]) -> dict[str, Any]:
    contract = load_contract()
    status, errors, public_evidence = classify_account(record, contract)
    return {
        "status": "PASS" if status != "BLOCKED" else "FAIL",
        "account_status": status,
        "errors": errors,
        "public_evidence": public_evidence,
        "external_actions_executed": False,
    }


def write_account_report(
    record: dict[str, Any],
    report: dict[str, Any],
    *,
    output_path: Path,
    events_path: Path = DEFAULT_EVENTS_PATH,
    actor: str = "export_buyer_intelligence",
) -> dict[str, str]:
    if report["status"] != "PASS":
        raise ValueError("Blocked buyer account record cannot be written as verified")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    value = {
        "schema_version": "buyer_account_verification.v1",
        "record": record,
        "report": report,
        "written_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "external_actions_executed": False,
    }
    output_path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    from scripts.event_ledger import append_event

    event = append_event(
        "buyer.account_verified",
        actor,
        case_id=clean(record["case_id"]),
        object_type="buyer",
        object_id=clean(record["buyer_id"]),
        source="buyer_account_verification",
        payload={
            "report_path": str(output_path),
            "account_status": report["account_status"],
            "confidence_score": int(record["confidence_score"]),
        },
        citations=[str(output_path), clean(record["public_evidence_path"])],
        idempotency_key=(
            f"buyer-account:{record['buyer_id']}:"
            f"{report['account_status']}:{report['public_evidence']['sha256']}"
        ),
        events_file=events_path,
    )
    return {"report_path": str(output_path), "event_id": str(event["event_id"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", default="")
    parser.add_argument("--events", default=str(DEFAULT_EVENTS_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    input_path = Path(args.input).expanduser()
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    record = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise SystemExit("input must be a JSON object")
    report = validate_account(record)
    payload: dict[str, Any] = {"mode": "write" if args.write else "dry_run", **report}
    if args.write and report["status"] == "PASS":
        output = Path(args.output).expanduser() if args.output else DEFAULT_OUTPUT_ROOT / clean(record["case_id"]) / "buyer_account_verification.json"
        if not output.is_absolute():
            output = PROJECT_ROOT / output
        payload.update(write_account_report(record, report, output_path=output, events_path=Path(args.events).expanduser()))
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"Buyer account verification: {payload}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
