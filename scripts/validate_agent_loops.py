#!/usr/bin/env python3
"""
validate_agent_loops.py

Validates the Tender + Export OS agent loop registry.

Usage:
    python scripts/validate_agent_loops.py
    python scripts/validate_agent_loops.py --path config/agent_loops.json
"""

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = PROJECT_ROOT / "config" / "agent_loops.json"

REQUIRED_TOP_LEVEL_KEYS = {
    "spec_version",
    "date",
    "agent_name",
    "sources_used",
    "requirements_snapshot",
    "global_test_suite",
    "loops",
}

REQUIRED_REQUIREMENTS_KEYS = {
    "objective",
    "primary_user",
    "stakeholders",
    "inputs",
    "data_sources",
    "tools_allowed",
    "tools_forbidden",
    "side_effects",
    "approval_gates",
    "outputs",
    "success_metrics",
    "constraints",
    "privacy_level",
    "autonomy_level",
    "stop_conditions",
    "failure_modes",
    "assumptions",
}

REQUIRED_LOOP_KEYS = {
    "loop_name",
    "loop_level",
    "architecture",
    "roles",
    "state_schema",
    "memory_policy",
    "tool_registry",
    "prompts",
    "guardrails",
    "approval_policy",
    "execution_flow",
    "retry_policy",
    "stop_conditions",
    "evaluation_plan",
    "test_cases",
    "observability",
    "handoff_bundle",
}

REQUIRED_PROMPTS = {
    "orchestrator_system",
    "elicitor",
    "planner_architect",
    "executor",
    "critic",
    "packager",
}

REQUIRED_RETRY_KEYS = {
    "max_iterations",
    "per_step_timeout_minutes",
    "overall_timeout_minutes",
    "retryable_errors",
    "non_retryable_errors",
    "failure_handoff",
}

REQUIRED_GLOBAL_TEST_COVERAGE = {
    "happy path",
    "ambiguous requirement",
    "missing tool/data",
    "wrong tool call",
    "prompt injection",
    "risky side effect",
    "no-progress/retry exhaustion",
    "success-condition validation",
    "final handoff completeness",
}

HIGH_RISK_ACTIONS = {
    "send_buyer_rfq_reply",
    "send_export_quotation",
    "submit_tender_bid",
    "upload_tender_documents",
    "commit_final_price",
    "commit_delivery_timeline",
    "accept_payment_terms",
    "confirm_hsn_itchs_classification",
    "claim_country_of_origin",
    "pay_emd_or_bid_security",
    "pay_security_deposit",
    "pay_advance_to_supplier",
    "place_supplier_purchase_order",
    "use_dsc",
}


def is_non_empty(value):
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return True


def validate_required_keys(errors, location, obj, required_keys):
    missing = sorted(required_keys - set(obj.keys()))
    for key in missing:
        errors.append(f"{location}: missing required key '{key}'")

    for key in sorted(required_keys & set(obj.keys())):
        if not is_non_empty(obj[key]):
            errors.append(f"{location}: key '{key}' must not be empty")


def validate_global_tests(errors, registry):
    tests = registry.get("global_test_suite", [])
    covered = {test.get("covers") for test in tests if isinstance(test, dict)}
    missing = sorted(REQUIRED_GLOBAL_TEST_COVERAGE - covered)
    for item in missing:
        errors.append(f"global_test_suite: missing coverage for '{item}'")


