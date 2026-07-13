#!/usr/bin/env python3
"""Validate typed Kanban inputs, parent handoffs, and task completion evidence."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_HANDOFF_FIELDS = {
    "case_id",
    "workflow_type",
    "stage",
    "source_event_ids",
    "input_artifacts",
    "required_output_schema",
    "approval_required",
    "deadline",
    "stop_conditions",
    "next_profile",
}
NEEDS_INPUT_REASONS = {
    "owner_approval",
    "missing_documents",
    "unavailable_credentials",
    "ambiguous_compliance",
    "portal_human_challenge",
}
SUPPORTED_COMPLETION_VALIDATORS = frozenset(
    {
        "fast_kill_decision",
        "deep_read_report",
        "supplier_532",
        "pricing_readiness",
        "compliance_matrix",
        "artifact_manifest",
        "owner_approval_receipt",
        "execution_receipt",
        "buyer_verification",
        "learning_proposal",
        "evidence_bundle",
        "deterministic_fast_kill",
        "fast_kill_critic",
        "historical_commercial_intelligence",
        "bid_pack_verification",
        "evaluation_award_evidence",
        "delivery_payment_evidence",
        "export_demand_thesis",
        "buyer_target_hypothesis",
        "contact_path_proof",
        "gmail_plugin_handoff",
        "reply_classification",
        "rfq_verification",
        "export_quote_pack_verification",
        "negotiation_draft",
        "order_evidence",
        "shipment_payment_evidence",
        "repeat_buyer_learning",
    }
)
VALIDATOR_ALIASES = {
    "deterministic_fast_kill": "fast_kill_decision",
    "fast_kill_critic": "evidence_bundle",
    "historical_commercial_intelligence": "evidence_bundle",
    "bid_pack_verification": "artifact_manifest",
    "evaluation_award_evidence": "evidence_bundle",
    "delivery_payment_evidence": "evidence_bundle",
    "export_demand_thesis": "evidence_bundle",
    "buyer_target_hypothesis": "evidence_bundle",
    "contact_path_proof": "evidence_bundle",
    "gmail_plugin_handoff": "evidence_bundle",
    "reply_classification": "evidence_bundle",
    "rfq_verification": "evidence_bundle",
    "export_quote_pack_verification": "artifact_manifest",
    "negotiation_draft": "evidence_bundle",
    "order_evidence": "evidence_bundle",
    "shipment_payment_evidence": "evidence_bundle",
    "repeat_buyer_learning": "learning_proposal",
}


def _resolve(path: str, project_root: Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else project_root / candidate


def parse_handoff(body: str) -> dict[str, Any] | None:
    lines = body.splitlines()
    try:
        marker = lines.index("TEOS_TYPED_HANDOFF_V1")
    except ValueError:
        return None
    if marker + 1 >= len(lines):
        return None
    try:
        value = json.loads(lines[marker + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def validate_task_input(
    task: dict[str, Any],
    *,
    known_case_ids: set[str] | None = None,
    project_root: Path = PROJECT_ROOT,
    check_input_files: bool = True,
) -> dict[str, Any]:
    handoff = parse_handoff(str(task.get("body") or ""))
    errors: list[str] = []
    if handoff is None:
        return {"ok": False, "errors": ["typed handoff marker or JSON is missing"], "handoff": None}
    missing = sorted(REQUIRED_HANDOFF_FIELDS - set(handoff))
    if missing:
        errors.append(f"missing typed handoff fields: {', '.join(missing)}")
    case_id = str(handoff.get("case_id") or "")
    if known_case_ids is not None and case_id not in known_case_ids:
        errors.append(f"unknown case_id: {case_id}")
    if handoff.get("workflow_type") not in {"GOV", "EXPORT"}:
        errors.append("workflow_type must be GOV or EXPORT")
    if not isinstance(handoff.get("source_event_ids"), list):
        errors.append("source_event_ids must be a list")
    inputs = handoff.get("input_artifacts")
    if not isinstance(inputs, list):
        errors.append("input_artifacts must be a list")
        inputs = []
    if not isinstance(handoff.get("stop_conditions"), list):
        errors.append("stop_conditions must be a list")
    if not isinstance(handoff.get("approval_required"), bool):
        errors.append("approval_required must be a boolean")
    if not str(handoff.get("required_output_schema") or ""):
        errors.append("required_output_schema is empty")
    if not str(handoff.get("next_profile") or ""):
        errors.append("next_profile is empty")
    if check_input_files:
        missing_inputs = [path for path in inputs if not _resolve(str(path), project_root).exists()]
        if missing_inputs:
            errors.append(f"missing input artifacts: {', '.join(missing_inputs)}")
        schema = str(handoff.get("required_output_schema") or "")
        if schema and not _resolve(schema, project_root).is_file():
            errors.append(f"required output schema missing: {schema}")
    return {"ok": not errors, "errors": errors, "handoff": handoff}


def validate_parent_results(
    expected_parent_ids: list[str],
    parent_results: dict[str, dict[str, Any]],
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    visible_artifacts: list[str] = []
    for parent_id in expected_parent_ids:
        parent = parent_results.get(parent_id)
        if not parent:
            errors.append(f"parent result missing: {parent_id}")
            continue
        if str(parent.get("status") or "").lower() != "done":
            errors.append(f"parent not done: {parent_id}")
        result = parent.get("result") if isinstance(parent.get("result"), dict) else {}
        if result.get("status") != "PASS":
            errors.append(f"parent completion did not pass: {parent_id}")
        citations = result.get("citations")
        if not isinstance(citations, list) or not citations:
            errors.append(f"parent citations missing: {parent_id}")
        artifacts = result.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(f"parent artifacts missing: {parent_id}")
            continue
        for artifact in artifacts:
            path = _resolve(str(artifact), project_root)
            if not path.exists():
                errors.append(f"parent artifact not visible: {artifact}")
            else:
                visible_artifacts.append(str(artifact))
    return {"ok": not errors, "errors": errors, "visible_artifacts": visible_artifacts}


def _validate_stage(validator: str, result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if validator not in SUPPORTED_COMPLETION_VALIDATORS:
        return [f"unknown completion validator: {validator or '<empty>'}"]
    validator = VALIDATOR_ALIASES.get(validator, validator)
    if validator == "fast_kill_decision":
        if result.get("decision") not in {"FAST_KILL", "REJECTED", "WATCHLIST", "PROMOTE"}:
            errors.append("fast-kill decision is missing or invalid")
    elif validator == "deep_read_report":
        if result.get("document_readable") is not True:
            errors.append("deep-read document_readable must be true")
        if "ambiguous_clauses" not in result:
            errors.append("deep-read ambiguous_clauses must be explicit")
    elif validator == "supplier_532":
        if int(result.get("supplier_candidates") or 0) < 5:
            errors.append("supplier candidate count is below five")
        if int(result.get("source_types") or 0) < 3:
            errors.append("supplier source-type count is below three")
        if int(result.get("strict_quote_proofs") or 0) < 2:
            errors.append("strict quote proof count is below two")
    elif validator == "pricing_readiness":
        if int(result.get("strict_quote_proofs") or 0) < 2:
            errors.append("pricing readiness requires two strict quote proofs")
        if result.get("unknown_costs_zeroed") is not False:
            errors.append("pricing must state that unknown costs were not silently zeroed")
    elif validator == "compliance_matrix":
        statuses = set(result.get("clause_statuses") or [])
        allowed = {"COMPLIES", "DOES_NOT_COMPLY", "UNKNOWN", "OWNER/EXPERT_REVIEW"}
        if not statuses or not statuses <= allowed:
            errors.append("compliance clause statuses are missing or invalid")
    elif validator == "artifact_manifest":
        checks = result.get("artifact_checks")
        if isinstance(checks, list) and checks:
            if any(not isinstance(check, dict) for check in checks):
                errors.append("artifact verification checks must be objects")
            elif any(
                check.get("open_verified") is not True
                or check.get("render_verified") is not True
                or check.get("parse_verified") is not True
                for check in checks
            ):
                errors.append("artifact render/open/parse verification is incomplete")
        elif result.get("render_verified") is not True or result.get("parse_verified") is not True:
            errors.append("artifact render/open/parse verification is incomplete")
    elif validator == "owner_approval_receipt":
        if result.get("approval_status") not in {"APPROVED", "REJECTED", "CHANGES_REQUESTED"}:
            errors.append("owner approval receipt status is missing or invalid")
    elif validator == "execution_receipt":
        if not result.get("receipt_sha256"):
            errors.append("execution receipt hash is missing")
        if result.get("approval_scope_verified") is not True:
            errors.append("execution approval scope is not verified")
    elif validator == "buyer_verification":
        for field in ("legal_entity", "official_domain", "public_evidence_hash"):
            if not result.get(field):
                errors.append(f"buyer verification missing {field}")
    elif validator == "learning_proposal":
        if result.get("proposal_status") != "STAGED":
            errors.append("learning output must remain STAGED")
        if result.get("applied") is not False:
            errors.append("learning proposal may not be applied by completion")
    elif validator == "evidence_bundle":
        if not result.get("evidence_hashes"):
            errors.append("evidence bundle hashes are missing")
    return errors


def validate_completion(
    task: dict[str, Any],
    result: dict[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    handoff_result = validate_task_input(task, project_root=project_root, check_input_files=False)
    handoff = handoff_result.get("handoff") or task.get("handoff") or {}
    if not handoff_result["ok"]:
        errors.extend(handoff_result["errors"])
    if result.get("status") != "PASS":
        errors.append("completion status must be PASS")
    if result.get("case_id") != handoff.get("case_id"):
        errors.append("completion case_id mismatch")
    if result.get("stage") != handoff.get("stage"):
        errors.append("completion stage mismatch")
    citations = result.get("citations")
    if not isinstance(citations, list) or not citations:
        errors.append("completion citations are missing")
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("completion artifacts must be a list")
        artifacts = []
    expected = list(task.get("expected_outputs") or [])
    for expected_path in expected:
        if str(expected_path) not in [str(value) for value in artifacts]:
            errors.append(f"expected artifact not declared: {expected_path}")
        if not _resolve(str(expected_path), project_root).exists():
            errors.append(f"expected artifact missing: {expected_path}")
    run_logs = result.get("run_log_evidence")
    if not isinstance(run_logs, list) or not run_logs:
        errors.append("run-log evidence is missing")
    else:
        for run_log in run_logs:
            if not _resolve(str(run_log), project_root).is_file():
                errors.append(f"run-log evidence missing: {run_log}")
    errors.extend(_validate_stage(str(task.get("completion_validator") or ""), result))
    return {"ok": not errors, "errors": errors, "case_id": handoff.get("case_id"), "stage": handoff.get("stage")}


def can_auto_promote(task: dict[str, Any], *, parents_complete: bool) -> bool:
    if not parents_complete:
        return False
    block_kind = str(task.get("block_kind") or "")
    if block_kind in {"needs_input", "capability"}:
        return False
    if str(task.get("block_reason") or "") in NEEDS_INPUT_REASONS:
        return False
    return block_kind in {"", "dependency", "transient"}


def _known_case_ids(path: Path) -> set[str]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return {row.get("case_id", "") for row in csv.DictReader(handle) if row.get("case_id")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="JSON task file")
    parser.add_argument("--result", help="Optional JSON completion result")
    parser.add_argument("--output", default="outputs/kanban_task_graphs/handoff_validation.json")
    args = parser.parse_args()

    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    report: dict[str, Any] = {
        "input": validate_task_input(
            task,
            known_case_ids=_known_case_ids(PROJECT_ROOT / "data" / "master_cases.csv"),
        )
    }
    if args.result:
        result = json.loads(Path(args.result).read_text(encoding="utf-8"))
        report["completion"] = validate_completion(task, result)
    report["status"] = "PASS" if all(section.get("ok") for key, section in report.items() if key != "status") else "FAIL"
    report["external_actions_executed"] = False
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    os.chmod(output, 0o600)
    print(json.dumps({"status": report["status"], "output": str(output)}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
