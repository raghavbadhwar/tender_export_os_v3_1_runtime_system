#!/usr/bin/env python3
"""Validate numerical infrastructure scale gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "infrastructure_scale_gates.yaml"
REQUIRED_GATES = {
    "postgres",
    "temporal",
    "external_vector_memory",
    "langfuse",
    "paid_extraction_or_cloud_browser",
}


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def validate_scale_gates(config: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if config.get("default_decision") != "KEEP_OFF_UNTIL_MEASURED_TRIGGER_AND_OWNER_APPROVAL":
        errors.append("default_decision must keep infrastructure off until measured trigger and owner approval")
    if config.get("owner_approval_required") is not True:
        errors.append("owner_approval_required must be true")
    gates = config.get("gates") if isinstance(config.get("gates"), dict) else {}
    missing = sorted(REQUIRED_GATES - set(gates))
    if missing:
        errors.append(f"missing gates: {', '.join(missing)}")
    for gate_name, gate in gates.items():
        if not isinstance(gate, dict):
            errors.append(f"{gate_name} must be a mapping")
            continue
        if gate.get("current_state") != "OFF":
            errors.append(f"{gate_name}.current_state must be OFF")
        triggers = gate.get("adopt_only_after")
        if not isinstance(triggers, list) or not triggers:
            errors.append(f"{gate_name}.adopt_only_after must contain measured triggers")
            continue
        for index, trigger in enumerate(triggers):
            if not isinstance(trigger, dict):
                errors.append(f"{gate_name}.adopt_only_after[{index}] must be a mapping")
                continue
            for field in ("metric", "operator", "threshold", "window"):
                if trigger.get(field) in ("", None):
                    errors.append(f"{gate_name}.adopt_only_after[{index}].{field} is required")
    requirements = set(config.get("activation_requirements") or [])
    for required in ("measured trigger evidence path", "owner approval receipt", "rollback plan", "test plan"):
        if required not in requirements:
            errors.append(f"activation_requirements missing: {required}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "gate_count": len(gates),
        "required_gates": sorted(REQUIRED_GATES),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_scale_gates(load_config(Path(args.config).expanduser()))
    print(json.dumps(result, indent=2) if args.json else f"Infrastructure scale gates {result['status']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
