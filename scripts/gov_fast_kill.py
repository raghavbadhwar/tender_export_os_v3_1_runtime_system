#!/usr/bin/env python3
"""Run the deterministic, citation-gated first stage of GOV fast-kill.

Hard rejections only occur when the rule is supported by cited evidence. Missing
or uncited evidence becomes a watchlist item and, together with survivors and
high-value exceptions, is routed to the GOV specialist critic rather than
being silently promoted or rejected.
"""

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

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event
from scripts.score_opportunity import score_gov_opportunity


CONFIG_PATH = PROJECT_ROOT / "config" / "kill_rules.yaml"
CASES_PATH = PROJECT_ROOT / "data" / "master_cases.csv"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"
EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"kill rules must be a mapping: {path}")
    return value


def clean(value: Any) -> str:
    return str(value or "").strip()


def number(value: Any) -> float | None:
    text = clean(value).replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def boolish(value: Any) -> bool | None:
    text = clean(value).casefold()
    if not text:
        return None
    if text in {"true", "yes", "1", "y"}:
        return True
    if text in {"false", "no", "0", "n"}:
        return False
    return None


def normalize_evidence(evidence: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    normalized: dict[str, list[dict[str, Any]]] = {}
    for field, value in (evidence or {}).items():
        rows = value if isinstance(value, list) else [value]
        useful = [item for item in rows if isinstance(item, dict) and clean(item.get("source_path"))]
        if useful:
            normalized[str(field)] = useful
    return normalized


def cited(evidence: dict[str, list[dict[str, Any]]], fields: list[str]) -> bool:
    return bool(fields) and all(evidence.get(field) for field in fields)


def _rule_state(rule_id: str, case: dict[str, Any], thresholds: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    """Return matched, missing evidence keys, and evidence keys required to prove a match."""
    if rule_id == "GOV-KILL-01":
        days = number(case.get("days_to_deadline"))
        if days is None:
            return False, ["days_to_deadline"], ["days_to_deadline"]
        return days <= float(thresholds.get("min_days_to_deadline_gov", 5)), [], ["days_to_deadline"]
    if rule_id == "GOV-KILL-02":
        required, verified = number(case.get("turnover_required_inr")), number(case.get("our_verified_turnover_inr"))
        missing = [key for key, value in (("turnover_required_inr", required), ("our_verified_turnover_inr", verified)) if value is None]
        return bool(not missing and required is not None and verified is not None and required > verified), missing, ["turnover_required_inr", "our_verified_turnover_inr"]
    if rule_id == "GOV-KILL-03":
        required, documented = boolish(case.get("past_experience_required")), boolish(case.get("our_past_experience_documented"))
        missing = [key for key, value in (("past_experience_required", required), ("our_past_experience_documented", documented)) if value is None]
        return bool(not missing and required and documented is False), missing, ["past_experience_required", "our_past_experience_documented"]
    if rule_id == "GOV-KILL-04":
        required, available = boolish(case.get("oem_required")), boolish(case.get("oem_authorization_available"))
        missing = [key for key, value in (("oem_required", required), ("oem_authorization_available", available)) if value is None]
        return bool(not missing and required and available is False), missing, ["oem_required", "oem_authorization_available"]
    if rule_id == "GOV-KILL-05":
        required, held = boolish(case.get("mandatory_license_required")), boolish(case.get("license_held"))
        missing = [key for key, value in (("mandatory_license_required", required), ("license_held", held)) if value is None]
        return bool(not missing and required and held is False), missing, ["mandatory_license_required", "license_held"]
    if rule_id == "GOV-KILL-06":
        emd = number(case.get("emd_amount_inr"))
        if emd is None:
            return False, ["emd_amount_inr"], ["emd_amount_inr"]
        threshold = number(case.get("max_emd_threshold_inr")) or number(thresholds.get("max_emd_threshold_inr")) or 500000
        return emd > threshold, [], ["emd_amount_inr"]
    if rule_id == "GOV-KILL-07":
        active = boolish(case.get("category_active"))
        if active is None:
            return False, ["category_active"], ["category_active"]
        return active is False, [], ["category_active"]
    if rule_id == "GOV-KILL-08":
        value = clean(case.get("delivery_location_score")).casefold()
        if not value:
            return False, ["delivery_location_score"], ["delivery_location_score"]
        return value == "impossible", [], ["delivery_location_score"]
    if rule_id == "GOV-KILL-09":
        value = clean(case.get("payment_risk_score")).casefold()
        if not value:
            return False, ["payment_risk_score"], ["payment_risk_score"]
        return value == "high", [], ["payment_risk_score"]
    if rule_id == "GOV-KILL-10":
        complete, candidates = boolish(case.get("supplier_search_complete")), number(case.get("supplier_candidates_found"))
        if complete is None:
            # Supplier proof happens after initial fast kill; absence is not a rejection.
            return False, [], ["supplier_search_complete", "supplier_candidates_found"]
        missing = [key for key, value in (("supplier_candidates_found", candidates),) if value is None] if complete else []
        return bool(complete and not missing and candidates is not None and candidates < 3), missing, ["supplier_search_complete", "supplier_candidates_found"]
    if rule_id == "GOV-KILL-11":
        required = boolish(case.get("security_clearance_required"))
        if required is None:
            return False, ["security_clearance_required"], ["security_clearance_required"]
        return required, [], ["security_clearance_required"]
    if rule_id == "GOV-KILL-12":
        unmet = boolish(case.get("local_content_requirement_unmet"))
        if unmet is None:
            return False, ["local_content_requirement_unmet"], ["local_content_requirement_unmet"]
        return unmet, [], ["local_content_requirement_unmet"]
    return False, [], []


def evaluate_gov_fast_kill(
    case: dict[str, Any],
    evidence_citations: dict[str, Any] | None,
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate rules and score without changing the case register."""
    config = config or load_config()
    if clean(case.get("workflow_type") or "GOV").upper() != "GOV":
        raise ValueError("GOV fast kill only accepts workflow_type GOV")
    case_id = clean(case.get("case_id"))
    if not case_id:
        raise ValueError("case_id is required")
    control = config.get("gov_fast_kill_control") if isinstance(config.get("gov_fast_kill_control"), dict) else {}
    thresholds = config.get("thresholds") if isinstance(config.get("thresholds"), dict) else {}
    evidence = normalize_evidence(evidence_citations)
    matched_rules: list[dict[str, Any]] = []
    missing_evidence: set[str] = set()
    proven_hard_rules: list[str] = []
    unproven_hard_rules: list[str] = []
    watch_rules: list[str] = []
    rules = config.get("gov_kill_rules") if isinstance(config.get("gov_kill_rules"), list) else []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rule_id = clean(rule.get("rule_id"))
        matched, missing, proof_fields = _rule_state(rule_id, case, thresholds)
        missing_evidence.update(missing)
        if not matched:
            continue
        is_cited = cited(evidence, proof_fields)
        entry = {
            "rule_id": rule_id,
            "result": clean(rule.get("result")).upper(),
            "reason_code": clean(rule.get("reason_code")),
            "proof_fields": proof_fields,
            "cited_proof": is_cited,
        }
        matched_rules.append(entry)
        if entry["result"] == "REJECTED":
            (proven_hard_rules if is_cited else unproven_hard_rules).append(rule_id)
        else:
            watch_rules.append(rule_id)

    score = score_gov_opportunity(case)
    score_threshold = float(control.get("score_proceed_threshold", 60))
    score_watch = float(score["total"]) < score_threshold
    high_value_threshold = number(control.get("high_value_exception_inr")) or 5_000_000
    tender_value = number(case.get("estimated_value_inr")) or 0
    high_value = tender_value >= high_value_threshold
    review_reasons: list[str] = []
    if missing_evidence:
        review_reasons.append("missing_evidence")
    if unproven_hard_rules:
        review_reasons.append("uncited_hard_kill")
    if watch_rules:
        review_reasons.append("watch_rule")
    if score_watch:
        review_reasons.append("score_below_proceed_threshold")
    if high_value and proven_hard_rules:
        review_reasons.append("high_value_exception")

    if proven_hard_rules and not high_value:
        decision = "REJECTED"
    elif review_reasons:
        decision = "WATCHLIST"
    else:
        decision = "SURVIVED"
    critic_required = decision != "REJECTED" or (high_value and bool(proven_hard_rules))
    return {
        "schema_version": "gov_fast_kill.v1",
        "case_id": case_id,
        "workflow_type": "GOV",
        "decision": decision,
        "hard_rejection_proven": bool(proven_hard_rules and decision == "REJECTED"),
        "stage2_critic_required": critic_required,
        "review_reasons": review_reasons,
        "matched_rules": matched_rules,
        "proven_hard_rules": proven_hard_rules,
        "unproven_hard_rules": unproven_hard_rules,
        "watch_rules": watch_rules,
        "missing_evidence": sorted(missing_evidence),
        "score": score,
        "score_proceed_threshold": score_threshold,
        "high_value_exception": high_value and bool(proven_hard_rules),
        "evidence_citations": evidence,
        "external_actions_executed": False,
        "master_cases_mutated": False,
        "safety_note": "Deterministic triage only. Missing or uncited proof remains WATCHLIST; no external, portal, pricing, compliance, or case-register action executed.",
    }


def build_critic_handoff(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": decision["case_id"],
        "workflow_type": "GOV",
        "stage": "fast_kill_critic",
        "source_event_ids": [],
        "input_artifacts": [],
        "required_output_schema": "config/schemas/mcp_tool_result.schema.json",
        "approval_required": False,
        "deadline": "",
        "stop_conditions": ["missing_documents", "ambiguous_compliance"],
        "next_profile": "gov-tender-intelligence",
        "decision": decision["decision"],
        "review_reasons": decision["review_reasons"],
    }


def render_markdown(decision: dict[str, Any]) -> str:
    lines = [
        f"# GOV Fast Kill — {decision['case_id']}",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Stage-two critic required: `{decision['stage2_critic_required']}`",
        f"- Deterministic score: `{decision['score']['total']}/{100}`",
        f"- Review reasons: `{', '.join(decision['review_reasons']) or 'none'}`",
        "- External actions executed: `false`",
        "",
        "## Matched rules",
        "",
    ]
    if not decision["matched_rules"]:
        lines.append("- None")
    for rule in decision["matched_rules"]:
        lines.append(f"- `{rule['rule_id']}` → `{rule['result']}`; cited proof: `{rule['cited_proof']}`")
    lines.extend(["", "## Missing evidence", ""])
    for item in decision["missing_evidence"] or ["None"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Safety boundary", "", decision["safety_note"], ""])
    return "\n".join(lines)


def write_decision(
    decision: dict[str, Any],
    *,
    output_dir: Path,
    events_path: Path = EVENTS_PATH,
    actor: str = "gov_fast_kill",
) -> dict[str, Path | str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    case_id = clean(decision["case_id"])
    report_path = output_dir / f"fast_kill_{case_id}.json"
    markdown_path = output_dir / f"fast_kill_{case_id}.md"
    report_path.write_text(json.dumps(decision, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(decision), encoding="utf-8")
    no_go_path: Path | None = None
    if decision["decision"] == "REJECTED":
        no_go_path = output_dir / "no_go_reason_note.txt"
        no_go_path.write_text(
            f"{case_id}: hard rejection with cited rule(s): {', '.join(decision['proven_hard_rules'])}\n",
            encoding="utf-8",
        )
    digest = hashlib.sha256(json.dumps(decision, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    event = append_event(
        "case.fast_kill_completed",
        actor,
        case_id=case_id,
        object_type="case",
        object_id=case_id,
        source="deterministic_gov_fast_kill",
        payload={
            "decision": decision["decision"],
            "report_path": str(report_path),
            "score": decision["score"]["total"],
            "stage2_critic_required": decision["stage2_critic_required"],
        },
        citations=[str(report_path), str(markdown_path)],
        idempotency_key=f"gov-fast-kill:{case_id}:{digest}",
        events_file=events_path,
    )
    return {
        "report_path": report_path,
        "markdown_path": markdown_path,
        "no_go_path": no_go_path or "",
        "event_id": str(event["event_id"]),
    }


def load_case(case_id: str, cases_path: Path = CASES_PATH) -> dict[str, str]:
    with cases_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("case_id") == case_id:
                return row
    raise ValueError(f"case_id not found: {case_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--case-id")
    source.add_argument("--input", help="A single GOV case JSON object")
    parser.add_argument("--evidence", default="", help="JSON field-to-citations map")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.case_id:
        case = load_case(args.case_id)
    else:
        input_path = Path(args.input).expanduser()
        if not input_path.is_absolute():
            input_path = PROJECT_ROOT / input_path
        case = json.loads(input_path.read_text(encoding="utf-8"))
    evidence: dict[str, Any] = {}
    if args.evidence:
        evidence_path = Path(args.evidence).expanduser()
        if not evidence_path.is_absolute():
            evidence_path = PROJECT_ROOT / evidence_path
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    decision = evaluate_gov_fast_kill(case, evidence)
    payload: dict[str, Any] = {"mode": "write" if args.write else "dry_run", "decision": decision}
    if args.write:
        output_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_OUTPUT_ROOT / decision["case_id"]
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        payload["write_result"] = {key: str(value) for key, value in write_decision(decision, output_dir=output_dir).items()}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"GOV fast kill {decision['decision']}: {decision['case_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
