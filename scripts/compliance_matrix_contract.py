#!/usr/bin/env python3
"""Validate and render a clause-by-clause draft compliance matrix.

No model or template can turn missing proof into compliance.  This contract
requires every clause to choose one explicit position and keeps uncertainty
as UNKNOWN or OWNER/EXPERT_REVIEW for the owner-facing workflow.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event
from scripts.compliance_source_policy import load_policy as load_source_policy
from scripts.compliance_source_policy import validate_citation as validate_source_citation
from scripts.compliance_source_policy import validate_policy as validate_source_policy


SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "compliance_matrix.schema.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def load_contract(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Compliance matrix contract must be an object: {path}")
    return value


def _parse_datetime(value: Any) -> bool:
    try:
        parsed = dt.datetime.fromisoformat(clean_text(value).replace("Z", "+00:00"))
        return parsed.tzinfo is not None
    except ValueError:
        return False


def _forbidden_key_paths(value: Any, forbidden: set[str], prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).casefold() in forbidden:
                paths.append(path)
            paths.extend(_forbidden_key_paths(child, forbidden, path))
        return paths
    if isinstance(value, list):
        return [path for index, child in enumerate(value) for path in _forbidden_key_paths(child, forbidden, f"{prefix}[{index}]")]
    return []


def validate_citations(
    value: Any,
    *,
    label: str,
    required: bool,
    workflow_type: str,
    requirement_type: str,
    generated_at: str,
    source_policy: dict[str, Any],
) -> list[str]:
    citations = value if isinstance(value, list) else []
    errors: list[str] = []
    if required and not citations:
        return [f"{label} requires at least one page/source citation"]
    if value is not None and not isinstance(value, list):
        return [f"{label} must be a list"]
    for index, citation in enumerate(citations, start=1):
        prefix = f"{label}[{index}]"
        if not isinstance(citation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not (clean_text(citation.get("source_path")) or clean_text(citation.get("source_url"))):
            errors.append(f"{prefix} requires source_path or source_url")
        page = citation.get("page")
        if page not in (None, ""):
            try:
                if int(str(page)) < 1:
                    raise ValueError
            except ValueError:
                errors.append(f"{prefix}.page must be a positive number when supplied")
        errors.extend(
            f"{prefix}: {error}"
            for error in validate_source_citation(
                citation,
                workflow_type=workflow_type,
                requirement_type=requirement_type,
                generated_at=generated_at,
                policy=source_policy,
            )
        )
    return errors


def validate_matrix(matrix: dict[str, Any], contract: dict[str, Any] | None = None) -> list[str]:
    contract = contract or load_contract()
    source_policy = load_source_policy()
    errors: list[str] = []
    for field in contract["required_top_level"]:
        if field not in matrix or matrix.get(field) is None:
            errors.append(f"missing required field: {field}")
    if matrix.get("schema_version") != contract["schema_version"]:
        errors.append(f"schema_version must be {contract['schema_version']}")
    if clean_text(matrix.get("workflow_type")).upper() not in set(contract["workflow_types"]):
        errors.append("workflow_type must be GOV or EXPORT")
    if not clean_text(matrix.get("case_id")):
        errors.append("case_id is required")
    if not _parse_datetime(matrix.get("generated_at")):
        errors.append("generated_at must be ISO-8601 with timezone")
    if matrix.get("matrix_status") not in set(contract["matrix_statuses"]):
        errors.append("matrix_status is not allowed")
    if matrix.get("external_actions_executed") is not False:
        errors.append("external_actions_executed must be false")
    errors.extend(validate_source_policy(source_policy))
    clauses = matrix.get("clauses")
    if not isinstance(clauses, list) or not clauses:
        errors.append("clauses must be a non-empty list")
        clauses = []
    positions = set(contract["positions"])
    ids: set[str] = set()
    blocking_positions: list[str] = []
    for index, clause in enumerate(clauses, start=1):
        prefix = f"clauses[{index}]"
        if not isinstance(clause, dict):
            errors.append(f"{prefix} must be an object")
            continue
        clause_id = clean_text(clause.get("clause_id"))
        if not clause_id:
            errors.append(f"{prefix}.clause_id is required")
        elif clause_id in ids:
            errors.append(f"duplicate clause_id: {clause_id}")
        ids.add(clause_id)
        for field in ("requirement_text", "requirement_type"):
            if not clean_text(clause.get(field)):
                errors.append(f"{prefix}.{field} is required")
        position = clean_text(clause.get("position"))
        if position not in positions:
            errors.append(f"{prefix}.position must be one of {sorted(positions)}")
            continue
        requires_citation = position in {"COMPLIES", "DOES_NOT_COMPLY"}
        errors.extend(
            validate_citations(
                clause.get("evidence_citations"),
                label=f"{prefix}.evidence_citations",
                required=requires_citation,
                workflow_type=clean_text(matrix.get("workflow_type")).upper(),
                requirement_type=clean_text(clause.get("requirement_type")),
                generated_at=clean_text(matrix.get("generated_at")),
                source_policy=source_policy,
            )
        )
        if position in {"DOES_NOT_COMPLY", "UNKNOWN", "OWNER/EXPERT_REVIEW"}:
            blocking_positions.append(clause_id or f"index_{index}")
        if position in {"UNKNOWN", "OWNER/EXPERT_REVIEW"}:
            if not clean_text(clause.get("reason")):
                errors.append(f"{prefix}.reason is required for {position}")
        if position == "DOES_NOT_COMPLY" and clause.get("owner_decision_needed") is not True:
            errors.append(f"{prefix}.owner_decision_needed must be true for DOES_NOT_COMPLY")
        if position == "OWNER/EXPERT_REVIEW" and clause.get("owner_decision_needed") is not True:
            errors.append(f"{prefix}.owner_decision_needed must be true for OWNER/EXPERT_REVIEW")
    unresolved = matrix.get("unresolved_items")
    if not isinstance(unresolved, list):
        errors.append("unresolved_items must be a list")
    elif blocking_positions and not unresolved:
        errors.append("DOES_NOT_COMPLY, UNKNOWN, or OWNER/EXPERT_REVIEW clauses require unresolved_items")
    if matrix.get("matrix_status") == "DRAFT_READY" and blocking_positions:
        errors.append("DRAFT_READY matrix may not contain DOES_NOT_COMPLY, UNKNOWN, or OWNER/EXPERT_REVIEW clauses")
    forbidden = {str(item).casefold() for item in contract.get("prohibited_keys", [])}
    for path in _forbidden_key_paths(matrix, forbidden):
        errors.append(f"prohibited raw/private field: {path}")
    return errors


def citation_text(citations: list[dict[str, Any]]) -> str:
    values: list[str] = []
    for citation in citations:
        source = clean_text(citation.get("source_path")) or clean_text(citation.get("source_url"))
        if not source:
            continue
        page = clean_text(citation.get("page"))
        values.append(f"{source}:p.{page}" if page else source)
    return "; ".join(dict.fromkeys(values)) or "No citation"


def render_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        f"# Clause-by-Clause Compliance Draft — {matrix['case_id']}",
        "",
        f"- Workflow: `{matrix['workflow_type']}`",
        f"- Matrix status: `{matrix['matrix_status']}`",
        f"- Generated at: `{matrix['generated_at']}`",
        "- External actions executed: `false`",
        "",
        "| Clause | Requirement | Position | Evidence / reason | Owner decision |",
        "|---|---|---|---|---|",
    ]
    for clause in matrix["clauses"]:
        basis = citation_text(clause.get("evidence_citations", [])) or clean_text(clause.get("reason"))
        clause_id = clean_text(clause.get("clause_id"))
        requirement = clean_text(clause.get("requirement_text")).replace("|", "\\|")
        evidence = basis.replace("|", "\\|")
        position = clean_text(clause.get("position"))
        owner_decision = str(bool(clause.get("owner_decision_needed"))).lower()
        lines.append(
            f"| {clause_id} | {requirement} | {position} | {evidence} | {owner_decision} |"
        )
    lines.extend(["", "## Unresolved items", ""])
    lines.extend(f"- {item}" for item in matrix["unresolved_items"] or ["- None"])
    lines.extend(["", "## Boundary", "", "This is a draft-only matrix. UNKNOWN and OWNER/EXPERT_REVIEW clauses are blockers, not compliance claims; it does not certify eligibility, legal compliance, origin, classification, price, or submission readiness.", ""])
    return "\n".join(lines)


def write_matrix(matrix: dict[str, Any], *, output_dir: Path, events_path: Path = DEFAULT_EVENTS_PATH, actor: str = "compliance_due_diligence") -> dict[str, Path | str]:
    errors = validate_matrix(matrix)
    if errors:
        raise ValueError("Invalid compliance matrix: " + "; ".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    case_id = clean_text(matrix["case_id"])
    json_path = output_dir / f"compliance_draft_{case_id}.json"
    markdown_path = output_dir / f"compliance_draft_{case_id}.md"
    json_path.write_text(json.dumps(matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(matrix), encoding="utf-8")
    digest = hashlib.sha256(json.dumps(matrix, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    citations = [str(json_path), str(markdown_path)]
    for clause in matrix["clauses"]:
        for citation in clause.get("evidence_citations", []) if isinstance(clause, dict) else []:
            if isinstance(citation, dict):
                citations.extend([clean_text(citation.get("source_path")), clean_text(citation.get("source_url"))])
    event = append_event(
        "compliance.matrix_drafted",
        actor,
        case_id=case_id,
        object_type="compliance",
        object_id=f"{case_id}:matrix",
        source="compliance_matrix_contract",
        payload={"report_path": str(json_path), "schema_version": matrix["schema_version"], "matrix_status": matrix["matrix_status"]},
        citations=[item for item in citations if item],
        idempotency_key=f"compliance-matrix:{case_id}:{digest}",
        events_file=events_path,
    )
    return {"json_path": json_path, "markdown_path": markdown_path, "event_id": str(event["event_id"])}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--actor", default="compliance_due_diligence")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    path = Path(args.input).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    matrix = _load_json(path)
    errors = validate_matrix(matrix)
    payload: dict[str, Any] = {"status": "PASS" if not errors else "FAIL", "mode": "write" if args.write else "dry_run", "case_id": matrix.get("case_id", ""), "errors": errors, "external_actions_executed": False}
    if not errors and args.write:
        output_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_OUTPUT_ROOT / clean_text(matrix["case_id"])
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        payload.update({key: str(value) for key, value in write_matrix(matrix, output_dir=output_dir, actor=args.actor).items()})
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"Compliance matrix contract: {payload}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
