#!/usr/bin/env python3
"""Validate per-profile operating budgets in the Hermes specialist registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = PROJECT_ROOT / "config" / "hermes_specialist_profiles.yaml"
REQUIRED_BUDGET_FIELDS = {
    "max_turns",
    "max_runtime_seconds",
    "max_delegate_count",
    "max_delegate_depth",
    "retry_count",
    "max_artifacts",
    "stop_on_no_progress_turns",
}
REQUIRED_TELEMETRY_FIELDS = {"input_tokens", "output_tokens", "cost_usd", "latency_ms", "runtime_seconds"}


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("profile registry must be a mapping")
    return value


def positive_int(value: Any, *, allow_zero: bool = False) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and (value >= 0 if allow_zero else value > 0)


def validate_operating_budgets(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    telemetry = registry.get("telemetry_contract", {})
    exposed = set(telemetry.get("record_when_exposed_by_hermes", [])) if isinstance(telemetry, dict) else set()
    if not REQUIRED_TELEMETRY_FIELDS <= exposed:
        errors.append(f"telemetry_contract missing fields: {sorted(REQUIRED_TELEMETRY_FIELDS - exposed)}")
    profiles = registry.get("profiles", {})
    if not isinstance(profiles, dict) or not profiles:
        return errors + ["profiles must be a non-empty mapping"]
    for profile, spec in profiles.items():
        if not isinstance(spec, dict):
            errors.append(f"{profile} spec must be a mapping")
            continue
        budget = spec.get("operating_budget")
        if not isinstance(budget, dict):
            errors.append(f"{profile}.operating_budget is required")
            continue
        missing = REQUIRED_BUDGET_FIELDS - set(budget)
        if missing:
            errors.append(f"{profile}.operating_budget missing fields: {sorted(missing)}")
        for field in ("max_turns", "max_runtime_seconds", "retry_count", "max_artifacts", "stop_on_no_progress_turns"):
            if field in budget and not positive_int(budget[field]):
                errors.append(f"{profile}.operating_budget.{field} must be a positive integer")
        for field in ("max_delegate_count", "max_delegate_depth"):
            if field in budget and not positive_int(budget[field], allow_zero=True):
                errors.append(f"{profile}.operating_budget.{field} must be a non-negative integer")
        if budget.get("max_turns") != spec.get("max_turns"):
            errors.append(f"{profile}.operating_budget.max_turns must match max_turns")
        if budget.get("max_runtime_seconds") != spec.get("task_timeout_seconds"):
            errors.append(f"{profile}.operating_budget.max_runtime_seconds must match task_timeout_seconds")
        delegate_limits = spec.get("delegate_limits") or {}
        if budget.get("max_delegate_count") != delegate_limits.get("max_delegates"):
            errors.append(f"{profile}.operating_budget.max_delegate_count must match delegate_limits.max_delegates")
        if budget.get("max_delegate_depth") != delegate_limits.get("max_depth"):
            errors.append(f"{profile}.operating_budget.max_delegate_depth must match delegate_limits.max_depth")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors = validate_operating_budgets(load_registry(Path(args.registry)))
    payload = {"status": "PASS" if not errors else "FAIL", "errors": errors}
    print(json.dumps(payload, indent=2) if args.json else f"Profile operating budgets: {payload['status']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
