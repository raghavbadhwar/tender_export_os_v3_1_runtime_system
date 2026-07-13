#!/usr/bin/env python3
"""Select and validate the Tender OS research/capture execution route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIGS = [
    PROJECT_ROOT / "config" / "research_capture_routing.yaml",
    PROJECT_ROOT / "config" / "public_web_scraping.yaml",
    PROJECT_ROOT / "config" / "agent_browser_research.yaml",
    PROJECT_ROOT / "config" / "deep_source_runtime.yaml",
]

CODEX_TASKS = {
    "pdf_boq_parsing",
    "document_parsing",
    "spreadsheet_parsing",
    "artifact_generation",
    "bid_pack",
    "quote_pack",
    "document_diff_render",
}
HERMES_TASKS = {
    "approval_routing",
    "kanban_coordination",
    "owner_brief",
    "specialist_review",
    "exception_routing",
}


def _base(route: str) -> dict[str, Any]:
    return {
        "route": route,
        "status": "ROUTED",
        "mode": "INTERNAL_ONLY",
        "may_mutate_registers": False,
        "external_actions_allowed": False,
        "owner_approval_required": False,
        "operational_evidence_required_before_case_progression": True,
        "escalation_label": "",
    }


def select_route(
    task_type: str,
    source_known: bool,
    login_required: bool,
    repetition_needed: bool,
) -> dict[str, Any]:
    """Route by epistemic need and access boundary, never by tool prestige."""
    task = str(task_type or "").strip().lower()
    if task in HERMES_TASKS:
        return _base("hermes_control_plane") | {
            "mode": "ROUTING_AND_REVIEW",
            "operational_evidence_required_before_case_progression": False,
        }
    if task in CODEX_TASKS:
        return _base("codex_artifact_runtime") | {
            "mode": "LOCAL_DOCUMENT_OR_ARTIFACT",
            "operational_evidence_required_before_case_progression": False,
        }
    if login_required:
        return _base("python_playwright_manual_session") | {
            "status": "NEEDS_INPUT",
            "mode": "OWNER_AUTHORIZED_MANUAL_LOGIN",
            "owner_approval_required": True,
            "escalation_label": "MANUAL_LOGIN_REQUIRED",
        }
    if not source_known:
        return _base("chatgpt_deep_research") | {
            "mode": "BROAD_DISCOVERY_ADVISORY",
            "may_mutate_registers": False,
        }
    if repetition_needed or source_known:
        return _base("python_playwright_agent_browser") | {
            "mode": "READ_ONLY_PUBLIC_EVIDENCE",
        }
    return _base("hermes_control_plane") | {"mode": "ROUTE_CLARIFICATION"}


def validate_route_configs(paths: Iterable[Path] = DEFAULT_CONFIGS) -> dict[str, Any]:
    path_list = list(paths)
    contracts: list[tuple[str, dict[str, Any]]] = []
    errors: list[str] = []
    for path in path_list:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        contract = data.get("shared_contract")
        if not isinstance(contract, dict):
            errors.append(f"{path.name}: shared_contract is missing")
            continue
        contracts.append((path.name, contract))
    canonical = contracts[0][1] if contracts else {}
    for name, contract in contracts[1:]:
        if contract != canonical:
            errors.append(f"{name}: shared_contract differs from {contracts[0][0]}")
    evidence = canonical.get("evidence") if isinstance(canonical.get("evidence"), dict) else {}
    boundaries = canonical.get("access_boundaries") if isinstance(canonical.get("access_boundaries"), dict) else {}
    limits = canonical.get("hard_limits") if isinstance(canonical.get("hard_limits"), dict) else {}
    labels = canonical.get("escalation_labels") if isinstance(canonical.get("escalation_labels"), dict) else {}
    if boundaries and any(boundaries.get(key) is not False for key in ("captcha_bypass", "login_bypass", "paywall_bypass", "external_actions")):
        errors.append("shared access boundaries must fail closed for bypasses and external actions")
    expected_limits = {"max_pages": 50, "max_depth": 3, "timeout_seconds": 120, "max_file_size_mb": 100}
    if limits and limits != expected_limits:
        errors.append(f"hard_limits must be {expected_limits}")
    return {
        "ok": not errors and len(contracts) == len(path_list),
        "errors": errors,
        "contract_version": canonical.get("version"),
        "evidence_root": evidence.get("private_root"),
        "redacted_root": evidence.get("redacted_root"),
        "hard_limits": limits,
        "access_boundaries": boundaries,
        "escalation_labels": sorted(set(str(value) for value in labels.values())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-type")
    parser.add_argument("--source-known", action="store_true")
    parser.add_argument("--login-required", action="store_true")
    parser.add_argument("--repetition-needed", action="store_true")
    parser.add_argument("--validate-configs", action="store_true")
    args = parser.parse_args()
    result = (
        validate_route_configs(DEFAULT_CONFIGS)
        if args.validate_configs
        else select_route(args.task_type or "", args.source_known, args.login_required, args.repetition_needed)
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
