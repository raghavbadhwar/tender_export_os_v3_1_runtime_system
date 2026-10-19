#!/usr/bin/env python3
"""Evaluate browser-evidence boundary behavior for the browser-capable profiles.

The evaluator is deterministic by design: it verifies the behavior contract
without visiting a live site or writing raw source evidence.  Live capture is
separately controlled by the read-only browser and static-scraper lanes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.agent_browser_capture import DEFAULT_OUTPUT_ROOT as BROWSER_OUTPUT_ROOT
from scripts.agent_browser_capture import READ_ONLY_COMMANDS, blocker_status, public_hostname
from scripts.public_web_evidence_scraper import DEFAULT_OUTPUT_ROOT as STATIC_OUTPUT_ROOT
from scripts.public_web_evidence_scraper import body_sha256, same_public_host


DEFAULT_SPEC = PROJECT_ROOT / "config" / "browser_boundary_eval.yaml"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "browser_boundary_eval"
REQUIRED_BOUNDARIES = {
    "robots_denial",
    "captcha",
    "login_wall",
    "prompt_injection",
    "redirect",
    "duplicate_content",
    "javascript_rendered",
    "paywall",
    "unreachable_source",
    "source_text_conflict",
}


def load_spec(path: Path = DEFAULT_SPEC) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"browser boundary spec must be a mapping: {path}")
    return value


def resolve_path(value: str | Path, project_root: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else project_root / path


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def load_profile_registry(spec: dict[str, Any], project_root: Path) -> dict[str, Any]:
    path = resolve_path(str(spec.get("profile_registry") or "config/hermes_specialist_profiles.yaml"), project_root)
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return value if isinstance(value, dict) else {}


def validate_spec(spec: dict[str, Any], *, project_root: Path = PROJECT_ROOT) -> list[str]:
    errors: list[str] = []
    scenarios = spec.get("scenarios")
    profiles = spec.get("profiles")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenarios must be a non-empty list")
        scenarios = []
    if not isinstance(profiles, list) or not profiles:
        errors.append("profiles must be a non-empty list")
        profiles = []
    boundaries = [str(item.get("boundary") or "") for item in scenarios if isinstance(item, dict)]
    missing = sorted(REQUIRED_BOUNDARIES - set(boundaries))
    extra = sorted(set(boundaries) - REQUIRED_BOUNDARIES)
    if missing:
        errors.append(f"missing required boundaries: {', '.join(missing)}")
    if extra:
        errors.append(f"unsupported boundaries: {', '.join(extra)}")
    if len(boundaries) != len(set(boundaries)):
        errors.append("boundary scenarios must be unique")
    if any(not str(item.get("scenario_id") or "") for item in scenarios if isinstance(item, dict)):
        errors.append("every scenario requires scenario_id")
    if any(not str(item.get("expected_status") or "") for item in scenarios if isinstance(item, dict)):
        errors.append("every scenario requires expected_status")
    policy = spec.get("policy") if isinstance(spec.get("policy"), dict) else {}
    if policy.get("external_actions_executed") is not False:
        errors.append("policy.external_actions_executed must be false")
    if policy.get("raw_evidence_outside_private_root") is not False:
        errors.append("policy.raw_evidence_outside_private_root must be false")
    private_root = resolve_path(str(spec.get("private_evidence_root") or "outputs/evidence/private"), project_root)
    if not inside(BROWSER_OUTPUT_ROOT, private_root) or not inside(STATIC_OUTPUT_ROOT, private_root):
        errors.append("browser and static raw evidence defaults must stay under private_evidence_root")
    registry = load_profile_registry(spec, project_root)
    known = registry.get("profiles", {}) if isinstance(registry.get("profiles"), dict) else {}
    for profile in profiles:
        profile_spec = known.get(str(profile)) if isinstance(known, dict) else None
        if not isinstance(profile_spec, dict):
            errors.append(f"unknown evaluation profile: {profile}")
            continue
        allowed = set(profile_spec.get("allowed_toolsets") or [])
        forbidden = set(profile_spec.get("forbidden_toolsets") or [])
        mcp_tools = set(profile_spec.get("mcp_tools") or [])
        if {"browser", "terminal"} & allowed:
            errors.append(f"profile exposes unrestricted browser or terminal access: {profile}")
        if not {"browser", "terminal"}.issubset(forbidden):
            errors.append(f"profile must forbid browser and terminal access: {profile}")
        if "capture_public_web" not in mcp_tools:
            errors.append(f"profile lacks governed public-web capture: {profile}")
    return errors


def evaluate_boundary(scenario: dict[str, Any]) -> dict[str, Any]:
    boundary = str(scenario.get("boundary") or "")
    fixture = scenario.get("fixture") if isinstance(scenario.get("fixture"), dict) else {}
    expected = str(scenario.get("expected_status") or "")
    observed = "UNSUPPORTED"
    evidence: dict[str, Any] = {}
    if boundary == "robots_denial":
        observed = "ROBOTS_ALLOWED" if fixture.get("robots_allowed") else "ROBOTS_BLOCKED"
    elif boundary == "captcha":
        markers = blocker_status(str(fixture.get("page_text") or ""))
        observed = "CAPTCHA_BLOCKED" if "CAPTCHA_BLOCKED" in markers else "NOT_DETECTED"
        evidence["blockers"] = markers
    elif boundary == "login_wall":
        markers = blocker_status(str(fixture.get("page_text") or ""))
        observed = "MANUAL_LOGIN_REQUIRED" if "MANUAL_LOGIN_REQUIRED" in markers else "NOT_DETECTED"
        evidence["blockers"] = markers
    elif boundary == "prompt_injection":
        markers = blocker_status(str(fixture.get("page_text") or ""))
        observed = "UNTRUSTED_SOURCE_INSTRUCTION" if "PROMPT_INJECTION_DETECTED" in markers else "NOT_DETECTED"
        evidence["blockers"] = markers
    elif boundary == "redirect":
        seed = str(fixture.get("seed_url") or "")
        final = str(fixture.get("final_url") or "")
        try:
            host = public_hostname(seed, resolve_dns=False)
            observed = "REDIRECT_ALLOWED" if same_public_host(final, host, resolve_dns=False) else "REDIRECT_BLOCKED"
        except ValueError:
            observed = "REDIRECT_BLOCKED"
    elif boundary == "duplicate_content":
        first = str(fixture.get("first_body") or "").encode("utf-8")
        second = str(fixture.get("second_body") or "").encode("utf-8")
        evidence["first_sha256"] = body_sha256(first)
        evidence["second_sha256"] = body_sha256(second)
        observed = "DUPLICATE_CONTENT" if evidence["first_sha256"] == evidence["second_sha256"] else "DISTINCT_CONTENT"
    elif boundary == "javascript_rendered":
        commands = {str(value) for value in fixture.get("commands", [])}
        prohibited = commands - READ_ONLY_COMMANDS
        evidence["commands"] = sorted(commands)
        observed = "JS_EVIDENCE_READ_ONLY" if commands and not prohibited else "JS_COMMAND_POLICY_FAILED"
    elif boundary == "paywall":
        markers = blocker_status(str(fixture.get("page_text") or ""))
        observed = "PAYWALL_BLOCKED" if "PAYWALL_BLOCKED" in markers else "NOT_DETECTED"
        evidence["blockers"] = markers
    elif boundary == "unreachable_source":
        observed = "UNREACHABLE_SOURCE" if str(fixture.get("error") or "").strip() else "REACHABLE_OR_UNKNOWN"
    elif boundary == "source_text_conflict":
        left = " ".join(str(fixture.get("structured_value") or "").casefold().split())
        right = " ".join(str(fixture.get("source_text_value") or "").casefold().split())
        observed = "SOURCE_TEXT_CONFLICT" if left and right and left != right else "SOURCE_TEXT_ALIGNED"
    return {
        "scenario_id": str(scenario.get("scenario_id") or ""),
        "boundary": boundary,
        "expected_status": expected,
        "observed_status": observed,
        "status": "PASS" if observed == expected else "FAIL",
        "evidence": evidence,
        "external_actions_executed": False,
    }


def evaluate(spec: dict[str, Any], *, project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validation_errors = validate_spec(spec, project_root=project_root)
    scenario_results = [evaluate_boundary(item) for item in spec.get("scenarios", []) if isinstance(item, dict)]
    registry = load_profile_registry(spec, project_root)
    profile_specs = registry.get("profiles", {}) if isinstance(registry.get("profiles"), dict) else {}
    profile_results: list[dict[str, Any]] = []
    for profile in spec.get("profiles", []):
        profile_spec = profile_specs.get(str(profile), {}) if isinstance(profile_specs, dict) else {}
        allowed_toolsets = set(profile_spec.get("allowed_toolsets") or [])
        forbidden_toolsets = set(profile_spec.get("forbidden_toolsets") or [])
        mcp_tools = set(profile_spec.get("mcp_tools") or [])
        read_only_capture_enforced = (
            not ({"browser", "terminal"} & allowed_toolsets)
            and {"browser", "terminal"}.issubset(forbidden_toolsets)
            and "capture_public_web" in mcp_tools
        )
        for scenario in scenario_results:
            passed = scenario["status"] == "PASS" and read_only_capture_enforced
            profile_results.append(
                {
                    "profile": str(profile),
                    "scenario_id": scenario["scenario_id"],
                    "boundary": scenario["boundary"],
                    "status": "PASS" if passed else "FAIL",
                    "read_only_capture_enforced": read_only_capture_enforced,
                    "external_actions_executed": False,
                }
            )
    status = "PASS" if not validation_errors and all(item["status"] == "PASS" for item in scenario_results + profile_results) else "FAIL"
    return {
        "status": status,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "validation_errors": validation_errors,
        "scenario_results": scenario_results,
        "profile_results": profile_results,
        "private_evidence_root": str(resolve_path(str(spec.get("private_evidence_root") or "outputs/evidence/private"), project_root)),
        "raw_evidence_written": False,
        "external_actions_executed": False,
        "safety": "Deterministic boundary evaluation only; no web access, browser commands, register writes, or external actions executed.",
    }


def write_report(report: dict[str, Any], output_root: Path) -> Path:
    run_id = "BROWSER-EVAL-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output_dir = output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    path = output_dir / "report.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", default=str(DEFAULT_SPEC))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    spec_path = resolve_path(args.spec, PROJECT_ROOT)
    spec = load_spec(spec_path)
    report = evaluate(spec)
    if args.validate_only:
        payload = {"status": report["status"], "validation_errors": report["validation_errors"], "raw_evidence_written": False}
    else:
        output_root = resolve_path(args.output_root, PROJECT_ROOT)
        path = write_report(report, output_root)
        payload = {"status": report["status"], "report": str(path), "raw_evidence_written": False}
    print(json.dumps(payload, indent=2) if args.json else f"Browser boundary evaluation: {payload}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
