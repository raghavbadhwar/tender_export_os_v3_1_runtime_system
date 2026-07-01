#!/usr/bin/env python3
"""Stage saved ChatGPT Deep Research leads without doing web research."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SCHEMA = PROJECT_ROOT / "config" / "schemas" / "deep_research_lead_schema.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "deep_research_staging"

FORBIDDEN_ACTIONS = {
    "SUBMIT",
    "SEND_QUOTE",
    "PAY",
    "UPLOAD",
    "USE_DSC",
    "COMMIT_PRICE",
    "CERTIFY_COMPLIANCE",
}


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


def stable_hash(parts: list[str]) -> str:
    raw = "|".join(str(part or "").strip().lower() for part in parts if str(part or "").strip())
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _minimal_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and stripped.endswith(":"):
            current_key = stripped[:-1]
            data[current_key] = []
            continue
        if not line.startswith(" ") and ":" in stripped:
            key, _, value = stripped.partition(":")
            data[key] = value.strip().strip('"')
            current_key = key
            continue
        if stripped.startswith("- ") and current_key:
            data.setdefault(current_key, []).append(stripped[2:].strip().strip('"'))
    return data


def load_schema(path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ModuleNotFoundError:
        return _minimal_yaml(path)


def parse_input(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        fenced = re.search(r"```json\s*(.*?)```", text, flags=re.S | re.I)
        if fenced:
            data = json.loads(fenced.group(1))
        else:
            return [], {
                "raw_report_path": display_path(path),
                "parse_note": "No structured JSON leads found. Save a JSON lead appendix before staging.",
            }
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)], {"raw_report_path": display_path(path)}
    if isinstance(data, dict):
        leads = data.get("leads", [])
        if isinstance(leads, list):
            meta = {key: value for key, value in data.items() if key != "leads"}
            meta.setdefault("raw_report_path", display_path(path))
            return [item for item in leads if isinstance(item, dict)], meta
    return [], {"raw_report_path": display_path(path), "parse_note": "Input JSON did not contain a lead list."}


def normalized_action(value: str) -> str:
    return str(value or "").strip().upper().replace(" ", "_")


def normalized_evidence(value: str) -> str:
    return str(value or "").strip().upper().replace(" ", "_")


def normalize_lead(lead: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(lead)
    normalized["recommended_repo_action"] = normalized_action(str(normalized.get("recommended_repo_action", "")))
    normalized["evidence_level"] = normalized_evidence(str(normalized.get("evidence_level", "")))
    if "owner_review_required" not in normalized or normalized["owner_review_required"] in {"", None}:
        normalized["owner_review_required"] = True

    evidence = normalized["evidence_level"]
    action = normalized["recommended_repo_action"]
    if evidence == "PUBLIC_LISTING_ONLY" and action == "CREATE_CASE_CANDIDATE_AFTER_EVIDENCE":
        normalized["original_recommended_repo_action"] = action
        normalized["recommended_repo_action"] = "MANUAL_SOURCE_CHECK"
        normalized["staging_warning"] = "PUBLIC_LISTING_ONLY is a lead, not a bid-ready case candidate."

    case_candidate_levels = set(schema.get("case_candidate_evidence_levels", []))
    normalized["case_candidate_allowed"] = (
        normalized["recommended_repo_action"] == "CREATE_CASE_CANDIDATE_AFTER_EVIDENCE"
        and evidence in case_candidate_levels
    )
    normalized["operational_stage"] = "CASE_CANDIDATE_REVIEW" if normalized["case_candidate_allowed"] else "LEAD_STAGING"
    return normalized


def validate_lead(lead: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = schema.get("required_fields", [])
    for field in required:
        value = lead.get(field)
        if field not in lead or value in {"", None} or value == []:
            errors.append(f"{lead.get('lead_id', '<unknown>')}: missing required field {field}")

    action = normalized_action(str(lead.get("recommended_repo_action", "")))
    allowed = set(schema.get("allowed_recommended_repo_actions", []))
    forbidden = set(schema.get("forbidden_recommended_repo_actions", [])) | FORBIDDEN_ACTIONS
    if action in forbidden:
        errors.append(f"{lead.get('lead_id', '<unknown>')}: forbidden recommended_repo_action {action}")
    elif action not in allowed:
        errors.append(f"{lead.get('lead_id', '<unknown>')}: unsupported recommended_repo_action {action}")

    evidence = normalized_evidence(str(lead.get("evidence_level", "")))
    if evidence not in set(schema.get("evidence_levels", [])):
        errors.append(f"{lead.get('lead_id', '<unknown>')}: unsupported evidence_level {evidence}")

    workflow = str(lead.get("workflow_type", "")).strip().upper()
    if workflow and workflow not in set(schema.get("workflow_types", [])):
        errors.append(f"{lead.get('lead_id', '<unknown>')}: unsupported workflow_type {workflow}")

    source_url = str(lead.get("source_url", ""))
    if source_url and not re.match(r"^https?://", source_url):
        errors.append(f"{lead.get('lead_id', '<unknown>')}: source_url must be http(s)")

    return errors


def validate_leads(leads: list[dict[str, Any]], schema: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    normalized: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    for lead in leads:
        errors.extend(validate_lead(lead, schema))
        item = normalize_lead(lead, schema)
        if item.get("staging_warning"):
            warnings.append(f"{item.get('lead_id')}: {item['staging_warning']}")
        normalized.append(item)
    return normalized, errors, warnings


def existing_case_keys() -> dict[str, str]:
    path = DATA_DIR / "master_cases.csv"
    keys: dict[str, str] = {}
    if not path.exists():
        return keys
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            case_id = row.get("case_id", "")
            if not case_id:
                continue
            if row.get("source_url"):
                keys[stable_hash([row.get("source_url", "")])] = case_id
            keys[stable_hash([row.get("opportunity_title", ""), row.get("buyer_name", ""), row.get("deadline_date", "")])] = case_id
    return keys


def existing_staged_keys(output_dir: Path) -> dict[str, str]:
    keys: dict[str, str] = {}
    if not output_dir.exists():
        return keys
    for path in output_dir.glob("**/staged_leads.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for lead in data.get("leads", []):
            lead_id = str(lead.get("lead_id", ""))
            if lead.get("source_url"):
                keys[stable_hash([lead.get("source_url", "")])] = lead_id
            keys[stable_hash([lead.get("lead_title", ""), lead.get("buyer_name", ""), lead.get("deadline", "")])] = lead_id
    return keys


def annotate_duplicates(leads: list[dict[str, Any]], output_dir: Path) -> list[dict[str, Any]]:
    case_keys = existing_case_keys()
    staged_keys = existing_staged_keys(output_dir)
    annotated = []
    for lead in leads:
        item = dict(lead)
        url_key = stable_hash([str(item.get("source_url", ""))]) if item.get("source_url") else ""
        title_key = stable_hash([str(item.get("lead_title", "")), str(item.get("buyer_name", "")), str(item.get("deadline", ""))])
        duplicate = case_keys.get(url_key) or case_keys.get(title_key)
        staged_duplicate = staged_keys.get(url_key) or staged_keys.get(title_key)
        item["duplicate_existing_case_id"] = duplicate or ""
        item["duplicate_existing_staged_lead_id"] = staged_duplicate or ""
        if duplicate:
            item["recommended_repo_action"] = "WATCH"
            item["staging_warning"] = "Duplicate of existing case; keep as watch item unless owner asks otherwise."
            item["case_candidate_allowed"] = False
            item["operational_stage"] = "DUPLICATE_WATCH"
        annotated.append(item)
    return annotated


def build_payload(
    input_path: Path,
    leads: list[dict[str, Any]],
    meta: dict[str, Any],
    warnings: list[str],
    mode: str,
) -> dict[str, Any]:
    staged_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    return {
        "staging_id": f"DRSTAGE-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}",
        "mode": mode,
        "staged_at": staged_at,
        "input_path": display_path(input_path),
        "source_meta": meta,
        "lead_count": len(leads),
        "case_candidate_allowed_count": sum(1 for lead in leads if lead.get("case_candidate_allowed")),
        "warnings": warnings,
        "external_actions_executed": False,
        "master_cases_mutated": False,
        "safety_note": "Staging only. No web research, sends, submissions, uploads, payments, DSC use, final price, final compliance, HSN/ITC-HS, or origin claims.",
        "leads": leads,
    }


def write_payload(payload: dict[str, Any], output_dir: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = output_dir / f"{stamp}_{payload['staging_id']}"
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "staged_leads.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def append_stage_event(payload: dict[str, Any], output_path: Path) -> None:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from event_ledger import append_event

    append_event(
        "deep_research.leads_staged",
        "stage_deep_research_leads",
        object_type="deep_research_lead",
        object_id=payload["staging_id"],
        source="chatgpt_scheduled_deep_research",
        payload={
            "staging_id": payload["staging_id"],
            "lead_count": payload["lead_count"],
            "case_candidate_allowed_count": payload["case_candidate_allowed_count"],
            "output_path": display_path(output_path),
            "external_actions_executed": False,
            "master_cases_mutated": False,
        },
        citations=[display_path(output_path), payload["input_path"]],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage saved Deep Research leads; does not browse the web.")
    parser.add_argument("--input", required=True, help="Saved Deep Research JSON/Markdown file")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Validate and write a dry-run staging package")
    mode.add_argument("--stage", action="store_true", help="Write staging package and append event-ledger staging event")
    parser.add_argument("--create-radar-leads", action="store_true", help="Reserved for explicit future owner-approved register mutation")
    parser.add_argument("--no-event", action="store_true", help="With --stage, write package without appending event")
    args = parser.parse_args()

    if args.create_radar_leads:
        print("--create-radar-leads is intentionally not implemented in this staging helper. Use Radar after evidence review.")
        return 2

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1

    schema = load_schema(Path(args.schema))
    leads, meta = parse_input(input_path)
    normalized, errors, warnings = validate_leads(leads, schema)
    if errors:
        print("Deep Research lead staging failed:")
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    annotated = annotate_duplicates(normalized, output_dir)
    mode_name = "stage" if args.stage else "dry_run"
    payload = build_payload(input_path, annotated, meta, warnings, mode_name)
    output_path = write_payload(payload, output_dir)

    if args.stage and not args.no_event:
        append_stage_event(payload, output_path)

    print(f"Deep Research lead staging {mode_name} complete")
    print(f"Staging output: {display_path(output_path)}")
    print("No external actions executed. master_cases.csv was not mutated.")
    if warnings:
        for warning in warnings:
            print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
