#!/usr/bin/env python3
"""Validate structured completion payloads for bounded Hermes review tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "case_id",
    "evidence",
    "gate",
    "artifact_paths",
    "validator_receipt_path",
    "stop_reason",
    "retry_method",
    "smallest_safe_next_action",
)


def validate_completion(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    status = str(payload.get("status") or "").upper()
    if status not in {"DONE", "BLOCKED", "REQUIRES_APPROVAL"}:
        errors.append("status must be DONE, BLOCKED, or REQUIRES_APPROVAL")
    for field in REQUIRED_FIELDS:
        value = payload.get(field)
        if value is None or value == "" or value == []:
            errors.append(f"missing required completion field: {field}")
    if payload.get("evidence") and not isinstance(payload.get("evidence"), list):
        errors.append("evidence must be a list")
    artifact_paths = payload.get("artifact_paths")
    if artifact_paths and not isinstance(artifact_paths, list):
        errors.append("artifact_paths must be a list")
    if payload.get("approval_required") not in {True, False}:
        errors.append("approval_required must be boolean")
    if payload.get("external_actions_executed") is not False:
        errors.append("external_actions_executed must be false")
    if isinstance(artifact_paths, list):
        for path_value in artifact_paths:
            path = Path(str(path_value))
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"artifact missing or empty: {path}")
    validator_path_value = payload.get("validator_receipt_path")
    if validator_path_value:
        validator_path = Path(str(validator_path_value))
        if not validator_path.is_file() or validator_path.stat().st_size == 0:
            errors.append(f"validator receipt missing or empty: {validator_path}")
    return {
        "valid": not errors,
        "errors": errors,
        "external_actions_executed": False,
        "approval_required": payload.get("approval_required"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path)
    args = parser.parse_args(argv)
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    result = validate_completion(payload)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
