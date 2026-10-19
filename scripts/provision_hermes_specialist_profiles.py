#!/usr/bin/env python3
"""Safely provision least-privilege Hermes specialist profiles.

Dry-run is the default. Apply mode creates only missing profiles with
``--no-skills``, deep-merges credential-free overlays, installs only the
registered local Tender skills, validates config, and records only a boolean
OpenAI Codex auth result. It never clones profiles or copies auth, env, memory,
cron, gateway, session, or business state.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.apply_specialist_profile_souls import REGISTRY_PATH, load_registry as _load_registry


DEFAULT_PROFILES_ROOT = Path.home() / ".hermes" / "profiles"
DEFAULT_OVERLAYS_ROOT = PROJECT_ROOT / "config" / "hermes_profiles"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "profile_specialization" / "provision_report.json"
Runner = Callable[..., subprocess.CompletedProcess[str]]

FORBIDDEN_OVERLAY_KEYS = {
    ".env",
    "auth",
    "auth.json",
    "credentials",
    "credential_pool",
    "cookies",
    "cron",
    "gateway",
    "gateway_state",
    "memories",
    "sessions",
    "state.db",
}
SECRET_KEY_PARTS = ("api_key", "password", "private_key", "refresh_token", "access_token", "client_secret")
SAFE_SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    return _load_registry(path)


def build_create_commands(registry: dict[str, Any], profiles_root: Path) -> list[list[str]]:
    commands: list[list[str]] = []
    profiles = registry.get("profiles") or {}
    requested = registry.get("specialist_profiles") or [
        name for name, spec in profiles.items() if spec.get("provision") == "create"
    ]
    for profile in requested:
        if (profiles_root / profile).is_dir():
            continue
        spec = profiles.get(profile) or {}
        if spec.get("provision") != "create":
            continue
        description = str(spec.get("description") or "").strip()
        if not description:
            raise ValueError(f"Missing description for {profile}")
        commands.append(
            [
                "hermes",
                "profile",
                "create",
                profile,
                "--no-skills",
                "--description",
                description,
            ]
        )
    return commands


def _check_overlay_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for raw_key, child in value.items():
            key = str(raw_key).strip().lower()
            dotted = ".".join((*path, key))
            if key in FORBIDDEN_OVERLAY_KEYS or any(part in key for part in SECRET_KEY_PARTS):
                raise ValueError(f"Overlay contains forbidden key: {dotted}")
            _check_overlay_keys(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_overlay_keys(child, (*path, str(index)))


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def write_profile_overlay(profile_dir: Path, overlay_path: Path) -> dict[str, Any]:
    overlay = yaml.safe_load(overlay_path.read_text(encoding="utf-8")) or {}
    if not isinstance(overlay, dict):
        raise ValueError(f"Overlay must be a YAML mapping: {overlay_path}")
    _check_overlay_keys(overlay)

    config_path = profile_dir / "config.yaml"
    current: dict[str, Any] = {}
    if config_path.is_file():
        current = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if not isinstance(current, dict):
            raise ValueError(f"Existing config must be a YAML mapping: {config_path}")
    merged = _deep_merge(current, overlay)
    config_path.write_text(
        yaml.safe_dump(merged, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    os.chmod(config_path, 0o600)
    return {
        "written": True,
        "overlay": str(overlay_path),
        "config": str(config_path),
        "config_sha256": sha256_file(config_path),
    }


def install_role_skills(
    source_profile_dir: Path,
    target_profile_dir: Path,
    skill_names: list[str],
) -> dict[str, Any]:
    installed: list[str] = []
    missing: list[str] = []
    for name in skill_names:
        if not SAFE_SKILL_NAME.fullmatch(name):
            raise ValueError(f"Unsafe skill name: {name!r}")
        source = source_profile_dir / "skills" / name
        target = target_profile_dir / "skills" / name
        if not (source / "SKILL.md").is_file():
            missing.append(name)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, symlinks=True, dirs_exist_ok=True)
        installed.append(name)
    return {"installed": installed, "missing": missing}


def _run(runner: Runner, command: list[str]) -> subprocess.CompletedProcess[str]:
    return runner(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def _auth_passed(completed: subprocess.CompletedProcess[str]) -> bool:
    combined = f"{completed.stdout}\n{completed.stderr}".lower()
    negative = any(marker in combined for marker in ("not logged in", "not configured", "missing", "expired"))
    return completed.returncode == 0 and not negative


def provision(
    registry: dict[str, Any],
    *,
    profiles_root: Path = DEFAULT_PROFILES_ROOT,
    overlays_root: Path = DEFAULT_OVERLAYS_ROOT,
    source_profile_dir: Path | None = None,
    apply: bool = False,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    source_profile = source_profile_dir or profiles_root / str(registry.get("owner_profile") or "tender-export-os")
    profiles = registry.get("profiles") or {}
    requested = list(registry.get("specialist_profiles") or [])
    create_commands = build_create_commands(registry, profiles_root)
    command_by_profile = {command[3]: command for command in create_commands}

    rows: list[dict[str, Any]] = []
    any_failed = False
    any_auth_required = False
    for profile in requested:
        spec = profiles.get(profile) or {}
        profile_dir = profiles_root / profile
        row: dict[str, Any] = {
            "profile": profile,
            "existed_before": profile_dir.is_dir(),
            "would_create": profile in command_by_profile,
            "created": False,
            "overlay": str(overlays_root / f"{profile}.yaml"),
            "skill_bundle": list(spec.get("skill_bundle") or []),
            "config_check": "NOT_RUN",
            "auth_status": "NOT_CHECKED",
            "credentials_copied": False,
            "memory_copied": False,
            "cron_copied": False,
            "gateway_started": False,
        }
        if not apply:
            rows.append(row)
            continue

        command = command_by_profile.get(profile)
        if command:
            completed = _run(runner, command)
            row["create_returncode"] = completed.returncode
            if completed.returncode != 0 or not profile_dir.is_dir():
                row["status"] = "CREATE_FAILED"
                any_failed = True
                rows.append(row)
                continue
            row["created"] = True

        if not profile_dir.is_dir():
            row["status"] = "PROFILE_MISSING"
            any_failed = True
            rows.append(row)
            continue

        overlay_path = overlays_root / f"{profile}.yaml"
        if not overlay_path.is_file():
            row["status"] = "OVERLAY_MISSING"
            any_failed = True
            rows.append(row)
            continue
        try:
            row["overlay_result"] = write_profile_overlay(profile_dir, overlay_path)
            row["skills"] = install_role_skills(
                source_profile,
                profile_dir,
                list(spec.get("skill_bundle") or []),
            )
        except (OSError, ValueError, yaml.YAMLError) as exc:
            row["status"] = "CONFIGURE_FAILED"
            row["error"] = f"{type(exc).__name__}: {exc}"
            any_failed = True
            rows.append(row)
            continue

        config_result = _run(runner, ["hermes", "-p", profile, "config", "check"])
        row["config_check"] = "PASS" if config_result.returncode == 0 else "FAIL"
        if config_result.returncode != 0:
            any_failed = True

        auth_result = _run(runner, ["hermes", "-p", profile, "auth", "status", "openai-codex"])
        if _auth_passed(auth_result):
            row["auth_status"] = "PASS"
        else:
            row["auth_status"] = "AUTH_REQUIRED"
            any_auth_required = True

        memory_dir = profile_dir / "memories"
        row["profile_auth_file_present"] = (profile_dir / "auth.json").exists()
        row["profile_memory_files_present"] = any(
            (memory_dir / name).exists() for name in ("MEMORY.md", "USER.md")
        )
        row["profile_cron_entries_present"] = any((profile_dir / "cron").glob("*.json")) if (profile_dir / "cron").is_dir() else False
        row["status"] = (
            "PASS"
            if row["config_check"] == "PASS" and row["auth_status"] == "PASS"
            else row["auth_status"] if row["config_check"] == "PASS" else "VALIDATION_FAILED"
        )
        rows.append(row)

    status = "DRY_RUN"
    if apply:
        status = "FAIL" if any_failed else "AUTH_REQUIRED" if any_auth_required else "PASS"
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "mode": "apply" if apply else "dry_run",
        "status": status,
        "profiles_root": str(profiles_root),
        "source_profile": str(source_profile),
        "create_commands": create_commands,
        "profiles": rows,
        "credentials_copied": False,
        "memory_copied": False,
        "cron_copied": False,
        "gateway_started": False,
        "external_actions_executed": False,
        "safety_note": (
            "No profile clone operation is used. Auth, .env, memory, cron, gateway, "
            "sessions, and business state are never copied."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--profiles-root", default=str(DEFAULT_PROFILES_ROOT))
    parser.add_argument("--overlays-root", default=str(DEFAULT_OVERLAYS_ROOT))
    parser.add_argument("--source-profile", default="")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    registry = load_registry(Path(args.registry))
    source = Path(args.source_profile) if args.source_profile else None
    report = provision(
        registry,
        profiles_root=Path(args.profiles_root),
        overlays_root=Path(args.overlays_root),
        source_profile_dir=source,
        apply=args.apply,
    )
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(output, 0o600)
    print(json.dumps({"status": report["status"], "mode": report["mode"], "output": str(output)}, indent=2))
    return 0 if report["status"] in {"PASS", "DRY_RUN"} else 2 if report["status"] == "AUTH_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
