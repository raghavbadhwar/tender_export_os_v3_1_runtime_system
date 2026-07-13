#!/usr/bin/env python3
"""Build internal pricing scenarios for GOV and EXPORT cases."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

try:
    from scripts.event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import append_event  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "pricing_scenarios.schema.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value)) and not isinstance(value, bool)
    except (TypeError, ValueError):
        return False


def number(value: Any) -> float:
    if not finite_number(value):
        raise ValueError(f"expected finite number, got {value!r}")
    return float(value)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"pricing scenario schema must be an object: {path}")
    return value


def build_scenarios(
    *,
    case_id: str,
    workflow_type: str,
    base_cost: float,
    currency: str,
    target_margin_pct: float,
    quote_validity_days: int,
    working_capital_need: float = 0,
    price_sensitivity_pct: float = 5,
    stress_cost_increase_pct: float = 12,
    owner_min_margin_pct: float = 8,
) -> dict[str, Any]:
    if base_cost <= 0:
        raise ValueError("base_cost must be positive")
    if quote_validity_days <= 0:
        raise ValueError("quote_validity_days must be positive")
    workflow = clean(workflow_type).upper()
    if workflow not in {"GOV", "EXPORT"}:
        raise ValueError("workflow_type must be GOV or EXPORT")
    if working_capital_need < 0:
        raise ValueError("working_capital_need must be non-negative")

    schema = load_schema()
    base_price = base_cost * (1 + target_margin_pct / 100)
    conservative_cost = base_cost * 1.05 + working_capital_need
    conservative_price = conservative_cost * (1 + target_margin_pct / 100)
    stress_cost = base_cost * (1 + stress_cost_increase_pct / 100) + working_capital_need
    stress_price = base_price
    walk_away_price = (base_cost + working_capital_need) * (1 + owner_min_margin_pct / 100)

    def scenario(name: str, cost: float, price: float, margin_pct: float, warning: str) -> dict[str, Any]:
        margin = price - cost
        return {
            "name": name,
            "cost": round(cost, 2),
            "price": round(price, 2),
            "gross_margin": round(margin, 2),
            "gross_margin_pct": round((margin / price) * 100, 2) if price else 0,
            "downside_loss": round(max(0, cost - price), 2),
            "working_capital_need": round(working_capital_need, 2),
            "quote_validity_days": quote_validity_days,
            "price_sensitivity_pct": round(price_sensitivity_pct, 2),
            "owner_decision_threshold": round(walk_away_price, 2),
            "decision_warning": warning,
            "final_commitment": False,
            "target_margin_pct": round(margin_pct, 2),
        }

    report = {
        "schema_version": schema["schema_version"],
        "case_id": clean(case_id),
        "workflow_type": workflow,
        "generated_at": utc_now(),
        "currency": clean(currency),
        "base_cost": round(base_cost, 2),
        "quote_validity_days": quote_validity_days,
        "owner_decision_threshold": {
            "minimum_price": round(walk_away_price, 2),
            "minimum_margin_pct": round(owner_min_margin_pct, 2),
            "rule": "Do not send, submit, or approve below threshold without explicit owner override.",
        },
        "scenarios": [
            scenario("base", base_cost, base_price, target_margin_pct, "internal_base_case"),
            scenario("conservative", conservative_cost, conservative_price, target_margin_pct, "uses cost and working-capital cushion"),
            scenario("stress", stress_cost, stress_price, target_margin_pct, "downside risk if cost rises but price cannot move"),
            scenario("walk_away", base_cost + working_capital_need, walk_away_price, owner_min_margin_pct, "minimum owner decision threshold"),
        ],
        "external_actions_executed": False,
        "boundary": schema["boundary"],
    }
    errors = validate_report(report)
    if errors:
        raise ValueError("Invalid pricing scenario report: " + "; ".join(errors))
    return report


def validate_report(report: dict[str, Any]) -> list[str]:
    schema = load_schema()
    errors: list[str] = []
    for field in schema["required_fields"]:
        if field not in report or report.get(field) in (None, ""):
            errors.append(f"missing {field}")
    if report.get("schema_version") != schema["schema_version"]:
        errors.append(f"schema_version must be {schema['schema_version']}")
    if clean(report.get("workflow_type")).upper() not in {"GOV", "EXPORT"}:
        errors.append("workflow_type must be GOV or EXPORT")
    if report.get("external_actions_executed") is not False:
        errors.append("external_actions_executed must be false")
    scenarios = report.get("scenarios")
    if not isinstance(scenarios, list):
        errors.append("scenarios must be a list")
        return errors
    names = [clean(item.get("name")) for item in scenarios if isinstance(item, dict)]
    if names != schema["scenario_names"]:
        errors.append("scenarios must be ordered as: " + ", ".join(schema["scenario_names"]))
    for index, item in enumerate(scenarios, start=1):
        if not isinstance(item, dict):
            errors.append(f"scenarios[{index}] must be an object")
            continue
        for field in ("cost", "price", "gross_margin", "gross_margin_pct", "downside_loss", "working_capital_need", "quote_validity_days", "price_sensitivity_pct", "owner_decision_threshold"):
            if not finite_number(item.get(field)):
                errors.append(f"scenarios[{index}].{field} must be numeric")
        if item.get("final_commitment") is not False:
            errors.append(f"scenarios[{index}].final_commitment must be false")
        if not clean(item.get("decision_warning")):
            errors.append(f"scenarios[{index}].decision_warning is required")
    return errors


def hash_report(report: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(report, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def write_report(report: dict[str, Any], *, output_dir: Path, events_path: Path = DEFAULT_EVENTS_PATH) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    digest = hash_report(report)
    case_id = clean(report["case_id"])
    json_path = output_dir / f"pricing_scenarios_{case_id}.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    event = append_event(
        "pricing.scenarios_drafted",
        "pricing_risk",
        case_id=case_id,
        object_type="pricing_draft",
        object_id=f"{case_id}:pricing_scenarios",
        source="pricing_scenario_builder",
        payload={
            "report_path": str(json_path.relative_to(PROJECT_ROOT)) if json_path.is_relative_to(PROJECT_ROOT) else str(json_path),
            "schema_version": report["schema_version"],
            "report_sha256": digest,
            "scenario_count": len(report["scenarios"]),
        },
        citations=[str(json_path.relative_to(PROJECT_ROOT)) if json_path.is_relative_to(PROJECT_ROOT) else str(json_path)],
        idempotency_key=f"pricing-scenarios:{case_id}:{digest}",
        events_file=events_path,
    )
    return {"json_path": str(json_path), "report_sha256": digest, "event_id": str(event["event_id"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--workflow-type", required=True, choices=["GOV", "EXPORT"])
    parser.add_argument("--base-cost", required=True, type=float)
    parser.add_argument("--currency", required=True)
    parser.add_argument("--target-margin-pct", required=True, type=float)
    parser.add_argument("--quote-validity-days", required=True, type=int)
    parser.add_argument("--working-capital-need", type=float, default=0)
    parser.add_argument("--price-sensitivity-pct", type=float, default=5)
    parser.add_argument("--stress-cost-increase-pct", type=float, default=12)
    parser.add_argument("--owner-min-margin-pct", type=float, default=8)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_scenarios(
        case_id=args.case_id,
        workflow_type=args.workflow_type,
        base_cost=args.base_cost,
        currency=args.currency,
        target_margin_pct=args.target_margin_pct,
        quote_validity_days=args.quote_validity_days,
        working_capital_need=args.working_capital_need,
        price_sensitivity_pct=args.price_sensitivity_pct,
        stress_cost_increase_pct=args.stress_cost_increase_pct,
        owner_min_margin_pct=args.owner_min_margin_pct,
    )
    payload: dict[str, Any] = {"status": "PASS", "mode": "write" if args.write else "dry_run", "report": report, "external_actions_executed": False}
    if args.write:
        output_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_OUTPUT_ROOT / args.case_id
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        payload.update(write_report(report, output_dir=output_dir))
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else "Pricing scenarios: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
