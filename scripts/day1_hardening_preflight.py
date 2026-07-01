#!/usr/bin/env python3
"""Day 1 hardening preflight for Tender Export OS.

Read-only against Hermes/runtime state. The only writes are local evidence files
under outputs/day1_hardening/. It does not pause/delete cron jobs, change
profiles, upload to Drive, send messages, submit bids, pay, use DSC, or mutate
business registers.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILES_ROOT = Path.home() / ".hermes" / "profiles"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "day1_hardening"
CANONICAL_CRON_PROFILE = "tender-export-os"

TENDER_PROFILE_NAMES = [
    "tender-export-os",
    "hermes-chief-operator",
    "gov-tender-radar",
    "export-rfq-radar",
    "supplier-sourcing",
    "pricing-compliance",
    "codex-artifact-factory",
    "sales-followup",
    "source-health",
    "learning-review",
    "chatgpt-boardroom-handoff",
]

SAFE_REPO_BACKUP_FILES = [
    "README.md",
    "AGENTS.md",
    "HERMES.md",
    "SOUL.md",
    "manifest.json",
    "docs/FINAL_ARCHITECTURE.md",
    "docs/CHATGPT_BOARDROOM.md",
    "docs/WEB_BROWSER_RESEARCH_ROUTING.md",
    "docs/V4_1_2_PHASEWISE_IMPLEMENTATION_PLAN.md",
    "docs/V4_1_2_OPERATIONAL_READINESS_REPORT.md",
    "docs/HYBRID_RESEARCH_AND_CAPTURE_MODEL.md",
    "docs/DEEP_RESEARCH_TO_REPO_STAGING.md",
    "config/hermes_cron.yaml",
    "config/portal_access_reality.yaml",
    "config/research_capture_routing.yaml",
    "config/sources.gov.yaml",
    "config/sources.export.yaml",
    "config/sources.supplier.yaml",
    "config/plugin_routing.yaml",
    "config/agent_capability_routing.yaml",
]

RUNTIME_DATA_FILES_FOR_HASH_ONLY = [
    "data/master_cases.csv",
    "data/approvals_receipts.csv",
    "data/agent_run_log.csv",
    "data/source_health.csv",
    "data/plugin_health.csv",
    "data/supplier_master.csv",
    "data/quote_master.csv",
    "data/events.jsonl",
]

SECRET_KEY_RE = re.compile(r"(password|passwd|secret|token|api[_-]?key|cookie|session|otp|mfa|bearer|authorization)", re.I)


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def rel(path: Path, root: Path = PROJECT_ROOT) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def redact(value: Any, key_hint: str = "") -> Any:
    if SECRET_KEY_RE.search(key_hint):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(key): redact(item, str(key)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item, key_hint) for item in value]
    if isinstance(value, str) and SECRET_KEY_RE.search(value):
        return "[REDACTED_STRING]"
    return value


def file_fingerprint(path: Path, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    if not path.exists():
        return {"path": rel(path, root), "exists": False}
    return {
        "path": rel(path, root),
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "modified_at": dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).replace(microsecond=0).isoformat(),
    }


def copy_safe_repo_backups(project_root: Path, run_dir: Path) -> list[dict[str, Any]]:
    copied = []
    for relative in SAFE_REPO_BACKUP_FILES:
        source = project_root / relative
        if not source.exists():
            copied.append({"source": relative, "exists": False})
            continue
        destination = run_dir / "backups" / "repo_files" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append({
            "source": relative,
            "backup_path": rel(destination, project_root),
            "sha256": sha256_file(source),
            "bytes": source.stat().st_size,
            "exists": True,
        })
    return copied


def discover_profiles(profiles_root: Path) -> list[Path]:
    profiles = []
    for name in TENDER_PROFILE_NAMES:
        path = profiles_root / name
        if path.exists() and path.is_dir():
            profiles.append(path)
    return profiles


def prompt_inventory(profile_dir: Path, run_dir: Path, project_root: Path) -> dict[str, Any]:
    soul = profile_dir / "SOUL.md"
    item = {
        "profile": profile_dir.name,
        "soul_path": str(soul),
        "exists": soul.exists(),
    }
    if not soul.exists():
        return item
    backup = run_dir / "backups" / "profile_prompts" / f"{profile_dir.name}_SOUL.md"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(soul, backup)
    item.update({
        "sha256": sha256_file(soul),
        "bytes": soul.stat().st_size,
        "backup_path": rel(backup, project_root),
    })
    return item


def redact_cron_job(job: dict[str, Any]) -> dict[str, Any]:
    redacted = redact(job)
    prompt = job.get("prompt") or ""
    if isinstance(redacted, dict) and "prompt" in redacted:
        redacted["prompt_sha256"] = sha256_bytes(prompt.encode("utf-8")) if prompt else ""
        redacted["prompt_chars"] = len(prompt)
        redacted["prompt_redacted"] = True
        redacted.pop("prompt", None)
    return redacted


def cron_inventory(profile_dir: Path, run_dir: Path, project_root: Path) -> dict[str, Any]:
    jobs_path = profile_dir / "cron" / "jobs.json"
    result = {
        "profile": profile_dir.name,
        "jobs_path": str(jobs_path),
        "exists": jobs_path.exists(),
        "jobs": [],
        "enabled_count": 0,
        "total_count": 0,
    }
    if not jobs_path.exists():
        return result
    data = read_json(jobs_path)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    result["total_count"] = len(jobs)
    result["enabled_count"] = sum(1 for job in jobs if job.get("enabled"))
    result["jobs"] = [redact_cron_job(job) for job in jobs]
    backup = run_dir / "backups" / "profile_cron_redacted" / f"{profile_dir.name}_jobs.redacted.json"
    write_json(backup, {"jobs": result["jobs"]})
    result["redacted_backup_path"] = rel(backup, project_root)
    result["jobs_json_sha256"] = sha256_file(jobs_path)
    return result


def job_key(profile: str, job: dict[str, Any]) -> str:
    schedule = job.get("schedule_display") or job.get("schedule", {}).get("display") or job.get("schedule", {}).get("expr") or ""
    return "|".join([
        str(job.get("name") or job.get("id") or ""),
        str(schedule),
        str(job.get("workdir") or ""),
    ])


def build_cron_cleanup_plan(cron_profiles: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for profile in cron_profiles:
        for job in profile.get("jobs", []):
            groups.setdefault(job_key(profile["profile"], job), []).append({"profile": profile["profile"], "job": job})

    actions = []
    duplicate_groups = []
    active_by_profile = {profile["profile"]: profile.get("enabled_count", 0) for profile in cron_profiles}
    for key, entries in sorted(groups.items()):
        if len(entries) < 2:
            continue
        duplicate_groups.append({
            "key": key,
            "profiles": [entry["profile"] for entry in entries],
            "job_ids": [entry["job"].get("id") for entry in entries],
        })
        for entry in entries:
            profile = entry["profile"]
            job = entry["job"]
            if profile == CANONICAL_CRON_PROFILE:
                actions.append({
                    "action": "KEEP_CANONICAL_ACTIVE",
                    "profile": profile,
                    "job_id": job.get("id"),
                    "job_name": job.get("name"),
                    "reason": "Canonical Tender Export OS cron owner.",
                })
            elif job.get("enabled"):
                actions.append({
                    "action": "PAUSE_CANDIDATE_DRY_RUN_ONLY",
                    "profile": profile,
                    "job_id": job.get("id"),
                    "job_name": job.get("name"),
                    "reason": "Duplicate specialist-profile cron risk if this profile's scheduler is started.",
                    "command_hint_not_executed": f"hermes --profile {profile} cron pause {job.get('id')}",
                })

    for profile, enabled_count in sorted(active_by_profile.items()):
        if profile != CANONICAL_CRON_PROFILE and enabled_count:
            actions.append({
                "action": "PROFILE_CRON_OWNER_REVIEW_DRY_RUN_ONLY",
                "profile": profile,
                "enabled_jobs": enabled_count,
                "reason": "Day 1 policy keeps live cron ownership in tender-export-os unless owner intentionally deploys specialist schedulers.",
            })

    return {
        "generated_at": now_iso(),
        "mode": "dry_run_only",
        "canonical_cron_owner": CANONICAL_CRON_PROFILE,
        "external_actions_executed": False,
        "cron_mutated": False,
        "safety_note": "No cron job was paused, deleted, resumed, created, or edited. This is a review plan only.",
        "active_jobs_by_profile": active_by_profile,
        "duplicate_groups": duplicate_groups,
        "recommended_actions": actions,
    }


def run_command(args: list[str], cwd: Path, timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
        return {
            "command": " ".join(args),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "ok": result.returncode == 0,
        }
    except Exception as exc:  # CLI availability should not fail preflight.
        return {"command": " ".join(args), "ok": False, "error": str(exc)}


def collect_git_snapshot(project_root: Path, run_dir: Path) -> dict[str, Any]:
    commands = {
        "git_status_short": ["git", "status", "--short"],
        "git_diff_stat": ["git", "diff", "--stat"],
    }
    snapshot = {}
    for name, command in commands.items():
        result = run_command(command, cwd=project_root, timeout=30)
        snapshot[name] = {key: value for key, value in result.items() if key != "stdout"}
        output_path = run_dir / f"{name}.txt"
        output_path.write_text(result.get("stdout", "") or result.get("stderr", "") or result.get("error", ""), encoding="utf-8")
        snapshot[name]["output_path"] = rel(output_path, project_root)
    return snapshot


def collect_kanban_snapshot(project_root: Path, run_dir: Path, skip_cli: bool) -> dict[str, Any]:
    if skip_cli:
        return {"skipped": True, "reason": "--skip-kanban-cli"}
    outputs = {}
    commands = {
        "list_json": ["hermes", "kanban", "--board", "tender-export-os", "list", "--json"],
        "stats": ["hermes", "kanban", "--board", "tender-export-os", "stats"],
        "diagnostics": ["hermes", "kanban", "--board", "tender-export-os", "diagnostics"],
    }
    for name, command in commands.items():
        result = run_command(command, cwd=project_root, timeout=60)
        suffix = "json" if name.endswith("json") and result.get("ok") else "txt"
        path = run_dir / f"kanban_{name}.{suffix}"
        body = result.get("stdout", "") or result.get("stderr", "") or result.get("error", "") or ""
        path.write_text(body, encoding="utf-8")
        outputs[name] = {
            "command": result.get("command"),
            "ok": result.get("ok", False),
            "returncode": result.get("returncode"),
            "output_path": rel(path, project_root),
        }
    return outputs


def group_prompt_hashes(prompt_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for item in prompt_items:
        sha = item.get("sha256")
        if sha:
            grouped.setdefault(sha, []).append(item["profile"])
    return [
        {"sha256": sha, "profiles": profiles, "profile_count": len(profiles)}
        for sha, profiles in sorted(grouped.items(), key=lambda pair: (-len(pair[1]), pair[0]))
    ]


def build_preflight(project_root: Path, profiles_root: Path, output_root: Path, skip_kanban_cli: bool = False) -> dict[str, Any]:
    run_dir = output_root / f"day1_preflight_{now_stamp()}"
    run_dir.mkdir(parents=True, exist_ok=True)

    repo_backups = copy_safe_repo_backups(project_root, run_dir)
    runtime_hashes = [file_fingerprint(project_root / relative, project_root) for relative in RUNTIME_DATA_FILES_FOR_HASH_ONLY]
    profiles = discover_profiles(profiles_root)
    prompt_items = [prompt_inventory(profile, run_dir, project_root) for profile in profiles]
    cron_profiles = [cron_inventory(profile, run_dir, project_root) for profile in profiles]
    cron_plan = build_cron_cleanup_plan(cron_profiles)
    cron_plan_path = run_dir / "cron_cleanup_dry_run_plan.json"
    write_json(cron_plan_path, cron_plan)

    inventory = {
        "generated_at": now_iso(),
        "mode": "day1_preflight_dry_run",
        "project_root": str(project_root),
        "profiles_root": str(profiles_root),
        "run_dir": rel(run_dir, project_root),
        "safety": {
            "external_actions_executed": False,
            "cron_mutated": False,
            "profiles_mutated": False,
            "drive_uploaded": False,
            "business_registers_mutated": False,
            "credentials_logged": False,
        },
        "repo_backups": repo_backups,
        "runtime_data_hash_only": runtime_hashes,
        "profile_prompt_inventory": prompt_items,
        "profile_prompt_hash_groups": group_prompt_hashes(prompt_items),
        "profile_cron_inventory": cron_profiles,
        "cron_cleanup_dry_run_plan_path": rel(cron_plan_path, project_root),
        "git_snapshot": collect_git_snapshot(project_root, run_dir),
        "kanban_snapshot": collect_kanban_snapshot(project_root, run_dir, skip_cli=skip_kanban_cli),
    }
    inventory_path = run_dir / "day1_preflight_inventory.json"
    write_json(inventory_path, inventory)

    readme = run_dir / "DAY1_PREFLIGHT_README.md"
    readme.write_text(
        "# Day 1 Hardening Preflight\n\n"
        f"Generated: {inventory['generated_at']}\n\n"
        "This folder contains local-only redacted inventory/backups and a cron cleanup dry-run plan.\n"
        "No cron jobs, profiles, Drive files, business registers, or external systems were mutated.\n\n"
        f"- Inventory: `{inventory_path.name}`\n"
        f"- Cron cleanup dry-run: `{cron_plan_path.name}`\n"
        "- Profile prompt backups: `backups/profile_prompts/`\n"
        "- Redacted cron backups: `backups/profile_cron_redacted/`\n"
        "- Safe repo file backups: `backups/repo_files/`\n",
        encoding="utf-8",
    )
    inventory["inventory_path"] = rel(inventory_path, project_root)
    inventory["readme_path"] = rel(readme, project_root)
    write_json(inventory_path, inventory)
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 1 hardening preflight: redacted inventory, backups, cron dry-run plan")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--profiles-root", default=str(DEFAULT_PROFILES_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--skip-kanban-cli", action="store_true", help="Skip Hermes Kanban CLI snapshot")
    args = parser.parse_args()

    inventory = build_preflight(
        Path(args.project_root).resolve(),
        Path(args.profiles_root).resolve(),
        Path(args.output_root).resolve(),
        skip_kanban_cli=args.skip_kanban_cli,
    )
    print("Day 1 hardening preflight complete")
    print(f"Inventory: {inventory['inventory_path']}")
    print(f"Cron cleanup dry-run: {inventory['cron_cleanup_dry_run_plan_path']}")
    print("No external actions executed. No cron/profile/register mutation performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
