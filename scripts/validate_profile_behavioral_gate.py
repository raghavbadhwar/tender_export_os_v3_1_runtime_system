#!/usr/bin/env python3
"""Validate that Hermes profile behavioral evaluation gates live work."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BEHAVIORAL_SPEC = PROJECT_ROOT / "config" / "hermes_behavioral_eval.yaml"
DEFAULT_PROFILE_REGISTRY = PROJECT_ROOT / "config" / "hermes_specialist_profiles.yaml"
REQUIRED_TYPES = {
    "ROUTINE",
    "AMBIGUOUS",
    "FAILURE",
    "INTEGRATION",
    "PROMPT_INJECTION",
    "MISSING_EVIDENCE",
    "OUT_OF_SCOPE",
}


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def validate_behavioral_gate(spec: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    execution = spec.get("execution") if isinstance(spec.get("execution"), dict) else {}
    gate = spec.get("live_work_gate") if isinstance(spec.get("live_work_gate"), dict) else {}
    scope = spec.get("profile_scope") if isinstance(spec.get("profile_scope"), dict) else {}
    scenarios = spec.get("scenarios") if isinstance(spec.get("scenarios"), list) else []
    owner_profile = str(registry.get("owner_profile") or "").strip()
    specialist_profiles = [str(value).strip() for value in registry.get("specialist_profiles") or [] if str(value).strip()]
    scoped_profiles = ([owner_profile] if scope.get("include_owner_profile") and owner_profile else []) + (
        specialist_profiles if scope.get("include_specialist_profiles") else []
    )
    scoped_profiles = list(dict.fromkeys(scoped_profiles))

    if gate.get("applies_to_every_profile_in_scope") is not True:
        errors.append("live_work_gate.applies_to_every_profile_in_scope must be true")
    if gate.get("live_work_requires_pass") is not True:
        errors.append("live_work_gate.live_work_requires_pass must be true")
    if gate.get("required_repeats") != 3 or execution.get("repeats") != gate.get("required_repeats"):
        errors.append("execution.repeats and live_work_gate.required_repeats must both be 3")
    if float(gate.get("minimum_case_pass_rate", 0)) != 1.0:
        errors.append("live_work_gate.minimum_case_pass_rate must be 1.0")
    if float(gate.get("critical_scenario_pass_rate", 0)) != 1.0:
        errors.append("live_work_gate.critical_scenario_pass_rate must be 1.0")
    if scope.get("live_work_default") != "SHADOW_ONLY_UNTIL_GATE_PASS":
        errors.append("profile_scope.live_work_default must be SHADOW_ONLY_UNTIL_GATE_PASS")
    if not scoped_profiles:
        errors.append("profile_scope must include owner and specialist profiles")

    registered_profiles = set(registry.get("profiles") or {})
    missing_registered = sorted(profile for profile in scoped_profiles if profile not in registered_profiles)
    if missing_registered:
        errors.append(f"scoped profiles missing from registry profiles: {', '.join(missing_registered)}")

    required_types = set(gate.get("required_scenario_types") or [])
    missing_gate_types = sorted(REQUIRED_TYPES - required_types)
    if missing_gate_types:
        errors.append(f"live_work_gate.required_scenario_types missing: {', '.join(missing_gate_types)}")

    scenario_types = {str(row.get("scenario_type") or "").strip() for row in scenarios if isinstance(row, dict)}
    missing_scenario_types = sorted(REQUIRED_TYPES - scenario_types)
    if missing_scenario_types:
        errors.append(f"scenarios missing required scenario types: {', '.join(missing_scenario_types)}")

    noncritical = [
        str(row.get("scenario_id") or f"scenario[{index}]")
        for index, row in enumerate(scenarios)
        if isinstance(row, dict) and row.get("critical") is not True
    ]
    if noncritical:
        errors.append(f"all gate scenarios must be critical: {', '.join(noncritical)}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "profile_count": len(scoped_profiles),
        "profiles": scoped_profiles,
        "required_repeats": gate.get("required_repeats"),
        "critical_scenario_pass_rate": gate.get("critical_scenario_pass_rate"),
        "required_scenario_types": sorted(REQUIRED_TYPES),
        "covered_scenario_types": sorted(scenario_types & REQUIRED_TYPES),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--behavioral-spec", default=str(DEFAULT_BEHAVIORAL_SPEC))
    parser.add_argument("--profile-registry", default=str(DEFAULT_PROFILE_REGISTRY))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = validate_behavioral_gate(
        load_yaml(Path(args.behavioral_spec).expanduser()),
        load_yaml(Path(args.profile_registry).expanduser()),
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Profile behavioral gate {result['status']}: {result['profile_count']} profiles")
        for error in result["errors"]:
            print(f"- {error}", file=sys.stderr)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
