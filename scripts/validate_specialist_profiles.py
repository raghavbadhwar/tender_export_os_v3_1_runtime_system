#!/usr/bin/env python3
"""Validate real Tender OS Hermes profiles and least-privilege boundaries."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.apply_specialist_profile_souls import REGISTRY_PATH, load_registry


DEFAULT_PROFILES_ROOT = Path.home() / ".hermes" / "profiles"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "profile_specialization" / "specialist_validation.json"
Runner = Callable[..., subprocess.CompletedProcess[str]]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(runner: Runner, command: list[str]) -> subprocess.CompletedProcess[str]:
    return runner(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )


def _auth_passed(result: subprocess.CompletedProcess[str]) -> bool:
    output = f"{result.stdout}\n{result.stderr}".lower()
    denied = any(marker in output for marker in ("not logged in", "not configured", "missing", "expired"))
    return result.returncode == 0 and not denied


def _same_file_hash(left: Path, right: Path) -> bool:
    return left.is_file() and right.is_file() and sha256_file(left) == sha256_file(right)


def _duplicates(values: dict[str, str]) -> list[list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for profile, value in values.items():
        if value:
            grouped[value].append(profile)
    return sorted(sorted(group) for group in grouped.values() if len(group) > 1)


def validate_profiles(
    registry: dict[str, Any],
    *,
    profiles_root: Path = DEFAULT_PROFILES_ROOT,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    workspace = str(registry.get("workspace") or "")
    owner_name = str(registry.get("owner_profile") or "tender-export-os")
    owner_dir = profiles_root / owner_name
    profile_specs = registry.get("profiles") or {}
    requested = list(registry.get("specialist_profiles") or [])

    descriptions: dict[str, str] = {}
    soul_hashes: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    failed_checks = 0

    for profile in requested:
        spec = profile_specs.get(profile) or {}
        profile_dir = profiles_root / profile
        errors: list[str] = []
        row: dict[str, Any] = {
            "profile": profile,
            "on_disk": profile_dir.is_dir(),
            "auth_status": "NOT_CHECKED",
            "forbidden_tools_present": [],
            "profile_local_cron": False,
            "separate_gateway": False,
            "copied_auth_material": False,
            "copied_env_material": False,
            "copied_memory_material": False,
        }
        if not profile_dir.is_dir():
            errors.append("profile directory missing")
            row["errors"] = errors
            row["ok"] = False
            failed_checks += len(errors)
            rows.append(row)
            continue

        config_path = profile_dir / "config.yaml"
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            if not isinstance(config, dict):
                raise ValueError("config is not a mapping")
        except (OSError, ValueError, yaml.YAMLError) as exc:
            config = {}
            errors.append(f"invalid config: {type(exc).__name__}")

        meta_path = profile_dir / "profile.yaml"
        try:
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            meta = {}
        description = str(meta.get("description") or "").strip()
        descriptions[profile] = description
        row["description_matches"] = description == str(spec.get("description") or "").strip()
        if not row["description_matches"]:
            errors.append("description does not match registry")

        soul_path = profile_dir / "SOUL.md"
        if soul_path.is_file():
            soul_hash = sha256_file(soul_path)
            soul_hashes[profile] = soul_hash
            row["soul_sha256"] = soul_hash
            if profile.lower() not in soul_path.read_text(encoding="utf-8", errors="ignore").lower():
                errors.append("SOUL does not identify its profile")
        else:
            errors.append("SOUL.md missing")

        actual_toolsets = list(((config.get("platform_toolsets") or {}).get("cli") or []))
        expected_toolsets = list(spec.get("allowed_toolsets") or [])
        row["toolsets_exact"] = actual_toolsets == expected_toolsets
        row["actual_toolsets"] = actual_toolsets
        if not row["toolsets_exact"]:
            errors.append("platform_toolsets.cli mismatch")
        forbidden = sorted(set(actual_toolsets) & set(spec.get("forbidden_toolsets") or []))
        row["forbidden_tools_present"] = forbidden
        if forbidden:
            errors.append("forbidden toolset present")

        actual_mcp = list(
            (((config.get("mcp_servers") or {}).get("tender_os") or {}).get("tools") or {}).get("include")
            or []
        )
        expected_mcp = list(spec.get("mcp_tools") or [])
        row["mcp_allowlist_exact"] = actual_mcp == expected_mcp
        row["actual_mcp_tools"] = actual_mcp
        if not row["mcp_allowlist_exact"]:
            errors.append("Tender OS MCP allowlist mismatch")

        row["mcp_timeout_correct"] = config.get("mcp_discovery_timeout") == 20
        if not row["mcp_timeout_correct"]:
            errors.append("mcp_discovery_timeout is not 20")
        row["terminal_workspace_correct"] = ((config.get("terminal") or {}).get("cwd") or "") == workspace
        if not row["terminal_workspace_correct"]:
            errors.append("terminal.cwd mismatch")
        row["dispatcher_disabled"] = ((config.get("kanban") or {}).get("dispatch_in_gateway")) is False
        if not row["dispatcher_disabled"]:
            errors.append("specialist gateway dispatcher is not disabled")

        cron_dir = profile_dir / "cron"
        row["profile_local_cron"] = cron_dir.is_dir() and any(path.is_file() for path in cron_dir.rglob("*"))
        if row["profile_local_cron"]:
            errors.append("profile-local cron files present")

        gateway_files = [profile_dir / name for name in ("gateway.pid", "gateway.lock", "gateway_state.json")]
        show = _run(runner, ["hermes", "profile", "show", profile])
        show_text = f"{show.stdout}\n{show.stderr}".lower()
        gateway_reported_running = "gateway: running" in show_text or "gateway      running" in show_text
        row["separate_gateway"] = any(path.exists() for path in gateway_files) or gateway_reported_running
        if row["separate_gateway"]:
            errors.append("separate specialist gateway present")

        auth = _run(runner, ["hermes", "-p", profile, "auth", "status", "openai-codex"])
        row["auth_status"] = "PASS" if _auth_passed(auth) else "AUTH_REQUIRED"
        if row["auth_status"] != "PASS":
            errors.append("OpenAI Codex auth required")

        missing_skills = [
            name
            for name in spec.get("skill_bundle") or []
            if not (profile_dir / "skills" / name / "SKILL.md").is_file()
        ]
        row["missing_role_skills"] = missing_skills
        if missing_skills:
            errors.append("role skill missing")

        row["copied_auth_material"] = _same_file_hash(profile_dir / "auth.json", owner_dir / "auth.json")
        row["copied_env_material"] = _same_file_hash(profile_dir / ".env", owner_dir / ".env")
        for name in ("MEMORY.md", "USER.md"):
            if _same_file_hash(profile_dir / "memories" / name, owner_dir / "memories" / name):
                row["copied_memory_material"] = True
        if row["copied_auth_material"]:
            errors.append("owner auth material appears copied")
        if row["copied_env_material"]:
            errors.append("owner env material appears copied")
        if row["copied_memory_material"]:
            errors.append("owner memory material appears copied")

        row["errors"] = errors
        row["ok"] = not errors
        failed_checks += len(errors)
        rows.append(row)

    duplicate_descriptions = _duplicates(descriptions)
    duplicate_soul_hashes = _duplicates(soul_hashes)
    failed_checks += len(duplicate_descriptions) + len(duplicate_soul_hashes)
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "status": "PASS" if failed_checks == 0 else "FAIL",
        "profiles_root": str(profiles_root),
        "expected_profiles": requested,
        "profile_count": len(rows),
        "passed_profiles": sum(bool(row.get("ok")) for row in rows),
        "failed_checks": failed_checks,
        "duplicate_descriptions": duplicate_descriptions,
        "duplicate_soul_hashes": duplicate_soul_hashes,
        "profiles": rows,
        "secrets_included": False,
        "external_actions_executed": False,
        "safety_note": "Auth commands are reduced to PASS or AUTH_REQUIRED; no tokens or credential output is stored.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--profiles-root", default=str(DEFAULT_PROFILES_ROOT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    report = validate_profiles(
        load_registry(Path(args.registry)),
        profiles_root=Path(args.profiles_root),
    )
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(output, 0o600)
    print(json.dumps({"status": report["status"], "failed_checks": report["failed_checks"], "output": str(output)}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
