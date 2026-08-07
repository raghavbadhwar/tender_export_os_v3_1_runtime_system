#!/usr/bin/env python3
"""Render and optionally apply governed SOUL prompts from the profile registry.

Default mode is dry-run. ``--apply`` writes only profile ``SOUL.md`` files
after preserving the previous prompt in the run receipt directory. It never
copies or edits credentials, memory, cron, gateway state, skills, or business
registers.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "config" / "hermes_specialist_profiles.yaml"
DEFAULT_PROFILES_ROOT = Path.home() / ".hermes" / "profiles"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "profile_specialization"


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Profile registry must be a mapping: {path}")
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError(f"Profile registry has no profiles: {path}")
    return data


def load_profile_specs(path: Path = REGISTRY_PATH) -> dict[str, dict[str, Any]]:
    profiles = load_registry(path)["profiles"]
    if not all(isinstance(name, str) and isinstance(spec, dict) for name, spec in profiles.items()):
        raise ValueError(f"Every profile entry must be a mapping: {path}")
    return profiles


_REGISTRY = load_registry()
PROFILE_SPECS = load_profile_specs()
GLOBAL_GATES = list((_REGISTRY.get("global_policy") or {}).get("approval_gates") or [])


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bullet(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def render_soul(
    profile: str,
    spec: dict[str, Any],
    *,
    global_gates: list[str] | None = None,
) -> str:
    gates = list(GLOBAL_GATES if global_gates is None else global_gates)
    output_contract = spec.get("output_contract") or {}
    required_fields = output_contract.get("required_fields") or []
    memory_scope = spec.get("memory_scope") or {}
    return f"""# SOUL.md — {spec['title']}

## Operating Identity
Profile: `{profile}`

{spec['identity']}

This profile is a least-privilege Tender Export OS worker. It must stay inside
its registered lane, cite evidence, return structured completion, and stop at
approval gates. It is not a clone of the owner console.

## Durable Responsibility
{spec.get('durable_responsibility', '')}

## Owns
{bullet(list(spec.get('owns') or []))}

## Inputs
{bullet(list(spec.get('inputs') or []))}

## Outputs
{bullet(list(spec.get('outputs') or []))}

## Must Never
{bullet(list(spec.get('never') or []))}

## Stop Conditions
{bullet(list(spec.get('stop_conditions') or []))}

## Global Approval Gates
Never execute these without explicit owner approval and a matching receipt:
{bullet(gates)}

## Tool and Memory Boundary
- Allowed toolsets: {', '.join(spec.get('allowed_toolsets') or [])}
- Tender OS MCP tools: {', '.join(spec.get('mcp_tools') or [])}
- Memory namespace: {memory_scope.get('namespace', 'none')}
- External actions allowed: no

## Structured Completion Contract
Return JSON with these fields: {', '.join(required_fields)}.
`external_actions_executed` must be `false`.

## Hybrid Research and Capture Rule
- ChatGPT Deep Research owns broad discovery, market/category/source intelligence, reasoning, synthesis, and cited theses.
- Python, Playwright, agent-browser, and Codex own repeatable capture, owner-authorized evidence, document parsing, calculations, dedupe, projections, validation, tests, and artifacts.
- The repository event ledger owns canonical state, memory proposals, audit trail, registers, approvals, and evidence manifests.
- `PUBLIC_LISTING_ONLY` is a lead, never a bid-ready or demand-proven case.

## Routing Discipline
If work falls outside this profile's registered responsibility, return it to
`teos-orchestrator`, `tender-export-os`, or the named next profile. Do not
expand authority to cover another profile's lane.

## Safety Statement
Never fabricate documents, certifications, eligibility, buyer verification,
supplier claims, HSN/ITC-HS classification, origin, prices, delivery, payment,
or execution receipts.
"""


def canary_passes(profile: str, content: str) -> bool:
    lowered = content.lower()
    required = [
        profile.lower(),
        "operating identity",
        "must never",
        "global approval gates",
        "structured completion contract",
        "external actions allowed: no",
    ]
    return all(item in lowered for item in required)


def apply_specialist_souls(
    profiles_root: Path,
    output_root: Path,
    apply: bool = False,
    *,
    profile_specs: dict[str, dict[str, Any]] | None = None,
    global_gates: list[str] | None = None,
    selected_profiles: set[str] | None = None,
) -> dict[str, Any]:
    all_specs = PROFILE_SPECS if profile_specs is None else profile_specs
    unknown = sorted((selected_profiles or set()) - set(all_specs))
    if unknown:
        raise ValueError(f"Unknown profile selection: {', '.join(unknown)}")
    specs = {
        name: spec
        for name, spec in all_specs.items()
        if selected_profiles is None or name in selected_profiles
    }
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = output_root / f"profile_specialization_{now_stamp()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = run_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    new_hashes: list[str] = []
    for profile, spec in specs.items():
        soul_path = profiles_root / profile / "SOUL.md"
        new_content = render_soul(profile, spec, global_gates=global_gates)
        new_hash = sha256_text(new_content)
        new_hashes.append(new_hash)
        old_content = soul_path.read_text(encoding="utf-8") if soul_path.exists() else ""
        old_hash = sha256_text(old_content) if old_content else ""
        backup_path = ""
        if soul_path.exists():
            backup = backup_dir / f"{profile}_SOUL_before.md"
            backup.write_text(old_content, encoding="utf-8")
            backup_path = str(backup)
        would_change = old_content != new_content
        if apply and would_change:
            soul_path.parent.mkdir(parents=True, exist_ok=True)
            soul_path.write_text(new_content, encoding="utf-8")
        rows.append(
            {
                "profile": profile,
                "soul_path": str(soul_path),
                "backup_path": backup_path,
                "old_sha256": old_hash,
                "new_sha256": new_hash,
                "would_change": would_change,
                "changed": bool(apply and would_change),
                "canary_pass": canary_passes(profile, new_content),
            }
        )

    report = {
        "generated_at": now_iso(),
        "mode": "apply" if apply else "dry_run",
        "registry": str(REGISTRY_PATH),
        "profiles_mutated": bool(apply),
        "cron_mutated": False,
        "memory_mutated": False,
        "credentials_mutated": False,
        "external_actions_executed": False,
        "profile_count": len(specs),
        "unique_new_hash_count": len(set(new_hashes)),
        "safety_note": (
            "Only SOUL.md files change in --apply mode. No cron, skills, memory, "
            "credentials, gateway, Drive, business register, or external action is touched."
        ),
        "profiles": rows,
    }
    report_path = run_dir / "profile_specialization_report.json"
    report["report_path"] = str(report_path)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(report_path, 0o600)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--profiles-root", default=str(DEFAULT_PROFILES_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--profile", action="append", help="Limit to a named profile; may repeat")
    parser.add_argument("--apply", action="store_true", help="Write SOUL.md files after backup")
    args = parser.parse_args()

    registry = load_registry(Path(args.registry))
    report = apply_specialist_souls(
        Path(args.profiles_root),
        Path(args.output_root),
        apply=args.apply,
        profile_specs=registry["profiles"],
        global_gates=list((registry.get("global_policy") or {}).get("approval_gates") or []),
        selected_profiles=set(args.profile) if args.profile else None,
    )
    print(f"Profile specialization {report['mode']} complete")
    print(f"Report: {report['report_path']}")
    print(f"Profiles: {report['profile_count']} unique_new_hashes={report['unique_new_hash_count']}")
    print("No cron, memory, credentials, gateway, registers, or external action was executed.")
    return 0 if all(item["canary_pass"] for item in report["profiles"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
