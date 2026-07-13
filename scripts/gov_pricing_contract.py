#!/usr/bin/env python3
"""Validate and render a complete, cited GOV pricing draft.

This contract is intentionally stricter than a calculator: every commercial
cost family must be explicit, each non-zero or assumed line needs a dated
source/assumption basis, and unresolved costs prevent a draft from presenting
itself as price-ready.  Nothing here commits a price externally.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event
from scripts.pricing_assumptions import load_assumptions, validate_assumption_config, validate_assumption_reference


SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "gov_pricing.schema.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_contract(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"GOV pricing contract must be an object: {path}")
    return value


def is_iso_date(value: Any) -> bool:
    try:
        dt.date.fromisoformat(clean_text(value)[:10])
        return True
    except ValueError:
        return False


def finite_nonnegative(value: Any) -> bool:
    if isinstance(value, bool) or value in (None, ""):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number >= 0


def finite_number(value: Any) -> bool:
    if isinstance(value, bool) or value in (None, ""):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
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
        return [item for index, child in enumerate(value) for item in _forbidden_key_paths(child, forbidden, f"{prefix}[{index}]")]
    return []


def validate_report(report: dict[str, Any], contract: dict[str, Any] | None = None) -> list[str]:
    contract = contract or load_contract()
    pricing_assumptions = load_assumptions()
    errors: list[str] = []
    for field in contract["required_top_level"]:
        if field not in report or report.get(field) is None:
            errors.append(f"missing required field: {field}")
    if report.get("schema_version") != contract["schema_version"]:
        errors.append(f"schema_version must be {contract['schema_version']}")
    if clean_text(report.get("workflow_type")).upper() != "GOV":
        errors.append("workflow_type must be GOV")
    if not clean_text(report.get("case_id")):
        errors.append("case_id is required")
    try:
        parsed = dt.datetime.fromisoformat(clean_text(report.get("generated_at")).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            errors.append("generated_at must include timezone")
    except ValueError:
        errors.append("generated_at must be ISO-8601")
    if report.get("supplier_gate_status") != "PASS":
        errors.append("supplier_gate_status must be PASS before GOV pricing draft can be written")
    if report.get("external_actions_executed") is not False:
        errors.append("external_actions_executed must be false")
    if report.get("pricing_status") not in set(contract["pricing_statuses"]):
        errors.append("pricing_status is not allowed")
    errors.extend(validate_assumption_config(pricing_assumptions, as_of=clean_text(report.get("generated_at"))[:10] or None))

    quote_proofs = report.get("supplier_quote_proofs")
    if not isinstance(quote_proofs, list) or len({clean_text(row.get("supplier_id") or row.get("supplier_name")) for row in quote_proofs if isinstance(row, dict)}) < 2:
        errors.append("supplier_quote_proofs requires two distinct supplier entries")
    else:
        for index, quote in enumerate(quote_proofs, start=1):
            if not isinstance(quote, dict):
                errors.append(f"supplier_quote_proofs[{index}] must be an object")
                continue
            for field in ("quote_id", "quote_proof_path", "source_date"):
                if not clean_text(quote.get(field)):
                    errors.append(f"supplier_quote_proofs[{index}].{field} is required")
            if quote.get("source_date") and not is_iso_date(quote.get("source_date")):
                errors.append(f"supplier_quote_proofs[{index}].source_date must be ISO date")

    waterfall = report.get("cost_waterfall")
    components = waterfall.get("components") if isinstance(waterfall, dict) else None
    if not isinstance(components, list):
        errors.append("cost_waterfall.components must be a list")
        components = []
    keys = [clean_text(item.get("key")) for item in components if isinstance(item, dict)]
    required_keys = set(contract["required_component_keys"])
    missing_keys = sorted(required_keys - set(keys))
    if missing_keys:
        errors.append("cost_waterfall missing required components: " + ", ".join(missing_keys))
    if len(keys) != len(set(keys)):
        errors.append("cost_waterfall component keys must be unique")
    statuses = set(contract["component_statuses"])
    unknown_components: list[str] = []
    for index, component in enumerate(components, start=1):
        if not isinstance(component, dict):
            errors.append(f"cost_waterfall.components[{index}] must be an object")
            continue
        key = clean_text(component.get("key"))
        status = clean_text(component.get("status")).upper()
        if not key:
            errors.append(f"cost_waterfall.components[{index}].key is required")
        if status not in statuses:
            errors.append(f"cost_waterfall.components[{index}].status is not allowed")
            continue
        if status in {"OBSERVED", "ASSUMED", "NOT_APPLICABLE"}:
            if not finite_nonnegative(component.get("amount_inr")):
                errors.append(f"cost_waterfall.components[{index}].amount_inr must be finite and non-negative")
            if status != "NOT_APPLICABLE" and not is_iso_date(component.get("source_date")):
                errors.append(f"cost_waterfall.components[{index}].source_date is required for {status}")
            if status == "OBSERVED" and not clean_text(component.get("evidence_path")):
                errors.append(f"cost_waterfall.components[{index}].evidence_path is required for OBSERVED")
            if status == "ASSUMED" and not clean_text(component.get("assumption_id")):
                errors.append(f"cost_waterfall.components[{index}].assumption_id is required for ASSUMED")
            if status == "ASSUMED" and clean_text(component.get("assumption_id")):
                errors.extend(
                    f"cost_waterfall.components[{index}]: {error}"
                    for error in validate_assumption_reference(
                        assumption_id=clean_text(component.get("assumption_id")),
                        workflow_type="GOV",
                        component_key=key,
                        amount=component.get("amount_inr"),
                        as_of=clean_text(report.get("generated_at"))[:10] or None,
                        config=pricing_assumptions,
                    )
                )
        else:
            unknown_components.append(key or f"index_{index}")
            if not clean_text(component.get("reason")):
                errors.append(f"cost_waterfall.components[{index}].reason is required for UNKNOWN")
            if component.get("amount_inr") not in (None, ""):
                errors.append(f"cost_waterfall.components[{index}].amount_inr must be blank for UNKNOWN")

    working_capital = report.get("working_capital")
    if not isinstance(working_capital, dict):
        errors.append("working_capital must be an object")
    else:
        for field in ("supplier_payment_day", "buyer_payment_day", "gap_days", "cash_gap_inr", "annual_financing_rate_pct"):
            if not finite_nonnegative(working_capital.get(field)):
                errors.append(f"working_capital.{field} must be finite and non-negative")
        if not clean_text(working_capital.get("source_date")) or not is_iso_date(working_capital.get("source_date")):
            errors.append("working_capital.source_date is required")

    l1_sensitivity = report.get("l1_sensitivity")
    if not isinstance(l1_sensitivity, list) or len(l1_sensitivity) < 3:
        errors.append("l1_sensitivity requires at least three scenarios")
    else:
        for index, scenario in enumerate(l1_sensitivity, start=1):
            if not isinstance(scenario, dict):
                errors.append(f"l1_sensitivity[{index}] must be an object")
                continue
            for field in ("scenario", "bid_price_inr", "gross_margin_inr", "gross_margin_pct", "decision_warning"):
                if field == "scenario" or field == "decision_warning":
                    if not clean_text(scenario.get(field)):
                        errors.append(f"l1_sensitivity[{index}].{field} is required")
                elif not finite_number(scenario.get(field)):
                    errors.append(f"l1_sensitivity[{index}].{field} must be finite")

    margin_scenarios = report.get("margin_scenarios")
    if not isinstance(margin_scenarios, list) or len(margin_scenarios) < 3:
        errors.append("margin_scenarios requires conservative, recommended, and aggressive scenarios")
    else:
        names = {clean_text(item.get("name")).casefold() for item in margin_scenarios if isinstance(item, dict)}
        for name in ("conservative", "recommended", "aggressive"):
            if name not in names:
                errors.append(f"margin_scenarios missing {name}")
        for index, scenario in enumerate(margin_scenarios, start=1):
            if not isinstance(scenario, dict):
                errors.append(f"margin_scenarios[{index}] must be an object")
                continue
            if not finite_nonnegative(scenario.get("margin_pct")) or not finite_nonnegative(scenario.get("bid_price_inr")):
                errors.append(f"margin_scenarios[{index}] requires non-negative margin_pct and bid_price_inr")

    source_dates = report.get("source_dates")
    if not isinstance(source_dates, list) or not source_dates:
        errors.append("source_dates must contain at least one dated source")
    else:
        for index, item in enumerate(source_dates, start=1):
            if not isinstance(item, dict):
                errors.append(f"source_dates[{index}] must be an object")
                continue
            for field in ("source_name", "source_date", "evidence_path"):
                if not clean_text(item.get(field)):
                    errors.append(f"source_dates[{index}].{field} is required")
            if item.get("source_date") and not is_iso_date(item.get("source_date")):
                errors.append(f"source_dates[{index}].source_date must be ISO date")

    assumptions = report.get("assumptions")
    if not isinstance(assumptions, list):
        errors.append("assumptions must be a list")
    else:
        for index, item in enumerate(assumptions, start=1):
            if not isinstance(item, dict) or not clean_text(item.get("assumption_id")) or not clean_text(item.get("basis")):
                errors.append(f"assumptions[{index}] requires assumption_id and basis")
    unresolved = report.get("unresolved_items")
    if not isinstance(unresolved, list):
        errors.append("unresolved_items must be a list")
    elif unknown_components and not unresolved:
        errors.append("UNKNOWN cost components require unresolved_items")
    if report.get("pricing_status") == "DRAFT_READY" and unknown_components:
        errors.append("DRAFT_READY pricing may not contain UNKNOWN cost components")
    final_price = report.get("final_bid_price_inr")
    if report.get("pricing_status") == "DRAFT_READY" and not finite_nonnegative(final_price):
        errors.append("DRAFT_READY requires finite final_bid_price_inr")
    if report.get("pricing_status") == "BLOCKED" and final_price not in (None, ""):
        errors.append("BLOCKED pricing must leave final_bid_price_inr blank")

    forbidden = {str(item).casefold() for item in contract.get("prohibited_keys", [])}
    for path in _forbidden_key_paths(report, forbidden):
        errors.append(f"prohibited raw/private field: {path}")
    return errors


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# GOV Pricing Draft — {report['case_id']}",
        "",
        f"- Pricing status: `{report['pricing_status']}`",
        f"- Supplier 5-3-2 gate: `{report['supplier_gate_status']}`",
        f"- Generated at: `{report['generated_at']}`",
        "- External actions executed: `false`",
        "",
        "## Cost waterfall",
        "",
        "| Component | Status | Amount (INR) | Source / assumption |",
        "|---|---|---:|---|",
    ]
    for component in report["cost_waterfall"]["components"]:
        basis = clean_text(component.get("evidence_path")) or clean_text(component.get("assumption_id")) or clean_text(component.get("reason"))
        lines.append(f"| {component.get('key', '')} | {component.get('status', '')} | {component.get('amount_inr', '')} | {basis} |")
    wc = report["working_capital"]
    lines.extend(
        [
            "",
            "## Working capital",
            "",
            f"- Supplier payment day: `{wc['supplier_payment_day']}`",
            f"- Buyer payment day: `{wc['buyer_payment_day']}`",
            f"- Gap days: `{wc['gap_days']}`",
            f"- Cash gap (INR): `{wc['cash_gap_inr']}`",
            "",
            "## L1 sensitivity and margin scenarios",
            "",
        ]
    )
    for scenario in report["l1_sensitivity"]:
        lines.append(f"- `{scenario['scenario']}`: bid ₹{scenario['bid_price_inr']}; margin ₹{scenario['gross_margin_inr']} ({scenario['gross_margin_pct']}%); {scenario['decision_warning']}")
    for scenario in report["margin_scenarios"]:
        lines.append(f"- Margin `{scenario['name']}`: {scenario['margin_pct']}% → ₹{scenario['bid_price_inr']}")
    lines.extend(["", "## Assumptions and unresolved items", ""])
    lines.extend(f"- Assumption `{item.get('assumption_id', '')}`: {item.get('basis', '')}" for item in report["assumptions"] or ["- None"])
    lines.extend(f"- Unresolved: {item}" for item in report["unresolved_items"] or ["- None"])
    lines.extend(["", "## Boundary", "", "Draft-only internal decision support. This does not commit a price, delivery, payment term, supplier, or tender submission.", ""])
    return "\n".join(lines)


def write_pricing(report: dict[str, Any], *, output_dir: Path, events_path: Path = DEFAULT_EVENTS_PATH, actor: str = "pricing_risk") -> dict[str, Path | str]:
    errors = validate_report(report)
    if errors:
        raise ValueError("Invalid GOV pricing report: " + "; ".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    case_id = clean_text(report["case_id"])
    json_path = output_dir / f"pricing_{case_id}.json"
    markdown_path = output_dir / f"pricing_{case_id}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    digest = hashlib.sha256(json.dumps(report, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    citations = [str(json_path), str(markdown_path)]
    citations.extend(clean_text(item.get("evidence_path")) for item in report["source_dates"] if isinstance(item, dict))
    citations.extend(clean_text(item.get("quote_proof_path")) for item in report["supplier_quote_proofs"] if isinstance(item, dict))
    event = append_event(
        "pricing.gov_draft_recorded",
        actor,
        case_id=case_id,
        object_type="pricing_draft",
        object_id=f"{case_id}:gov_pricing",
        source="gov_pricing_contract",
        payload={"report_path": str(json_path), "schema_version": report["schema_version"], "pricing_status": report["pricing_status"]},
        citations=[item for item in citations if item],
        idempotency_key=f"gov-pricing:{case_id}:{digest}",
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
    parser.add_argument("--actor", default="pricing_risk")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    input_path = Path(args.input).expanduser()
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    report = _load_json(input_path)
    errors = validate_report(report)
    payload: dict[str, Any] = {"status": "PASS" if not errors else "FAIL", "mode": "write" if args.write else "dry_run", "case_id": report.get("case_id", ""), "errors": errors, "external_actions_executed": False}
    if not errors and args.write:
        output_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_OUTPUT_ROOT / clean_text(report["case_id"])
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        payload.update({key: str(value) for key, value in write_pricing(report, output_dir=output_dir, actor=args.actor).items()})
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"GOV pricing contract: {payload}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
