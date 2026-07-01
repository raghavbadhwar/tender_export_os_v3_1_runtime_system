#!/usr/bin/env python3
"""
sync_to_drive.py
Upload local project outputs to Google Drive using the gws CLI.

Prerequisites:
  - gws CLI installed: brew install gws  (or brew install google-workspace-cli)
  - Authenticated: gws auth login -s drive,sheets
  - Drive folder created: set DRIVE_ROOT_FOLDER_ID below or in env var

Usage:
  # Dry-run (show what would be uploaded — safe, no writes)
  python3 scripts/sync_to_drive.py
  python3 scripts/sync_to_drive.py --mode private-runtime --dry-run

  # Execute upload for a specific group
  python3 scripts/sync_to_drive.py --execute --group daily_briefs

  # Execute upload for all groups (needs DRIVE_ROOT_FOLDER_ID set)
  python3 scripts/sync_to_drive.py --execute --all

  # Check gws auth status
  python3 scripts/sync_to_drive.py --check-auth

Environment variables:
  DRIVE_ROOT_FOLDER_ID   Google Drive folder ID for "Tender Export OS - Knowledge Bus"
  GWS_BIN                Override path to gws binary (default: gws)
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.check_no_private_runtime_data import (  # noqa: E402
    ALLOWLIST,
    SECRET_PATTERNS,
    TEXT_SUFFIXES,
    matches as scan_matches,
    parse_allowlist,
    scan_line,
    scrub_allowed,
)

GWS = os.environ.get("GWS_BIN", "gws")
DEFAULT_MANIFEST_OUTPUT = PROJECT_ROOT / "outputs" / "drive_sync_manifest.json"
DRIVE_SETUP_STATE = PROJECT_ROOT / "outputs" / "drive_knowledge_bus_setup.json"

# Set this to the Google Drive folder ID of your "Tender Export OS - Knowledge Bus" root
# Find it in Drive URL: drive.google.com/drive/folders/<FOLDER_ID>
DRIVE_ROOT_FOLDER_ID = os.environ.get("DRIVE_ROOT_FOLDER_ID", "")

PUBLIC_TEMPLATE_SYNC_GROUPS = {
    "00_Project_Context/01_Instructions": [
        "AGENTS.md",
        "README.md",
        "SOUL.md",
        "HERMES.md",
        "docs/FINAL_ARCHITECTURE.md",
        "docs/GOOGLE_DRIVE_KNOWLEDGE_BUS.md",
        "docs/CHATGPT_CODEX_HERMES_DRIVE_COMMUNICATION.md",
    ],
    "00_Schemas": [
        "config/schemas/*.json",
        "config/schemas/event_types.yaml",
    ],
    "00_Template_Data": ["data/examples/**"],
    "02_Case_Reports": ["outputs/examples/**"],
    "06_Receipts": ["receipts/examples/**"],
    "07_Config_Snapshots": [
        "config/sources.gov.yaml",
        "config/sources.export.yaml",
        "config/sources.supplier.yaml",
        "config/kill_rules.yaml",
        "config/scoring_weights.yaml",
        "config/approval_policy.yaml",
        "config/sync_policy.yaml",
        "config/hermes_cron.yaml",
        "config/kanban_board.yaml",
        "config/memory_policy.yaml",
        "config/public_scan_allowlist.yaml",
    ],
}

PRIVATE_RUNTIME_SYNC_GROUPS = {
    "00_Control_Center": [
        "data/events.jsonl",
        "data/master_cases.csv",
        "data/supplier_master.csv",
        "data/buyer_master.csv",
        "data/approvals_receipts.csv",
        "data/source_health.csv",
        "data/plugin_health.csv",
        "data/quote_master.csv",
        "data/rfq_master.csv",
        "data/demand_research.csv",
        "data/drive_manifest.csv",
        "data/agent_run_log.csv",
    ],
}

REDACTED_OWNER_BRIEF_SYNC_GROUPS = {
    "01_Daily_Briefs": ["outputs/daily_briefs/*.html"],
    "01_Owner_Reports": [
        "outputs/daily_briefs/*.md",
        "outputs/buyer_demand/*brief*.html",
        "outputs/buyer_demand/*brief*.md",
        "outputs/source_health/*report*.html",
        "outputs/deep_source_reports/*.html",
    ],
}

MODE_SYNC_GROUPS = {
    "public-template": PUBLIC_TEMPLATE_SYNC_GROUPS,
    "private-runtime": PRIVATE_RUNTIME_SYNC_GROUPS,
    "redacted-owner-brief": REDACTED_OWNER_BRIEF_SYNC_GROUPS,
}

# Backward-compatible alias for callers that import the old constant.
SYNC_GROUPS = PRIVATE_RUNTIME_SYNC_GROUPS

# Files that must NEVER be synced
NEVER_SYNC_PATTERNS = [
    "secrets", ".env", "credentials.json", "token", ".pem", ".key",
    "cookies", "DSC", "password", "bank", "private",
]

NEVER_SYNC_EXTENSIONS = {
    ".enc", ".p12", ".pfx", ".key", ".pem", ".asc", ".gpg",
}


def check_auth() -> bool:
    """Return True if gws can list Drive files."""
    try:
        result = subprocess.run(
            [GWS, "drive", "files", "list", "--params", '{"pageSize": 1}'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            print(f"✅ gws Drive auth OK — {GWS} is authenticated.")
            return True
        else:
            print(f"❌ gws Drive auth failed: {result.stderr.strip() or result.stdout.strip()}")
            return False
    except FileNotFoundError:
        print(f"❌ gws CLI not found at '{GWS}'. Install: brew install google-workspace-cli")
        return False
    except subprocess.TimeoutExpired:
        print("❌ gws auth check timed out.")
        return False


def load_setup_root_folder_id() -> str:
    if not DRIVE_SETUP_STATE.exists():
        return ""
    try:
        data = json.loads(DRIVE_SETUP_STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    return data.get("root_folder_id", "")


def is_safe_to_sync(path: Path) -> bool:
    """Return False if the file should never be synced."""
    name = path.name.lower()
    for pat in NEVER_SYNC_PATTERNS:
        if pat.lower() in name:
            return False
    if path.suffix.lower() in NEVER_SYNC_EXTENSIONS:
        return False
    return True


def expand_patterns(patterns: list[str]) -> list[Path]:
    files = []
    for pattern in patterns:
        if "*" in pattern or "?" in pattern:
            for match in glob.glob(str(PROJECT_ROOT / pattern), recursive=True):
                p = Path(match)
                if p.is_file() and is_safe_to_sync(p):
                    files.append(p)
        else:
            p = PROJECT_ROOT / pattern
            if p.is_file() and is_safe_to_sync(p):
                files.append(p)
    return sorted(set(files))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def content_scan_file(path: Path, mode: str, allowed_paths: list[str], allowed_literals: list[str]) -> list[str]:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return []
    relative = rel(path)
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError as exc:
        return [f"{relative}: read-error:{exc}"]

    findings: list[str] = []
    strict_public_scan = mode in {"public-template", "redacted-owner-brief"}
    allowed_by_path = scan_matches(relative, allowed_paths)
    for index, line in enumerate(lines, start=1):
        if strict_public_scan:
            line_findings = scan_line(path, index, line, allowed_literals)
            if allowed_by_path:
                line_findings = [
                    finding for finding in line_findings if not finding.endswith(" local-user-path")
                ]
            findings.extend(line_findings)
            continue

        text = scrub_allowed(line, allowed_literals)
        for pattern in SECRET_PATTERNS:
            if "re.compile(" in text:
                continue
            if pattern.search(text):
                findings.append(f"{relative}:{index}: secret-like-value")
                break
    return findings


def pre_upload_content_scan(files: list[Path], mode: str) -> list[str]:
    allowed_paths, allowed_literals = parse_allowlist(ALLOWLIST)
    findings: list[str] = []
    for path in files:
        findings.extend(content_scan_file(path, mode, allowed_paths, allowed_literals))
    return findings


def gws_upload(local_path: Path, parent_folder_id: str, dry_run: bool) -> bool:
    """Upload a file using gws drive files create. Returns True on success."""
    if dry_run:
        print(f"    [dry-run] Would upload: {local_path.relative_to(PROJECT_ROOT)}")
        return True

    params = {
        "fields": "id,name,webViewLink",
    }
    if parent_folder_id:
        params["parents"] = parent_folder_id  # not a query param — use metadata

    # gws drive files create uses --json for metadata and --upload for binary
    metadata = {"name": local_path.name}
    if parent_folder_id:
        metadata["parents"] = [parent_folder_id]

    try:
        result = subprocess.run(
            [
                GWS, "drive", "files", "create",
                "--json", json.dumps(metadata),
                "--upload", str(local_path),
                "--params", json.dumps({"fields": "id,name,webViewLink"}),
            ],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            try:
                out = json.loads(result.stdout)
                link = out.get("webViewLink", "no link")
                print(f"    ✅ Uploaded: {local_path.name} → {link}")
            except json.JSONDecodeError:
                print(f"    ✅ Uploaded: {local_path.name}")
            return True
        else:
            err = result.stderr.strip() or result.stdout.strip()
            print(f"    ❌ Upload failed: {local_path.name} — {err}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    ❌ Upload timed out: {local_path.name}")
        return False


def find_or_create_folder(name: str, parent_id: str, dry_run: bool) -> str:
    """Find a Drive folder by name under parent, or create it. Returns folder ID."""
    if dry_run:
        return f"[dry-run-folder:{name}]"

    # Search for existing folder
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    try:
        result = subprocess.run(
            [GWS, "drive", "files", "list",
             "--params", json.dumps({"q": query, "fields": "files(id,name)", "pageSize": 1})],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            files = data.get("files", [])
            if files:
                return files[0]["id"]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        pass

    # Create folder
    metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]

    result = subprocess.run(
        [GWS, "drive", "files", "create",
         "--json", json.dumps(metadata),
         "--params", '{"fields": "id"}'],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return data["id"]

    raise RuntimeError(f"Could not create folder '{name}': {result.stderr.strip()}")


def find_or_create_folder_path(path: str, parent_id: str, dry_run: bool) -> str:
    """Find/create a nested Drive folder path under parent_id."""
    current_parent = parent_id
    for part in [item for item in path.split("/") if item]:
        current_parent = find_or_create_folder(part, current_parent, dry_run)
    return current_parent


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync Tender Export OS outputs to Google Drive using gws CLI"
    )
    parser.add_argument("--execute", action="store_true",
                        help="Actually upload files. Default is dry-run (safe).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Force dry-run mode. This is the default.")
    parser.add_argument("--mode", choices=sorted(MODE_SYNC_GROUPS), default="private-runtime",
                        help="Projection mode label for the manifest; dry-run remains safe in every mode.")
    parser.add_argument("--all", action="store_true",
                        help="Sync all groups. Requires DRIVE_ROOT_FOLDER_ID.")
    parser.add_argument("--group", default="",
                        help="Sync a single group (e.g. daily_briefs, 01_Daily_Briefs).")
    parser.add_argument("--check-auth", action="store_true",
                        help="Check gws auth and exit.")
    parser.add_argument("--folder-id", default="",
                        help="Override DRIVE_ROOT_FOLDER_ID for this run.")
    parser.add_argument("--output", default=str(DEFAULT_MANIFEST_OUTPUT),
                        help="Write a local sync manifest JSON for review.")
    args = parser.parse_args()

    if args.check_auth:
        return 0 if check_auth() else 1

    dry_run = args.dry_run or not args.execute

    if dry_run:
        print("=== DRY RUN — no files will be uploaded ===")
        print("Add --execute to upload. Requires gws auth login -s drive")
        print()

    root_folder_id = args.folder_id or DRIVE_ROOT_FOLDER_ID or load_setup_root_folder_id()
    if args.execute and not root_folder_id:
        print("❌ DRIVE_ROOT_FOLDER_ID is not set.")
        print("   Set env var DRIVE_ROOT_FOLDER_ID to the Drive folder ID of your Knowledge Bus root.")
        print("   Find it in the URL: https://drive.google.com/drive/folders/<FOLDER_ID>")
        print("   Or run: gws drive files list --params '{\"q\": \"name=\\'Tender Export OS - Knowledge Bus\\' and trashed=false\"}'")
        return 1

    if args.execute and not check_auth():
        print("Run: gws auth login -s drive,sheets")
        return 1

    available_groups = MODE_SYNC_GROUPS[args.mode]

    # Determine which groups to sync
    if args.group:
        # Match by key or by short name
        groups_to_sync = {}
        for k, v in available_groups.items():
            if args.group.lower() in k.lower():
                groups_to_sync[k] = v
        if not groups_to_sync:
            print(f"❌ Group '{args.group}' not found for mode '{args.mode}'. Available: {list(available_groups.keys())}")
            return 1
    else:
        groups_to_sync = available_groups

    group_files = {
        group_name: expand_patterns(patterns if isinstance(patterns, list) else [patterns])
        for group_name, patterns in groups_to_sync.items()
    }
    selected_files = sorted({path for files in group_files.values() for path in files})
    content_findings = pre_upload_content_scan(selected_files, args.mode)
    if content_findings:
        print("❌ Pre-upload content scan failed:")
        for finding in content_findings:
            print(f"FAIL: {finding}")
        return 1

    total_files = 0
    total_ok = 0
    total_fail = 0
    manifest = {
        "drive_root_name": "Tender Export OS - Knowledge Bus",
        "mode": "execute" if args.execute else "dry_run",
        "projection_mode": args.mode,
        "warning": "Review this manifest before any Drive upload. Secrets and restricted files are filtered locally.",
        "groups": [],
        "never_sync_patterns": NEVER_SYNC_PATTERNS,
        "never_sync_extensions": sorted(NEVER_SYNC_EXTENSIONS),
    }

    for group_name, patterns in groups_to_sync.items():
        files = group_files[group_name]
        manifest["groups"].append({
            "drive_folder": group_name,
            "files": [str(path.relative_to(PROJECT_ROOT)) for path in files],
        })
        print(f"\n📁 {group_name} ({len(files)} files)")

        if not files:
            print("    (no files matched)")
            continue

        # Find/create subfolder
        try:
            folder_id = find_or_create_folder_path(group_name, root_folder_id, dry_run)
        except RuntimeError as e:
            print(f"  ❌ Folder error: {e}")
            continue

        for f in files:
            total_files += 1
            ok = gws_upload(f, folder_id, dry_run)
            if ok:
                total_ok += 1
            else:
                total_fail += 1

    print(f"\n=== Sync complete: {total_ok}/{total_files} OK, {total_fail} failed ===")
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote sync manifest: {output}")
    if dry_run:
        print("Re-run with --execute to actually upload.")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
