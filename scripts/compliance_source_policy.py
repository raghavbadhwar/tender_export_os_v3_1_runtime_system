#!/usr/bin/env python3
"""Validate compliance source kind and freshness rules."""

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
DEFAULT_POLICY_PATH = PROJECT_ROOT / "config" / "compliance_source_policy.yaml"


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def upper(value: Any) -> str:
    return clean(value).upper()


def parse_date(value: Any) -> dt.date | None:
    try:
        return dt.date.fromisoformat(clean(value)[:10])
    except ValueError:
        return None


def parse_generated_date(value: Any) -> dt.date:
    try:
        parsed = dt.datetime.fromisoformat(clean(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("generated_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("generated_at must include timezone")
    return parsed.date()


def load_policy(path: Path = DEFAULT_POLICY_PATH) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load compliance source policy")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"compliance source policy must be a mapping: {path}")
    return value


def requirement_policy(policy: dict[str, Any], workflow_type: str, requirement_type: str) -> dict[str, Any] | None:
    workflow = (policy.get("workflows") or {}).get(upper(workflow_type))
    if not isinstance(workflow, dict):
        return None
    requirements = workflow.get("requirement_types") if isinstance(workflow.get("requirement_types"), dict) else {}
    return requirements.get(clean(requirement_type).casefold()) or requirements.get(clean(requirement_type)) or requirements.get("general")


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    workflows = policy.get("workflows")
    if not isinstance(workflows, dict) or not workflows:
        return ["workflows must be a non-empty mapping"]
    for workflow_name, workflow in workflows.items():
        if workflow_name not in {"GOV", "EXPORT"}:
            errors.append(f"unknown workflow: {workflow_name}")
        if not isinstance(workflow, dict):
            errors.append(f"{workflow_name} must be a mapping")
            continue
        requirement_types = workflow.get("requirement_types")
        if not isinstance(requirement_types, dict) or not requirement_types:
            errors.append(f"{workflow_name}.requirement_types must be non-empty")
            continue
        for key, rule in requirement_types.items():
            if not isinstance(rule, dict):
                errors.append(f"{workflow_name}.{key} must be a mapping")
                continue
            if not rule.get("allowed_source_kinds"):
                errors.append(f"{workflow_name}.{key}.allowed_source_kinds is required")
            try:
                if int(rule.get("max_age_days")) <= 0:
                    errors.append(f"{workflow_name}.{key}.max_age_days must be positive")
            except (TypeError, ValueError):
                errors.append(f"{workflow_name}.{key}.max_age_days must be an integer")
            if rule.get("primary_required") is not True:
                errors.append(f"{workflow_name}.{key}.primary_required must be true")
    return errors


def validate_citation(
    citation: dict[str, Any],
    *,
    workflow_type: str,
    requirement_type: str,
    generated_at: str,
    policy: dict[str, Any] | None = None,
) -> list[str]:
    policy = policy or load_policy()
    rule = requirement_policy(policy, workflow_type, requirement_type)
    if rule is None:
        return [f"no compliance source policy for workflow {workflow_type}"]
    errors: list[str] = []
    source_kind = clean(citation.get("source_kind"))
    allowed = {clean(item) for item in rule.get("allowed_source_kinds", [])}
    if source_kind not in allowed:
        errors.append(f"source_kind {source_kind or '<blank>'} is not allowed for {workflow_type}/{requirement_type}")
    if citation.get("primary_source") is not True:
        errors.append("primary_source must be true")
    source_date = parse_date(citation.get("source_date"))
    if source_date is None:
        errors.append("source_date must be ISO date")
    else:
        generated_date = parse_generated_date(generated_at)
        if source_date > generated_date:
            errors.append("source_date cannot be after generated_at")
        age_days = (generated_date - source_date).days
        max_age = int(rule.get("max_age_days"))
        if age_days > max_age:
            errors.append(f"source_date is stale by policy: {age_days} days old, max {max_age}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", default=str(DEFAULT_POLICY_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors = validate_policy(load_policy(Path(args.policy)))
    payload = {"status": "PASS" if not errors else "FAIL", "errors": errors}
    print(json.dumps(payload, indent=2) if args.json else f"Compliance source policy: {payload['status']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
