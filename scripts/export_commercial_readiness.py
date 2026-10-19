#!/usr/bin/env python3
"""Validate a draft-only export supplier, pricing, and compliance readiness contract."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.export_landed_cost_calculator import calculate_export_landed_cost
    from scripts.pricing_assumptions import load_assumptions, validate_assumption_config, validate_assumption_reference
    from scripts.quote_proof import strict_quote_proofs
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from export_landed_cost_calculator import calculate_export_landed_cost  # type: ignore
    from pricing_assumptions import load_assumptions, validate_assumption_config, validate_assumption_reference  # type: ignore
    from quote_proof import strict_quote_proofs  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "export_commercial_readiness.schema.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"


def load_contract(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Export commercial readiness contract must be an object: {path}")
    return value


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def finite_nonnegative(value: Any) -> bool:
    try:
        return float(value) >= 0
    except (TypeError, ValueError):
        return False


def build_scenarios(costs: dict[str, Any]) -> dict[str, float]:
    result = calculate_export_landed_cost(
        supplier_base_usd=float(costs["supplier_base"]),
        packaging_usd=float(costs["packaging"]),
        inland_freight_usd=float(costs["inland_freight"]),
        cha_docs_usd=float(costs["cha_customs_docs"]),
        port_handling_usd=float(costs["port_handling"]),
        international_freight_usd=float(costs["international_freight"]),
        insurance_usd=float(costs["insurance"]),
        bank_charges_pct=float(costs["bank_charges_pct"]),
        inspection_certification_usd=float(costs["inspection_certification"]),
        sample_cost_usd=float(costs["sample_cost"]),
        currency_buffer_pct=float(costs["currency_buffer_pct"]),
        payment_risk_pct=float(costs["payment_risk_pct"]),
    )
    multiplier = 1 + float(costs["margin_pct"]) / 100
    return {"EXW": round(result.exw_usd * multiplier, 2), "FOB": round(result.fob_usd * multiplier, 2), "CIF": round(result.cif_usd * multiplier, 2)}


def validate_contract(report: dict[str, Any]) -> list[str]:
    contract = load_contract()
    pricing_assumptions = load_assumptions()
    errors: list[str] = []
    for field in contract["required_fields"]:
        if field not in report or report.get(field) in (None, ""):
            errors.append(f"missing {field}")
    if clean(report.get("workflow_type")).upper() != "EXPORT":
        errors.append("workflow_type must be EXPORT")
    if clean(report.get("schema_version")) != contract["schema_version"]:
        errors.append(f"schema_version must be {contract['schema_version']}")
    if report.get("external_actions_executed") is not False:
        errors.append("external_actions_executed must be false")
    if clean(report.get("pricing_status")) not in set(contract["pricing_statuses"]):
        errors.append("pricing_status is not allowed")
    errors.extend(validate_assumption_config(pricing_assumptions, as_of=clean(report.get("generated_at"))[:10] or None))

    quote_proofs = report.get("supplier_quote_proofs") if isinstance(report.get("supplier_quote_proofs"), list) else []
    strict = strict_quote_proofs(clean(report.get("case_id")), quote_proofs)
    if report.get("pricing_status") == "DRAFT_READY" and len(strict) < 2:
        errors.append("export draft requires two distinct supplier-specific quote proofs")

    costs = report.get("cost_inputs_usd") if isinstance(report.get("cost_inputs_usd"), dict) else {}
    missing_costs = [key for key in contract["required_cost_components_usd"] if key not in costs or not finite_nonnegative(costs.get(key))]
    if report.get("pricing_status") == "DRAFT_READY" and missing_costs:
        errors.append("missing or invalid cost inputs: " + ", ".join(missing_costs))
    cost_assumptions = report.get("cost_assumptions") if isinstance(report.get("cost_assumptions"), dict) else {}
    if report.get("pricing_status") == "DRAFT_READY":
        for key in contract["required_cost_components_usd"]:
            if key == "supplier_base":
                continue
            assumption_ref = cost_assumptions.get(key)
            if isinstance(assumption_ref, dict):
                assumption_id = clean(assumption_ref.get("assumption_id"))
            else:
                assumption_id = clean(assumption_ref)
            if not assumption_id:
                errors.append(f"cost_assumptions.{key} is required for DRAFT_READY")
                continue
            errors.extend(
                f"cost_assumptions.{key}: {error}"
                for error in validate_assumption_reference(
                    assumption_id=assumption_id,
                    workflow_type="EXPORT",
                    component_key=key,
                    amount=costs.get(key),
                    as_of=clean(report.get("generated_at"))[:10] or None,
                    config=pricing_assumptions,
                )
            )

    candidate = report.get("candidate_hsn_itchs") if isinstance(report.get("candidate_hsn_itchs"), dict) else {}
    if clean(candidate.get("status")) not in set(contract["candidate_hsn_statuses"]):
        errors.append("candidate_hsn_itchs.status is not allowed")
    if report.get("pricing_status") == "DRAFT_READY" and not clean(candidate.get("value")):
        errors.append("candidate_hsn_itchs.value is required as a draft candidate")

    scomet = report.get("scomet_review") if isinstance(report.get("scomet_review"), dict) else {}
    scomet_status = clean(scomet.get("status"))
    if scomet_status not in set(contract["scomet_statuses"]):
        errors.append("scomet_review.status is not allowed")
    if scomet_status in {"SUSPECTED", "SPECIALIST_REVIEW_REQUIRED", "PROHIBITED"} and report.get("pricing_status") != "BLOCKED":
        errors.append("SCOMET/prohibited signal requires pricing_status=BLOCKED")

    for field in ("origin_questions", "destination_requirements", "unresolved_items"):
        if not isinstance(report.get(field), list):
            errors.append(f"{field} must be a list")
    if not clean(report.get("payment_risk_note")):
        errors.append("payment_risk_note is required")
    if not clean(report.get("incoterm_rationale")):
        errors.append("incoterm_rationale is required")
    try:
        if int(report.get("quote_validity_days")) <= 0:
            errors.append("quote_validity_days must be positive")
    except (TypeError, ValueError):
        errors.append("quote_validity_days must be an integer")

    if report.get("pricing_status") == "DRAFT_READY" and report.get("unresolved_items"):
        errors.append("DRAFT_READY cannot contain unresolved_items")
    if report.get("pricing_status") == "BLOCKED":
        if not report.get("unresolved_items"):
            errors.append("BLOCKED pricing requires explicit unresolved_items")
        if report.get("draft_scenarios_usd") not in ({}, None, ""):
            errors.append("BLOCKED pricing must not expose draft_scenarios_usd")
    return errors


def prepare_report(report: dict[str, Any]) -> dict[str, Any]:
    value = dict(report)
    contract = load_contract()
    value.setdefault("schema_version", contract["schema_version"])
    value.setdefault("generated_at", dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat())
    costs = value.get("cost_inputs_usd") if isinstance(value.get("cost_inputs_usd"), dict) else {}
    if all(finite_nonnegative(costs.get(key)) for key in contract["required_cost_components_usd"]):
        value["draft_scenarios_usd"] = build_scenarios(costs) if value.get("pricing_status") == "DRAFT_READY" else {}
    else:
        value.setdefault("draft_scenarios_usd", {})
    return value


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Export Commercial Readiness — {report['case_id']}", "", f"- Pricing status: `{report['pricing_status']}`",
        f"- Candidate HSN/ITC-HS: `{report['candidate_hsn_itchs'].get('value', '')}` (draft only)",
        f"- SCOMET review: `{report['scomet_review'].get('status', '')}`", f"- Quote validity: `{report['quote_validity_days']}` days",
        "- External actions executed: `false`", "", "## Draft scenarios (internal only)", "",
    ]
    lines.extend(f"- {name}: USD {amount}" for name, amount in (report.get("draft_scenarios_usd") or {}).items())
    lines.extend(["", "## Payment risk", "", clean(report["payment_risk_note"]), "", "## Incoterm rationale", "", clean(report["incoterm_rationale"]), "", "## Unresolved items", ""])
    lines.extend(f"- {item}" for item in report.get("unresolved_items") or ["None recorded"])
    lines.extend(["", "This is a draft-only commercial readiness report. It is not a final price, classification, origin, delivery, payment, or compliance commitment.", ""])
    return "\n".join(lines)


def write_report(report: dict[str, Any], *, output_dir: Path, events_path: Path = DEFAULT_EVENTS_PATH, actor: str = "pricing_risk") -> dict[str, str]:
    errors = validate_contract(report)
    if errors:
        raise ValueError("Invalid export commercial readiness report: " + "; ".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    case_id = clean(report["case_id"])
    json_path = output_dir / f"export_commercial_readiness_{case_id}.json"
    markdown_path = output_dir / f"export_commercial_readiness_{case_id}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    digest = hashlib.sha256(json.dumps(report, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    from scripts.event_ledger import append_event
    event = append_event(
        "pricing.export_draft_recorded", actor, case_id=case_id, object_type="pricing_draft", object_id=f"{case_id}:export_commercial",
        source="export_commercial_readiness",
        payload={"report_path": str(json_path), "schema_version": report["schema_version"], "pricing_status": report["pricing_status"]},
        citations=[str(json_path), *[clean(row.get("quote_proof_path")) for row in report["supplier_quote_proofs"]]],
        idempotency_key=f"export-commercial:{case_id}:{digest}", events_file=events_path,
    )
    return {"json_path": str(json_path), "markdown_path": str(markdown_path), "event_id": str(event["event_id"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    path = Path(args.input).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit("input must be a JSON object")
    report = prepare_report(raw)
    errors = validate_contract(report)
    payload: dict[str, Any] = {"status": "PASS" if not errors else "FAIL", "mode": "write" if args.write else "dry_run", "errors": errors, "report": report, "external_actions_executed": False}
    if args.write and not errors:
        output_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_OUTPUT_ROOT / clean(report["case_id"])
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        payload.update(write_report(report, output_dir=output_dir))
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"Export commercial readiness: {payload['status']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