def validate_loop(errors, loop, index):
    location = f"loops[{index}]"
    validate_required_keys(errors, location, loop, REQUIRED_LOOP_KEYS)

    loop_name = loop.get("loop_name", f"index_{index}")

    prompts = loop.get("prompts", {})
    if isinstance(prompts, dict):
        validate_required_keys(errors, f"{loop_name}.prompts", prompts, REQUIRED_PROMPTS)
    else:
        errors.append(f"{loop_name}.prompts: must be an object")

    retry_policy = loop.get("retry_policy", {})
    if isinstance(retry_policy, dict):
        validate_required_keys(errors, f"{loop_name}.retry_policy", retry_policy, REQUIRED_RETRY_KEYS)
        max_iterations = retry_policy.get("max_iterations")
        overall_timeout = retry_policy.get("overall_timeout_minutes")
        if not isinstance(max_iterations, int) or max_iterations < 1:
            errors.append(f"{loop_name}.retry_policy.max_iterations: must be a positive integer")
        if not isinstance(overall_timeout, int) or overall_timeout < 1:
            errors.append(f"{loop_name}.retry_policy.overall_timeout_minutes: must be a positive integer")
    else:
        errors.append(f"{loop_name}.retry_policy: must be an object")

    approval_policy = loop.get("approval_policy", {})
    if isinstance(approval_policy, dict):
        actions = set(approval_policy.get("approval_required_actions", []))
        risky_actions = actions & HIGH_RISK_ACTIONS
        if risky_actions and approval_policy.get("halt_on_gate") is not True:
            errors.append(f"{loop_name}.approval_policy: high-risk actions require halt_on_gate=true")
        if approval_policy.get("source") != "config/approval_policy.yaml":
            errors.append(f"{loop_name}.approval_policy: source must be config/approval_policy.yaml")
    else:
        errors.append(f"{loop_name}.approval_policy: must be an object")

    evaluation_plan = loop.get("evaluation_plan", {})
    if isinstance(evaluation_plan, dict):
        if evaluation_plan.get("pass_threshold", 0) < 85:
            errors.append(f"{loop_name}.evaluation_plan.pass_threshold: must be at least 85")
        if evaluation_plan.get("side_effect_safety_required") is not True:
            errors.append(f"{loop_name}.evaluation_plan.side_effect_safety_required: must be true")
    else:
        errors.append(f"{loop_name}.evaluation_plan: must be an object")

    if len(loop.get("test_cases", [])) < 3:
        errors.append(f"{loop_name}.test_cases: must include at least 3 loop-specific tests")


def validate_registry(registry):
    errors = []
    validate_required_keys(errors, "registry", registry, REQUIRED_TOP_LEVEL_KEYS)

    requirements = registry.get("requirements_snapshot", {})
    if isinstance(requirements, dict):
        validate_required_keys(errors, "requirements_snapshot", requirements, REQUIRED_REQUIREMENTS_KEYS)
    else:
        errors.append("requirements_snapshot: must be an object")

    validate_global_tests(errors, registry)

    loops = registry.get("loops", [])
    if not isinstance(loops, list):
        errors.append("loops: must be a list")
    elif not loops:
        errors.append("loops: must contain at least one loop")
    else:
        names = []
        for index, loop in enumerate(loops):
            if not isinstance(loop, dict):
                errors.append(f"loops[{index}]: must be an object")
                continue
            names.append(loop.get("loop_name"))
            validate_loop(errors, loop, index)
        duplicates = sorted({name for name in names if names.count(name) > 1})
        for name in duplicates:
            errors.append(f"loops: duplicate loop_name '{name}'")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate Tender + Export OS agent loop registry")
    parser.add_argument("--path", default=str(DEFAULT_REGISTRY), help="Path to agent_loops.json")
    args = parser.parse_args()

    registry_path = Path(args.path)
    if not registry_path.is_absolute():
        registry_path = PROJECT_ROOT / registry_path

    try:
        with registry_path.open("r", encoding="utf-8") as f:
            registry = json.load(f)
    except FileNotFoundError:
        print(f"FAIL: registry not found: {registry_path}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return 1

    errors = validate_registry(registry)
    if errors:
        print("FAIL: agent loop registry has validation errors")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"PASS: {registry_path}")
    print(f"Loops validated: {len(registry.get('loops', []))}")
    print(f"Global tests validated: {len(registry.get('global_test_suite', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
