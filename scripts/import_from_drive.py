#!/usr/bin/env python3
"""
import_from_drive.py
Download files from Google Drive into the local project using the gws CLI.

Prerequisites:
  - gws CLI installed: brew install google-workspace-cli
  - Authenticated: gws auth login -s drive
  - DRIVE_ROOT_FOLDER_ID set (see sync_to_drive.py)

Usage:
  # Dry-run: show what would be downloaded (safe)
  python3 scripts/import_from_drive.py

  # Download the ChatGPT snapshot only
  python3 scripts/import_from_drive.py --execute --file chatgpt_snapshot.md

  # Download all control-center CSVs from Drive
  python3 scripts/import_from_drive.py --execute --group 00_Control_Center

  # Search Drive for a specific file by name
  python3 scripts/import_from_drive.py --search "master_cases"

Environment variables:
  DRIVE_ROOT_FOLDER_ID   Google Drive folder ID for "Tender Export OS - Knowledge Bus"
  GWS_BIN                Override path to gws binary (default: gws)

SAFETY RULES:
  - Never auto-overwrite local CSV registers without --force flag
  - Always review downloaded content before committing it
  - Never download credentials, tokens, DSC files, or bank details
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GWS = os.environ.get("GWS_BIN", "gws")
DRIVE_ROOT_FOLDER_ID = os.environ.get("DRIVE_ROOT_FOLDER_ID", "")
DEFAULT_IMPORT_PLAN_OUTPUT = PROJECT_ROOT / "outputs" / "drive_import_plan.json"

# Map Drive subfolder → local destination
IMPORT_MAP = {
    "00_Control_Center": {
        "events.jsonl": "data/events.jsonl",
        "master_cases.csv": "data/master_cases.csv",
        "supplier_master.csv": "data/supplier_master.csv",
        "approvals_receipts.csv": "data/approvals_receipts.csv",
        "source_health.csv": "data/source_health.csv",
        "plugin_health.csv": "data/plugin_health.csv",
        "quote_master.csv": "data/quote_master.csv",
        "agent_run_log.csv": "data/agent_run_log.csv",
    },
    "00_Schemas": {
        "master_cases.schema.json": "config/schemas/master_cases.schema.json",
        "approvals_receipts.schema.json": "config/schemas/approvals_receipts.schema.json",
        "quote_master.schema.json": "config/schemas/quote_master.schema.json",
        "supplier_master.schema.json": "config/schemas/supplier_master.schema.json",
        "event.schema.json": "config/schemas/event.schema.json",
    },
    "08_ChatGPT_Bridge/02_From_ChatGPT": {
        "chatgpt_return.md": "outputs/chatgpt_bridge/from_chatgpt/chatgpt_return.md",
    },
    "08_ChatGPT_Bridge/03_Reviewed_For_Codex_Hermes": {
        "review_plan.json": "outputs/chatgpt_bridge/reviewed/review_plan.json",
    },
}

NEVER_IMPORT_PATTERNS = [
    "secret", "token", "credential", "password", "cookie",
    "dsc", "bank", "private", ".enc", ".pem", ".p12", ".key",
]


def is_safe_name(name: str) -> bool:
    lower = name.lower()
    return not any(p in lower for p in NEVER_IMPORT_PATTERNS)


def gws_search(query: str) -> list[dict]:
    """Search Drive files. Returns list of {id, name, mimeType} dicts."""
    result = subprocess.run(
        [GWS, "drive", "files", "list",
         "--params", json.dumps({"q": query, "pageSize": 20,
                                 "fields": "files(id,name,mimeType,modifiedTime,webViewLink)"})],
        capture_output=True, text=True, timeout=20
    )
    if result.returncode != 0:
        print(f"❌ Search failed: {result.stderr.strip()}")
        return []
    data = json.loads(result.stdout)
    return data.get("files", [])


def gws_download(file_id: str, dest: Path, dry_run: bool) -> bool:
    """Download a Drive file to dest. Returns True on success."""
    if dry_run:
        print(f"    [dry-run] Would download: file_id={file_id} → {dest.relative_to(PROJECT_ROOT)}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [GWS, "drive", "files", "get",
         "--params", json.dumps({"fileId": file_id, "alt": "media"}),
         "--output", str(dest)],
        capture_output=True, timeout=60
    )
    if result.returncode == 0:
        print(f"    ✅ Downloaded: {dest.relative_to(PROJECT_ROOT)}")
        return True
    else:
        print(f"    ❌ Download failed: {dest.name} — {result.stderr.decode().strip()}")
        return False


def search_by_name(name: str) -> None:
    """Search Drive for files matching name and print results."""
    print(f"\nSearching Drive for: '{name}' ...")
    files = gws_search(f"name contains '{name}' and trashed=false")
    if not files:
        print("  No files found.")
        return
    for f in files:
        print(f"  {f['name']}")
        print(f"    ID: {f['id']}")
        print(f"    Type: {f['mimeType']}")
        print(f"    Modified: {f.get('modifiedTime', 'N/A')}")
        print(f"    Link: {f.get('webViewLink', 'N/A')}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import files from Google Drive to local project using gws CLI"
    )
    parser.add_argument("--execute", action="store_true",
                        help="Actually download files. Default is dry-run (safe).")
    parser.add_argument("--group", default="",
                        help="Import a specific group (e.g. 00_Control_Center, chatgpt_snapshots).")
    parser.add_argument("--file", default="",
                        help="Import a specific file by name (e.g. chatgpt_snapshot.md).")
    parser.add_argument("--file-id", default="",
                        help="Download a specific Drive file ID to --dest.")
    parser.add_argument("--dest", default="",
                        help="Local destination path for --file-id download.")
    parser.add_argument("--search", default="",
                        help="Search Drive by file name and show results (no download).")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing local files without prompt.")
    parser.add_argument("--output", default=str(DEFAULT_IMPORT_PLAN_OUTPUT),
                        help="Write a local import plan JSON for review.")
    args = parser.parse_args()

    dry_run = not args.execute

    if args.search:
        search_by_name(args.search)
        return 0

    if args.file_id:
        if not args.dest:
            print("❌ --dest is required with --file-id")
            return 1
        dest = Path(args.dest)
        if not dest.is_absolute():
            dest = PROJECT_ROOT / dest
        return 0 if gws_download(args.file_id, dest, dry_run) else 1

    if dry_run:
        print("=== DRY RUN — no files will be downloaded ===")
        print("Add --execute to download. Requires gws auth login -s drive")
        print()

    if args.execute:
        # Quick auth check
        result = subprocess.run(
            [GWS, "drive", "files", "list", "--params", '{"pageSize": 1}'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print("❌ gws not authenticated. Run: gws auth login -s drive")
            return 1
        print("✅ gws Drive auth OK")

    # Determine which groups to import
    if args.group:
        groups = {k: v for k, v in IMPORT_MAP.items() if args.group.lower() in k.lower()}
        if not groups:
            print(f"❌ Group '{args.group}' not found. Available: {list(IMPORT_MAP.keys())}")
            return 1
    else:
        groups = IMPORT_MAP

    total = 0
    ok = 0
    plan = {
        "drive_root_name": "Tender Export OS - Knowledge Bus",
        "mode": "execute" if args.execute else "dry_run",
        "warning": "Dry-run is offline and does not search or download from Drive. Review before any --execute import.",
        "local_review_required_before_overwrite": True,
        "groups": [],
        "never_import_patterns": NEVER_IMPORT_PATTERNS,
    }

    for group_name, file_map in groups.items():
        print(f"\n📁 {group_name}")
        group_plan = {"drive_folder": group_name, "files": []}
        plan["groups"].append(group_plan)
        for drive_name, local_rel in file_map.items():
            if args.file and args.file.lower() not in drive_name.lower():
                continue
            if not is_safe_name(drive_name):
                print(f"    ⛔ Skipped (never-import): {drive_name}")
                continue

            total += 1
            local_path = PROJECT_ROOT / local_rel
            group_plan["files"].append({
                "drive_name": drive_name,
                "local_path": local_rel,
                "exists_locally": local_path.exists(),
            })

            if local_path.exists() and not args.force and not dry_run:
                print(f"    ⚠️  Exists locally — skipping (use --force to overwrite): {local_rel}")
                continue

            if dry_run:
                print(f"    [dry-run] Would search Drive for {drive_name} → {local_rel}")
                ok += 1
                continue

            # Search Drive for this file
            files = gws_search(f"name='{drive_name}' and trashed=false")
            if not files:
                print(f"    ⚠️  Not found on Drive: {drive_name}")
                continue

            file_id = files[0]["id"]
            print(f"    Found: {files[0]['name']} (id={file_id})")
            if gws_download(file_id, local_path, dry_run):
                ok += 1

    print(f"\n=== Import complete: {ok}/{total} OK ===")
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"Wrote import plan: {output}")
    if dry_run:
        print("Re-run with --execute to actually download.")
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
