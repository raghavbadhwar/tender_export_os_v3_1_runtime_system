#!/usr/bin/env python3
"""Validate versioned pricing assumptions for draft cost waterfalls."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - direct CLI dependency error
    yaml = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSUMPTIONS_PATH = PROJECT_ROOT / "config" / "pricing_assumptions.yaml"


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def upper(value: Any) -> str:
    return clean(value).upper()


def parse_date(value: Any) -> dt.date | None:
    try:
        return dt.date.fromisoformat(clean(value)[:10])
    except ValueError:
        return None


def as_of_date(value: dt.date | str | None = None) -> dt.date:
    if isinstance(value, dt.date):
        return value
    if value:
        parsed = parse_date(value)
        if parsed is None:
            raise ValueError("as_of must be an ISO date")
        return parsed
    return dt.datetime.now(dt.timezone.utc).date()


def finite_number(value: Any) -> bool:
    try:
        float(value)
        return not isinstance(value, bool)
    except (TypeError, ValueError):
        return False


def load_assumptions(path: Path = DEFAULT_ASSUMPTIONS_PATH) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load pricing assumptions")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"pricing assumptions must be a mapping: {path}")
    return value


def assumption_index(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {clean(item.get("assumption_id")): dict(item) for item in config.get("assumptions", []) if isinstance(item, dict)}


def validate_assumption_config(config: dict[str, Any], *, as_of: dt.date | str | None = None) -> list[str]:
    errors: list[str] = []
    required = [clean(item) for item in config.get("required_fields", [])]
    allowed_statuses = {upper(item) for item in config.get("allowed_statuses", [])}
    allowed_workflows = {upper(item) for item in config.get("allowed_workflows", [])}
    seen: set[str] = set()
    today = as_of_date(as_of)
    for index, item in enumerate(config.get("assumptions", []), start=1):
        if not isinstance(item, dict):
            errors.append(f"assumptions[{index}] must be an object")
            continue
        assumption_id = clean(item.get("assumption_id"))
        if not assumption_id:
            errors.append(f"assumptions[{index}].assumption_id is required")
        elif assumption_id in seen:
            errors.append(f"duplicate assumption_id: {assumption_id}")
        seen.add(assumption_id)
        for field in required:
            if item.get(field) in (None, ""):
                errors.append(f"{assumption_id or index}.{field} is required")
        if upper(item.get("status")) not in allowed_statuses:
            errors.append(f"{assumption_id}.status is not allowed")
        if upper(item.get("workflow_type")) not in allowed_workflows:
            errors.append(f"{assumption_id}.workflow_type is not allowed")
        observed = parse_date(item.get("observed_date"))
        expiry = parse_date(item.get("expiry_date"))
        if observed is None:
            errors.append(f"{assumption_id}.observed_date must be ISO date")
        if expiry is None:
            errors.append(f"{assumption_id}.expiry_date must be ISO date")
        if observed and expiry and expiry < observed:
            errors.append(f"{assumption_id}.expiry_date cannot be before observed_date")
        if expiry and expiry < today and upper(item.get("status")) == "ACTIVE":
            errors.append(f"{assumption_id} is ACTIVE but expired")
        for field in ("default_value", "conservative_value"):
            if not finite_number(item.get(field)):
                errors.append(f"{assumption_id}.{field} must be numeric")
        if finite_number(item.get("default_value")) and float(item.get("default_value")) == 0 and not clean(item.get("zero_value_reason")):
            errors.append(f"{assumption_id}.zero_value_reason is required when default_value is zero")
    return errors


def validate_assumption_reference(
    *,
    assumption_id: str,
    workflow_type: str,
    component_key: str,
    amount: Any,
    as_of: dt.date | str | None = None,
    config: dict[str, Any] | None = None,
) -> list[str]:
    config = config or load_assumptions()
    index = assumption_index(config)
    errors: list[str] = []
    assumption = index.get(clean(assumption_id))
    label = clean(assumption_id) or f"{workflow_type}:{component_key}"
    if assumption is None:
        return [f"{label} does not reference an active versioned pricing assumption"]
    if upper(assumption.get("status")) != "ACTIVE":
        errors.append(f"{label} is not ACTIVE")
    if upper(assumption.get("workflow_type")) != upper(workflow_type):
        errors.append(f"{label} workflow_type mismatch")
    if clean(assumption.get("component_key")) != clean(component_key):
        errors.append(f"{label} component_key mismatch")
    expiry = parse_date(assumption.get("expiry_date"))
    if expiry is None:
        errors.append(f"{label}.expiry_date must be ISO date")
    elif expiry < as_of_date(as_of):
        errors.append(f"{label} expired on {expiry.isoformat()}")
    if finite_number(amount) and float(amount) == 0 and not clean(assumption.get("zero_value_reason")):
        errors.append(f"{label} cannot justify a zero cost")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_ASSUMPTIONS_PATH))
    parser.add_argument("--as-of", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors = validate_assumption_config(load_assumptions(Path(args.config)), as_of=args.as_of or None)
    payload = {"status": "PASS" if not errors else "FAIL", "errors": errors}
    print(json.dumps(payload, indent=2) if args.json else f"Pricing assumptions: {payload['status']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
