#!/usr/bin/env python3
"""Revalidate Google Drive Knowledge Bus sync with a non-sensitive dry-run receipt."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECEIPT_DIR = PROJECT_ROOT / "receipts" / "drive_setup"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "drive_revalidation"
Runner = Callable[..., subprocess.CompletedProcess[str]]


def now_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def project_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return path.name


def scrub_local_paths(value: Any) -> Any:
    """Remove absolute local workspace paths from public-sync receipts."""
    local_root = str(PROJECT_ROOT)
    if isinstance(value, str):
        return value.replace(local_root, ".")
    if isinstance(value, list):
        return [scrub_local_paths(item) for item in value]
    if isinstance(value, dict):
        return {key: scrub_local_paths(item) for key, item in value.items()}
    return value


def sanitize_existing_public_artifacts(*, output_dir: Path = OUTPUT_DIR, receipt_dir: Path = RECEIPT_DIR) -> list[str]:
    """Rewrite prior generated Drive revalidation artifacts so public-template scans stay clean."""
    sanitized: list[str] = []
    for directory in (output_dir, receipt_dir):
        if not directory.is_dir():
            continue
        for path in directory.glob("*.json"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            new_text = text.replace(str(PROJECT_ROOT), ".")
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
                sanitized.append(project_relative(path))
    return sanitized


def run_command(command: list[str], *, runner: Runner = subprocess.run, timeout: int = 45) -> dict[str, Any]:
    try:
        completed = runner(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return scrub_local_paths({
            "command": command,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "timed_out": False,
        })
    except subprocess.TimeoutExpired as exc:
        return scrub_local_paths({
            "command": command,
            "returncode": None,
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        })


def build_revalidation(
    *,
    runner: Runner = subprocess.run,
    stamp: str | None = None,
    output_dir: Path = OUTPUT_DIR,
    receipt_dir: Path = RECEIPT_DIR,
) -> dict[str, Any]:
    stamp = stamp or now_stamp()
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt_dir.mkdir(parents=True, exist_ok=True)
    sanitized_artifacts = sanitize_existing_public_artifacts(output_dir=output_dir, receipt_dir=receipt_dir)
    manifest_path = output_dir / f"knowledge_bus_dry_run_manifest_{stamp}.json"
    auth = run_command(
        [".venv/bin/python", "scripts/sync_to_drive.py", "--check-auth"],
        runner=runner,
        timeout=20,
    )
    dry_run = run_command(
        [
            ".venv/bin/python",
            "scripts/sync_to_drive.py",
            "--mode",
            "public-template",
            "--group",
            "00_Project_Context",
            "--dry-run",
            "--output",
            str(manifest_path),
        ],
        runner=runner,
        timeout=60,
    )
    dry_run_passed = dry_run["returncode"] == 0 and manifest_path.is_file()
    auth_passed = auth["returncode"] == 0
    status = "PASS" if dry_run_passed and auth_passed else ("DRY_RUN_PASS_LIVE_AUTH_BLOCKED" if dry_run_passed else "FAIL")
    remediation_steps: list[str] = []
    if dry_run_passed and not auth_passed:
        remediation_steps.extend(
            [
                "Renew Google Drive auth for gws with drive scope.",
                "Run: gws auth login -s drive,sheets",
                "Rerun: python3 scripts/revalidate_drive_knowledge_bus_sync.py --json",
                "Keep live_upload_attempted=false unless a separate owner-approved execute path is requested.",
            ]
        )
    elif not dry_run_passed:
        remediation_steps.extend(
            [
                "Fix public-template dry-run blockers before any live Drive sync.",
                "Review the dry_run stdout_tail in this receipt for content-scan or routing failures.",
                "Rerun: python3 scripts/revalidate_drive_knowledge_bus_sync.py --json",
            ]
        )
    receipt = {
        "schema_version": "drive_knowledge_bus_revalidation.v1",
        "receipt_id": f"DRIVE-REVALIDATION-{stamp}",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "drive_root": "Tender Export OS - Knowledge Bus",
        "stable_context_folder": "00_Project_Context",
        "bridge_folder_boundary": "08_ChatGPT_Bridge is for bounded packet exchange only",
        "non_sensitive_packet": True,
        "sanitized_existing_artifacts": sanitized_artifacts,
        "dry_run_manifest": project_relative(manifest_path),
        "auth_check": auth,
        "dry_run": dry_run,
        "remediation_steps": remediation_steps,
        "live_upload_attempted": False,
        "external_actions_executed": False,
        "safety_note": "Dry-run revalidation only. No Drive upload was attempted unless a future owner-approved execute path is run separately.",
    }
    receipt_path = receipt_dir / f"knowledge_bus_revalidation_{stamp}.json"
    receipt["receipt_path"] = project_relative(receipt_path)
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    receipt = build_revalidation()
    payload = {
        "status": receipt["status"],
        "receipt": receipt["receipt_path"],
        "dry_run_manifest": receipt["dry_run_manifest"],
        "live_upload_attempted": False,
    }
    print(json.dumps(payload, indent=2) if args.json else f"Drive revalidation {receipt['status']}: {receipt['receipt_path']}")
    return 0 if receipt["status"] in {"PASS", "DRY_RUN_PASS_LIVE_AUTH_BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
