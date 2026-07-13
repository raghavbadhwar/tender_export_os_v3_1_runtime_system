#!/usr/bin/env python3
"""Validate and render a citation-first GOV tender deep-read report.

This helper accepts structured extraction already produced from public or
owner-provided evidence. It deliberately does not browse, infer eligibility,
or make any tender portal, commercial, or compliance commitment.
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


SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "gov_deep_read.schema.json"
DEFAULT_CASE_REPORT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"
EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"


def load_contract(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"GOV deep-read schema must be an object: {path}")
    return value


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def parse_iso_timestamp(value: Any) -> bool:
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.tzinfo is not None
    except ValueError:
        return False


def validate_citations(value: Any, *, label: str, required: bool) -> list[str]:
    errors: list[str] = []
    citations = value if isinstance(value, list) else []
    if required and not citations:
        return [f"{label} requires at least one page/source citation"]
    if value is not None and not isinstance(value, list):
        return [f"{label}.citations must be a list"]
    for index, citation in enumerate(citations, start=1):
        prefix = f"{label}.citations[{index}]"
        if not isinstance(citation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not clean_text(citation.get("source_path")):
            errors.append(f"{prefix}.source_path is required")
        page = citation.get("page")
        try:
            page_value = int(str(page))
        except (TypeError, ValueError):
            page_value = 0
        if page_value < 1:
            errors.append(f"{prefix}.page must be a positive page number")
    return errors


def _forbidden_key_paths(value: Any, forbidden: set[str], prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        matches: list[str] = []
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).casefold() in forbidden:
                matches.append(path)
            matches.extend(_forbidden_key_paths(child, forbidden, path))
        return matches
    if isinstance(value, list):
        matches = []
        for index, child in enumerate(value):
            matches.extend(_forbidden_key_paths(child, forbidden, f"{prefix}[{index}]"))
        return matches
    return []


def validate_report(report: dict[str, Any], contract: dict[str, Any] | None = None) -> list[str]:
    contract = contract or load_contract()
    errors: list[str] = []
    for field in contract.get("required_top_level", []):
        value = report.get(field)
        if field not in report or value in (None, ""):
            errors.append(f"missing required field: {field}")
    if report.get("schema_version") != contract.get("schema_version"):
        errors.append(f"schema_version must be {contract.get('schema_version')}")
    if str(report.get("workflow_type") or "").upper() != "GOV":
        errors.append("workflow_type must be GOV")
    if not parse_iso_timestamp(report.get("generated_at")):
        errors.append("generated_at must be an ISO-8601 timestamp with timezone")
    if report.get("extraction_status") not in set(contract.get("extraction_statuses", [])):
        errors.append("extraction_status is not allowed")
    if report.get("recommended_case_status") not in set(contract.get("recommended_case_statuses", [])):
        errors.append("recommended_case_status is not allowed")
    if report.get("external_actions_executed") is not False:
        errors.append("external_actions_executed must be false")

    source_documents = report.get("source_documents")
    if not isinstance(source_documents, list) or not source_documents:
        errors.append("source_documents must be a non-empty list")
    else:
        for index, document in enumerate(source_documents, start=1):
            prefix = f"source_documents[{index}]"
            if not isinstance(document, dict):
                errors.append(f"{prefix} must be an object")
                continue
            for field in ("source_path", "sha256", "document_type"):
                if not clean_text(document.get(field)):
                    errors.append(f"{prefix}.{field} is required")
            digest = clean_text(document.get("sha256"))
            if digest and not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                errors.append(f"{prefix}.sha256 must be a SHA-256 hex digest")

    statuses = set(contract.get("fact_statuses", []))
    citation_required = set(contract.get("citation_required_for", []))
    reason_required = set(contract.get("unknown_reason_required_for", []))
    facts = report.get("facts")
    if not isinstance(facts, dict):
        errors.append("facts must be an object")
        facts = {}
    for key in contract.get("required_fact_keys", []):
        fact = facts.get(key)
        label = f"facts.{key}"
        if not isinstance(fact, dict):
            errors.append(f"{label} is required")
            continue
        status = clean_text(fact.get("status")).upper()
        if status not in statuses:
            errors.append(f"{label}.status is not allowed")
            continue
        if status == "EXTRACTED" and not clean_text(fact.get("value")):
            errors.append(f"{label}.value is required when EXTRACTED")
        if status in reason_required and not clean_text(fact.get("reason")):
            errors.append(f"{label}.reason is required when {status}")
        errors.extend(validate_citations(fact.get("citations"), label=label, required=status in citation_required))

    corrigenda = report.get("corrigenda")
    if not isinstance(corrigenda, list):
        errors.append("corrigenda must be a list")
    else:
        for index, item in enumerate(corrigenda, start=1):
            label = f"corrigenda[{index}]"
            if not isinstance(item, dict) or not clean_text(item.get("status")):
                errors.append(f"{label}.status is required")
                continue
            errors.extend(validate_citations(item.get("citations"), label=label, required=True))

    boq_lines = report.get("boq_lines")
    if not isinstance(boq_lines, list):
        errors.append("boq_lines must be a list")
    else:
        if report.get("extraction_status") == "COMPLETE" and not boq_lines:
            errors.append("COMPLETE deep read requires at least one BOQ line")
        for index, line in enumerate(boq_lines, start=1):
            label = f"boq_lines[{index}]"
            if not isinstance(line, dict):
                errors.append(f"{label} must be an object")
                continue
            for field in ("line_id", "description", "quantity", "unit"):
                if not clean_text(line.get(field)):
                    errors.append(f"{label}.{field} is required")
            errors.extend(validate_citations(line.get("citations"), label=label, required=True))

    ambiguous = report.get("ambiguous_clauses")
    if not isinstance(ambiguous, list):
        errors.append("ambiguous_clauses must be a list")
    else:
        for index, clause in enumerate(ambiguous, start=1):
            label = f"ambiguous_clauses[{index}]"
            if not isinstance(clause, dict):
                errors.append(f"{label} must be an object")
                continue
            for field in ("topic", "status", "summary"):
                if not clean_text(clause.get(field)):
                    errors.append(f"{label}.{field} is required")
            errors.extend(validate_citations(clause.get("citations"), label=label, required=True))

    forbidden = {str(item).casefold() for item in contract.get("prohibited_keys", [])}
    for path in _forbidden_key_paths(report, forbidden):
        errors.append(f"prohibited raw/private field: {path}")
    return errors


def citation_text(citations: list[dict[str, Any]]) -> str:
    parts = []
    for citation in citations:
        source = clean_text(citation.get("source_path"))
        page = clean_text(citation.get("page"))
        section = clean_text(citation.get("section"))
        item = f"{source}:p.{page}" if source and page else source
        if section:
            item += f" ({section})"
        if item:
            parts.append(item)
    return "; ".join(parts)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Government Tender Deep Read — {report['case_id']}",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Extraction status: `{report['extraction_status']}`",
        f"- Recommended case status: `{report['recommended_case_status']}`",
        f"- Generated at: `{report['generated_at']}`",
        "- External actions executed: `false`",
        "",
        "## Source documents",
        "",
    ]
    for document in report.get("source_documents", []):
        lines.append(
            f"- `{document.get('document_type', '')}` — `{document.get('source_path', '')}` "
            f"(sha256 `{document.get('sha256', '')}`)"
        )
    lines.extend(["", "## Tender facts", "", "| Fact | Status | Value / reason | Evidence |", "|---|---|---|---|"])
    for key, fact in report.get("facts", {}).items():
        value = clean_text(fact.get("value")) or clean_text(fact.get("reason"))
        lines.append(f"| {key} | {fact.get('status', '')} | {value} | {citation_text(fact.get('citations', []))} |")
    lines.extend(["", "## BOQ lines", "", "| Line | Description | Quantity | Unit | Evidence |", "|---|---|---:|---|---|"])
    for line in report.get("boq_lines", []):
        lines.append(
            f"| {line.get('line_id', '')} | {line.get('description', '')} | {line.get('quantity', '')} | "
            f"{line.get('unit', '')} | {citation_text(line.get('citations', []))} |"
        )
    lines.extend(["", "## Corrigenda", ""])
    if not report.get("corrigenda"):
        lines.append("- No corrigendum record supplied; verify this remains current before any decision.")
    for item in report.get("corrigenda", []):
        lines.append(f"- `{item.get('status', '')}` — {item.get('summary', '')} — {citation_text(item.get('citations', []))}")
    lines.extend(["", "## Ambiguous or risky clauses", ""])
    if not report.get("ambiguous_clauses"):
        lines.append("- None recorded. This is not a compliance certification.")
    for clause in report.get("ambiguous_clauses", []):
        lines.append(f"- **{clause.get('topic', '')}** ({clause.get('status', '')}): {clause.get('summary', '')} — {citation_text(clause.get('citations', []))}")
    lines.extend(["", "## Boundary", "", "Extraction and risk note only. Unknown, ambiguous, and missing proof remain blockers; this report does not certify eligibility, compliance, price, origin, delivery, or submission readiness.", ""])
    return "\n".join(lines)


def write_deep_read(
    report: dict[str, Any],
    *,
    output_dir: Path,
    events_path: Path = EVENTS_PATH,
    actor: str = "gov_tender_intelligence",
) -> dict[str, Path | str]:
    errors = validate_report(report)
    if errors:
        raise ValueError("Invalid GOV deep read: " + "; ".join(errors))
    case_id = clean_text(report["case_id"])
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"deep_read_{case_id}.json"
    markdown_path = output_dir / f"deep_read_{case_id}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    digest = hashlib.sha256(json.dumps(report, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    citations = [str(json_path), str(markdown_path)] + [str(item.get("source_path") or "") for item in report["source_documents"]]
    event = append_event(
        "case.deep_read_recorded",
        actor,
        case_id=case_id,
        object_type="case",
        object_id=case_id,
        source="gov_deep_read_contract",
        payload={
            "report_path": str(json_path),
            "markdown_path": str(markdown_path),
            "schema_version": report["schema_version"],
            "extraction_status": report["extraction_status"],
            "recommended_case_status": report["recommended_case_status"],
        },
        citations=[item for item in citations if item],
        idempotency_key=f"gov-deep-read:{case_id}:{digest}",
        events_file=events_path,
    )
    return {"json_path": json_path, "markdown_path": markdown_path, "event_id": str(event["event_id"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Structured GOV deep-read JSON from the evidence review lane")
    parser.add_argument("--case-id", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--actor", default="gov_tender_intelligence")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    input_path = Path(args.input).expanduser()
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    report = json.loads(input_path.read_text(encoding="utf-8"))
    if args.case_id and clean_text(report.get("case_id")) != args.case_id:
        raise SystemExit("--case-id does not match the structured report")
    errors = validate_report(report)
    payload: dict[str, Any] = {
        "status": "PASS" if not errors else "FAIL",
        "mode": "write" if args.write else "dry_run",
        "case_id": report.get("case_id", ""),
        "errors": errors,
        "external_actions_executed": False,
    }
    if not errors and args.write:
        output_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_CASE_REPORT_ROOT / str(report["case_id"])
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        result = write_deep_read(report, output_dir=output_dir, actor=args.actor)
        payload.update({key: str(value) for key, value in result.items()})
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"GOV deep-read {payload['status']}: {payload}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
