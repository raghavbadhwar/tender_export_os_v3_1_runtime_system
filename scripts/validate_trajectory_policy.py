#!/usr/bin/env python3
"""Validate privacy-controlled trajectory policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = PROJECT_ROOT / "config" / "trajectory_policy.yaml"
REQUIRED_EXCLUSIONS = {
    "raw_prompt",
    "raw_document_text",
    "email_body",
    "password",
    "token",
    "cookie",
    "session",
    "dsc",
    "bank_details",
    "private_browser_content",
}
REQUIRED_ALLOWED = {"task_id", "tool_names", "decision_ids", "outcome_ids", "evaluator_scores"}


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("trajectory policy must be a mapping")
    return value


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    capture = policy.get("trajectory_capture", {})
    rl = policy.get("rl_training", {})
    retention = policy.get("retention", {})
    allowed = set(capture.get("allowed_fields", []))
    excluded = set(capture.get("excluded_fields", []))
    if not REQUIRED_ALLOWED <= allowed:
        errors.append(f"allowed_fields missing: {sorted(REQUIRED_ALLOWED - allowed)}")
    if not REQUIRED_EXCLUSIONS <= excluded:
        errors.append(f"excluded_fields missing: {sorted(REQUIRED_EXCLUSIONS - excluded)}")
    overlap = allowed & excluded
    if overlap:
        errors.append(f"allowed_fields overlap excluded_fields: {sorted(overlap)}")
    if rl.get("enabled") is not False:
        errors.append("rl_training.enabled must remain false until approved training design exists")
    if rl.get("approved_training_design_required") is not True:
        errors.append("approved_training_design_required must be true")
    if retention.get("raw_sensitive_content_retention_days") != 0:
        errors.append("raw sensitive content retention must be 0 days")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors = validate_policy(load_policy(Path(args.policy)))
    payload = {"status": "PASS" if not errors else "FAIL", "errors": errors}
    print(json.dumps(payload, indent=2) if args.json else f"Trajectory policy: {payload['status']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
