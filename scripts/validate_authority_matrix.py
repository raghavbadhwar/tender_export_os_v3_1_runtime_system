#!/usr/bin/env python3
"""Validate the Level 6 authority matrix against live Tender OS policy registries.

The matrix is a constitutional cross-check, not an execution grant. It fails
closed when a tool policy, approval policy, or profile registry drifts away
from the declared authority and receipt contracts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = PROJECT_ROOT / "config" / "agent_authority_matrix.yaml"
DEFAULT_TOOL_POLICY = PROJECT_ROOT / "config" / "tender_tool_policy.yaml"
DEFAULT_APPROVAL_POLICY = PROJECT_ROOT / "config" / "approval_policy.yaml"
DEFAULT_PROFILES = PROJECT_ROOT / "config" / "hermes_specialist_profiles.yaml"

VALID_APPROVAL_MODES = {"not_required", "required", "prohibited"}
REQUIRED_CLASS_FIELDS = {
    "tier",
    "description",
    "external_effect",
    "approval_mode",
    "staging_profiles",
    "execution_profiles",
    "receipt_contract",
}


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return value if isinstance(value, dict) else {}


def _as_action_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value if str(item).strip()}


def approval_policy_actions(approval_policy: dict[str, Any]) -> set[str]:
    actions = {
        str(item)
        for item in approval_policy.get("standing_authorizations", {}).get(
            "hard_limits_still_requiring_specific_owner_approval", []
    )
    }
    for item in approval_policy.get("mode_b_approval_gated", {}).get("approval_required_for", []):
        if isinstance(item, dict) and str(item.get("action", "")).strip():
            actions.add(str(item["action"]))
    return actions


def validate_authority_matrix(
    matrix: dict[str, Any],
    tool_policy: dict[str, Any],
    approval_policy: dict[str, Any],
    profile_registry: dict[str, Any],
) -> list[str]:
    """Return deterministic validation findings; an empty list means PASS."""

    errors: list[str] = []
    classes = matrix.get("action_classes")
    mappings = matrix.get("policy_action_classes")
    tool_actions = tool_policy.get("actions")
    receipt_contracts = matrix.get("receipt_contracts")

    if not isinstance(classes, dict):
        return ["action_classes must be an object"]
    if not isinstance(mappings, dict):
        return ["policy_action_classes must be an object"]
    if not isinstance(tool_actions, dict):
        return ["tender tool policy actions must be an object"]
    if not isinstance(receipt_contracts, dict):
        return ["receipt_contracts must be an object"]

    known_profiles = {str(profile_registry.get("owner_profile", ""))}
    known_profiles.update(str(item) for item in profile_registry.get("specialist_profiles", []) if str(item).strip())
    known_profiles.discard("")
    known_profiles.add("owner")

    for class_name, spec in classes.items():
        if not isinstance(spec, dict):
            errors.append(f"action class {class_name!r} must be an object")
            continue
        missing = sorted(REQUIRED_CLASS_FIELDS - set(spec))
        if missing:
            errors.append(f"action class {class_name!r} missing fields: {missing}")
        mode = spec.get("approval_mode")
        if mode not in VALID_APPROVAL_MODES:
            errors.append(f"action class {class_name!r} has invalid approval_mode: {mode!r}")
        if not isinstance(spec.get("tier"), int) or not 0 <= spec.get("tier", -1) <= 5:
            errors.append(f"action class {class_name!r} tier must be an integer from 0 to 5")
        if not isinstance(spec.get("external_effect"), bool):
            errors.append(f"action class {class_name!r} external_effect must be boolean")
        if spec.get("external_effect") and mode != "required":
            errors.append(f"action class {class_name!r} with external_effect=true must require approval")
        if mode == "prohibited" and spec.get("execution_profiles"):
            errors.append(f"prohibited action class {class_name!r} cannot have execution_profiles")
        for field in ("staging_profiles", "execution_profiles"):
            values = spec.get(field, [])
            if not isinstance(values, list):
                errors.append(f"action class {class_name!r} {field} must be a list")
                continue
            unknown = sorted(set(str(value) for value in values) - known_profiles)
            if unknown:
                errors.append(f"action class {class_name!r} has unknown {field}: {unknown}")
        receipt_contract = spec.get("receipt_contract")
        if receipt_contract not in receipt_contracts:
            errors.append(f"action class {class_name!r} references unknown receipt contract {receipt_contract!r}")

    tool_names = set(str(key) for key in tool_actions)
    mapping_names = set(str(key) for key in mappings)
    for missing in sorted(tool_names - mapping_names):
        errors.append(f"tool policy action missing authority mapping: {missing}")
    for extra in sorted(mapping_names - tool_names):
        errors.append(f"authority mapping is not present in tool policy: {extra}")

    prohibited_policy_actions = {
        action for action, spec in tool_actions.items() if isinstance(spec, dict) and spec.get("prohibited") is True
    }
    declared_prohibited = _as_action_set(matrix.get("prohibited_actions"))
    if prohibited_policy_actions != declared_prohibited:
        errors.append(
            "prohibited_actions drift: "
            f"policy_only={sorted(prohibited_policy_actions - declared_prohibited)}, "
            f"matrix_only={sorted(declared_prohibited - prohibited_policy_actions)}"
        )

    for action in sorted(tool_names & mapping_names):
        class_name = str(mappings[action])
        if class_name not in classes:
            errors.append(f"{action}: authority mapping references unknown class {class_name!r}")
            continue
        class_spec = classes[class_name]
        policy_spec = tool_actions[action] if isinstance(tool_actions[action], dict) else {}
        if policy_spec.get("prohibited") is True:
            if class_spec.get("approval_mode") != "prohibited":
                errors.append(f"{action}: prohibited tool action must map to approval_mode=prohibited")
            continue
        if class_spec.get("tier") != policy_spec.get("tier"):
            errors.append(f"{action}: matrix tier {class_spec.get('tier')} != tool policy tier {policy_spec.get('tier')}")
        if class_spec.get("external_effect") != bool(policy_spec.get("external_effect", False)):
            errors.append(
                f"{action}: matrix external_effect={class_spec.get('external_effect')} "
                f"!= tool policy external_effect={bool(policy_spec.get('external_effect', False))}"
            )
        if class_spec.get("approval_mode") == "required" and not bool(policy_spec.get("approval_required", False)):
            errors.append(f"{action}: matrix requires approval but tool policy does not")
        if class_spec.get("approval_mode") == "not_required" and bool(policy_spec.get("approval_required", False)):
            errors.append(f"{action}: tool policy requires approval but matrix does not")

    hard_limit_actions = approval_policy_actions(approval_policy)
    declared_approval_actions = _as_action_set(matrix.get("approval_required_actions"))
    missing_hard_limits = sorted(hard_limit_actions - declared_approval_actions)
    if missing_hard_limits:
        errors.append(f"approval_required_actions missing approval-policy hard limits: {missing_hard_limits}")

    autopilot_actions = _as_action_set(
        approval_policy.get("mode_a_autopilot", {}).get("allowed_actions", [])
    )
    overlap = sorted(declared_approval_actions & autopilot_actions)
    if overlap:
        errors.append(f"actions cannot be both autopilot and approval-required: {overlap}")

    for action in sorted(declared_approval_actions):
        class_name = mappings.get(action)
        if class_name is None:
            errors.append(f"approval-required action missing authority mapping: {action}")
            continue
        class_spec = classes.get(class_name, {})
        if class_spec.get("approval_mode") != "required":
            errors.append(f"{action}: approval-required action maps to {class_name!r}, not approval_mode=required")

    if matrix.get("default_policy") != "deny":
        errors.append("default_policy must remain deny")
    if matrix.get("external_actions_default") is not False:
        errors.append("external_actions_default must remain false")

    for contract_name, contract in receipt_contracts.items():
        if not isinstance(contract, dict):
            errors.append(f"receipt contract {contract_name!r} must be an object")
            continue
        required = contract.get("required_fields")
        if not isinstance(required, list) or not required:
            errors.append(f"receipt contract {contract_name!r} must declare required_fields")
        if contract.get("external_actions_executed") is not False:
            errors.append(f"receipt contract {contract_name!r} must set external_actions_executed=false")

    return errors


def build_report(
    matrix: dict[str, Any],
    tool_policy: dict[str, Any],
    approval_policy: dict[str, Any],
    profile_registry: dict[str, Any],
) -> dict[str, Any]:
    errors = validate_authority_matrix(matrix, tool_policy, approval_policy, profile_registry)
    return {
        "schema_version": "authority_matrix_validation.v1",
        "status": "PASS" if not errors else "FAIL",
        "matrix_version": matrix.get("version"),
        "action_class_count": len(matrix.get("action_classes", {})),
        "mapped_policy_action_count": len(matrix.get("policy_action_classes", {})),
        "approval_required_action_count": len(matrix.get("approval_required_actions", [])),
        "prohibited_action_count": len(matrix.get("prohibited_actions", [])),
        "errors": errors,
        "external_actions_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Tender OS Level 6 authority matrix")
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--tool-policy", default=str(DEFAULT_TOOL_POLICY))
    parser.add_argument("--approval-policy", default=str(DEFAULT_APPROVAL_POLICY))
    parser.add_argument("--profiles", default=str(DEFAULT_PROFILES))
    parser.add_argument("--output", default="", help="Optional JSON validation receipt path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    matrix = load_yaml(Path(args.matrix))
    tool_policy = load_yaml(Path(args.tool_policy))
    approval_policy = load_yaml(Path(args.approval_policy))
    profile_registry = load_yaml(Path(args.profiles))
    report = build_report(matrix, tool_policy, approval_policy, profile_registry)
    if args.output:
        output = Path(args.output).expanduser()
        if not output.is_absolute():
            output = PROJECT_ROOT / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Authority matrix validation {report['status']}: {report['mapped_policy_action_count']} mapped actions")
        for error in report["errors"]:
            print(f"FAIL: {error}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
