#!/usr/bin/env python3
"""Independent internal critic for high-risk compliance matrices."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.compliance_matrix_contract import validate_matrix
    from scripts.event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from compliance_matrix_contract import validate_matrix  # type: ignore
    from event_ledger import append_event  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "compliance_critic.schema.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"
SCOMET_WORDS = {"scomet", "restricted", "prohibited", "export control", "dual use"}


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"compliance critic schema must be an object: {path}")
    return value


def contains_scomet_signal(matrix: dict[str, Any]) -> bool:
    text = json.dumps(matrix, ensure_ascii=False).casefold()
    return any(word in text for word in SCOMET_WORDS)


def high_risk_clauses(matrix: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or load_schema()
    high_risk_types = {clean(item).casefold() for item in schema["high_risk_requirement_types"]}
    result: list[str] = []
    for clause in matrix.get("clauses") if isinstance(matrix.get("clauses"), list) else []:
        if not isinstance(clause, dict):
            continue
        requirement_type = clean(clause.get("requirement_type")).casefold()
        position = clean(clause.get("position"))
        text = f"{clause.get('requirement_text', '')} {clause.get('reason', '')}".casefold()
        if (
            requirement_type in high_risk_types
            or position in {"UNKNOWN", "OWNER/EXPERT_REVIEW", "DOES_NOT_COMPLY"}
            or any(word in text for word in SCOMET_WORDS)
        ):
            result.append(clean(clause.get("clause_id")) or f"index_{len(result) + 1}")
    return result


def review_matrix(matrix: dict[str, Any]) -> dict[str, Any]:
    schema = load_schema()
    validation_errors = validate_matrix(matrix)
    risky = high_risk_clauses(matrix, schema)
    scomet_signal = contains_scomet_signal(matrix)
    critic_required = bool(risky or scomet_signal)
    gaps = list(validation_errors)
    if scomet_signal and not any("SCOMET" in gap.upper() for gap in gaps):
        gaps.append("SCOMET/restricted/prohibited signal requires specialist review before promotion")
    if any("stale by policy" in gap for gap in validation_errors):
        gaps.append("stale official source blocks compliance promotion")
    if gaps:
        status = "BLOCKED"
    elif critic_required:
        status = "REVIEW_REQUIRED"
    else:
        status = "PASS_NO_CRITIC_REQUIRED"
    return {
        "schema_version": schema["schema_version"],
        "case_id": clean(matrix.get("case_id")),
        "workflow_type": clean(matrix.get("workflow_type")).upper(),
        "reviewed_at": utc_now(),
        "critic_required": critic_required,
        "status": status,
        "high_risk_clauses": risky,
        "scomet_signal": scomet_signal,
        "gaps": gaps,
        "can_write_final_state": False,
        "external_actions_executed": False,
        "boundary": schema["boundary"],
    }


def validate_review(review: dict[str, Any]) -> list[str]:
    schema = load_schema()
    errors: list[str] = []
    for field in schema["required_fields"]:
        if field not in review or review.get(field) in (None, ""):
            errors.append(f"missing {field}")
    if review.get("schema_version") != schema["schema_version"]:
        errors.append(f"schema_version must be {schema['schema_version']}")
    if review.get("status") not in schema["statuses"]:
        errors.append("status is not allowed")
    if review.get("can_write_final_state") is not False:
        errors.append("can_write_final_state must be false")
    if review.get("external_actions_executed") is not False:
        errors.append("external_actions_executed must be false")
    if not isinstance(review.get("gaps"), list):
        errors.append("gaps must be a list")
    return errors


def hash_review(review: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(review, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def write_review(review: dict[str, Any], *, output_dir: Path, events_path: Path = DEFAULT_EVENTS_PATH) -> dict[str, str]:
    errors = validate_review(review)
    if errors:
        raise ValueError("Invalid compliance critic review: " + "; ".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    case_id = clean(review["case_id"])
    output_path = output_dir / f"compliance_critic_{case_id}.json"
    output_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    digest = hash_review(review)
    event = append_event(
        "compliance.critic_reviewed",
        "compliance_due_diligence",
        case_id=case_id,
        object_type="compliance",
        object_id=f"{case_id}:critic",
        source="compliance_critic",
        payload={
            "report_path": str(output_path.relative_to(PROJECT_ROOT)) if output_path.is_relative_to(PROJECT_ROOT) else str(output_path),
            "schema_version": review["schema_version"],
            "status": review["status"],
            "critic_required": review["critic_required"],
            "report_sha256": digest,
        },
        citations=[str(output_path.relative_to(PROJECT_ROOT)) if output_path.is_relative_to(PROJECT_ROOT) else str(output_path)],
        idempotency_key=f"compliance-critic:{case_id}:{digest}",
        events_file=events_path,
    )
    return {"json_path": str(output_path), "report_sha256": digest, "event_id": str(event["event_id"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--events", default=str(DEFAULT_EVENTS_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    matrix_path = Path(args.matrix).expanduser()
    if not matrix_path.is_absolute():
        matrix_path = PROJECT_ROOT / matrix_path
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    if not isinstance(matrix, dict):
        raise SystemExit("matrix must be a JSON object")
    review = review_matrix(matrix)
    payload: dict[str, Any] = {"status": review["status"], "mode": "write" if args.write else "dry_run", "review": review, "external_actions_executed": False}
    if args.write:
        output_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_OUTPUT_ROOT / clean(review["case_id"])
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        payload.update(write_review(review, output_dir=output_dir, events_path=Path(args.events).expanduser()))
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"Compliance critic: {review['status']}")
    return 0 if review["status"] != "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
