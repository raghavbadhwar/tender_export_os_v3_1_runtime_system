#!/usr/bin/env python3
"""Install expiring, self-identifying wrappers for legacy Tender commands."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.apply_specialist_profile_souls import REGISTRY_PATH, load_registry


SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
DEFAULT_WRAPPER_DIR = Path.home() / ".local" / "bin"
DEFAULT_PROFILES_ROOT = Path.home() / ".hermes" / "profiles"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "profile_specialization" / "compatibility_wrappers.json"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def render_wrapper(alias: str, target: str, expires_on: str, hermes_binary: str) -> str:
    if not SAFE_NAME.fullmatch(alias) or not SAFE_NAME.fullmatch(target):
        raise ValueError("Unsafe alias or target profile name")
    if not hermes_binary.startswith("/"):
        raise ValueError("Hermes binary must be an absolute path")
    notice = (
        f"DEPRECATED: {alias} now routes to Hermes profile {target} and expires "
        f"after {expires_on}. Target profile: {target}"
    )
    return f"#!/bin/sh\nprintf '%s\\n' '{notice}' >&2\nexec {hermes_binary} -p {target} \"$@\"\n"


def install_wrappers(
    aliases: dict[str, str],
    *,
    wrapper_dir: Path,
    profiles_root: Path,
    expires_on: str,
    hermes_binary: str,
    apply: bool = False,
    backup_dir: Path,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failed = 0
    for alias, target in aliases.items():
        wrapper = wrapper_dir / alias
        target_dir = profiles_root / target
        row: dict[str, Any] = {
            "alias": alias,
            "target_profile": target,
            "wrapper": str(wrapper),
            "target_on_disk": target_dir.is_dir(),
            "would_change": True,
            "changed": False,
        }
        if not apply:
            rows.append(row)
            continue
        if not target_dir.is_dir():
            row["status"] = "TARGET_PROFILE_MISSING"
            failed += 1
            rows.append(row)
            continue
        wrapper_dir.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)
        if wrapper.exists():
            shutil.copy2(wrapper, backup_dir / f"{alias}.before")
        content = render_wrapper(alias, target, expires_on, hermes_binary)
        wrapper.write_text(content, encoding="utf-8")
        os.chmod(wrapper, 0o755)
        row["changed"] = True
        row["status"] = "PASS"
        rows.append(row)
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "mode": "apply" if apply else "dry_run",
        "status": "PASS" if failed == 0 else "FAIL",
        "expires_on": expires_on,
        "wrappers_mutated": apply and any(row["changed"] for row in rows),
        "kanban_assignees_mutated": False,
        "external_actions_executed": False,
        "failed": failed,
        "wrappers": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--wrapper-dir", default=str(DEFAULT_WRAPPER_DIR))
    parser.add_argument("--profiles-root", default=str(DEFAULT_PROFILES_ROOT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    registry = load_registry(Path(args.registry))
    policy = registry.get("compatibility_policy") or {}
    expires_on = str(policy.get("expires_on") or "")
    if not expires_on:
        raise SystemExit("compatibility_policy.expires_on is required")
    hermes_binary = shutil.which("hermes") or ""
    if not hermes_binary:
        raise SystemExit("hermes is not on PATH")
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    report = install_wrappers(
        dict(registry.get("compatibility_aliases") or {}),
        wrapper_dir=Path(args.wrapper_dir),
        profiles_root=Path(args.profiles_root),
        expires_on=expires_on,
        hermes_binary=str(Path(hermes_binary).resolve()),
        apply=args.apply,
        backup_dir=output.parent / "wrapper_backups",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    os.chmod(output, 0o600)
    print(json.dumps({"status": report["status"], "mode": report["mode"], "wrappers": len(report["wrappers"]), "output": str(output)}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
