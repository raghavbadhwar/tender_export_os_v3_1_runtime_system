#!/usr/bin/env python3
"""Run a non-destructive Tender Export OS disaster-recovery drill."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "disaster_recovery_drill"
PROFILE_REGISTRY = PROJECT_ROOT / "config" / "hermes_specialist_profiles.yaml"
HERMES_PROFILES_ROOT = Path.home() / ".hermes" / "profiles"
Runner = Callable[..., subprocess.CompletedProcess[str]]


def load_registry(path: Path = PROFILE_REGISTRY) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def profile_names(registry: dict[str, Any]) -> list[str]:
    owner = str(registry.get("owner_profile") or "").strip()
    specialists = [str(value).strip() for value in registry.get("specialist_profiles") or [] if str(value).strip()]
    return list(dict.fromkeys(([owner] if owner else []) + specialists))


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def export_profiles(profiles: list[str], output_dir: Path, *, profiles_root: Path = HERMES_PROFILES_ROOT) -> list[dict[str, Any]]:
    exported = []
    for profile in profiles:
        src_dir = profiles_root / profile
        target_dir = output_dir / profile
        files = []
        for name in ("config.yaml", "profile.yaml", "SOUL.md", "state.db"):
            src = src_dir / name
            if copy_if_exists(src, target_dir / name):
                files.append(name)
        exported.append({"profile": profile, "source_exists": src_dir.is_dir(), "files": files})
    return exported


def run_command(command: list[str], *, runner: Runner = subprocess.run, timeout: int = 120) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = runner(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "runtime_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "runtime_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": exc.stdout[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": exc.stderr[-4000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def isolated_restore_check(profile: str, export_dir: Path, restore_dir: Path) -> dict[str, Any]:
    source = export_dir / profile
    target = restore_dir / f"{profile}-drill-restore"
    if target.exists():
        shutil.rmtree(target)
    if source.exists():
        shutil.copytree(source, target)
    required = ["config.yaml", "SOUL.md", "state.db"]
    missing = [name for name in required if not (target / name).is_file()]
    return {
        "profile": profile,
        "restore_path": str(target),
        "required_files": required,
        "missing": missing,
        "ok": not missing,
    }


def run_drill(*, output_root: Path = DEFAULT_OUTPUT_ROOT, runner: Runner = subprocess.run) -> dict[str, Any]:
    started = time.monotonic()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    drill_dir = output_root / f"DR-{stamp}"
    export_dir = drill_dir / "profile_exports"
    restore_dir = drill_dir / "isolated_restore"
    projections_dir = drill_dir / "rebuilt_projections"
    config_snapshot_dir = drill_dir / "config_snapshot"
    drill_dir.mkdir(parents=True, exist_ok=True)

    registry = load_registry()
    profiles = profile_names(registry)
    exported = export_profiles(profiles, export_dir)
    copy_if_exists(PROJECT_ROOT / "data" / "events.jsonl", drill_dir / "snapshots" / "events.jsonl")
    for config_name in (
        "hermes_specialist_profiles.yaml",
        "kanban_board.yaml",
        "approval_policy.yaml",
        "profile_production_routing_gate.yaml",
        "shadow_pilot.yaml",
    ):
        copy_if_exists(PROJECT_ROOT / "config" / config_name, config_snapshot_dir / config_name)

    projection = run_command(
        [".venv/bin/python", "scripts/rebuild_projections_from_events.py", "--output-dir", str(projections_dir)],
        runner=runner,
        timeout=180,
    )
    checkpoint_status = run_command(["hermes", "checkpoints", "status"], runner=runner, timeout=60)
    restored = isolated_restore_check(profiles[0], export_dir, restore_dir) if profiles else {"ok": False, "missing": ["no profiles"]}
    blockers: list[str] = []
    if any(not row["source_exists"] for row in exported):
        blockers.append("one or more configured profile directories are missing")
    if projection["returncode"] != 0:
        blockers.append("projection rebuild failed")
    if checkpoint_status["returncode"] != 0:
        blockers.append("checkpoint status failed")
    if not restored["ok"]:
        blockers.append("isolated profile restore check failed")

    runtime = round(time.monotonic() - started, 3)
    report = {
        "schema_version": "disaster_recovery_drill.v1",
        "run_id": f"DR-{stamp}",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS" if not blockers else "BLOCKED",
        "output_dir": str(drill_dir),
        "profile_exports": exported,
        "snapshot_paths": {
            "events": str(drill_dir / "snapshots" / "events.jsonl"),
            "config_snapshot": str(config_snapshot_dir),
            "rebuilt_projections": str(projections_dir),
        },
        "projection_rebuild": projection,
        "checkpoint_status": checkpoint_status,
        "isolated_restore": restored,
        "measured_recovery_time_seconds": runtime,
        "data_loss_point": "latest local data/events.jsonl copied at drill start",
        "destructive_restore_performed": False,
        "external_actions_executed": False,
        "blockers": blockers,
    }
    report_path = drill_dir / "disaster_recovery_drill_report.json"
    report["report_path"] = str(report_path)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = run_drill()
    payload = {
        "status": report["status"],
        "report": report["report_path"],
        "measured_recovery_time_seconds": report["measured_recovery_time_seconds"],
        "destructive_restore_performed": False,
    }
    print(json.dumps(payload, indent=2) if args.json else f"DR drill {report['status']}: {report['report_path']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
