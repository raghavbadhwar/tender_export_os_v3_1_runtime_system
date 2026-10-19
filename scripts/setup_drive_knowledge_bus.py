#!/usr/bin/env python3
"""Create the Google Drive Knowledge Bus folder tree."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GWS = os.environ.get("GWS_BIN", "gws")
DEFAULT_STATE = PROJECT_ROOT / "outputs" / "drive_knowledge_bus_setup.json"
ROOT_NAME = "Tender Export OS - Knowledge Bus"

FOLDER_PATHS = [
    "00_Project_Context/01_Instructions",
    "00_Project_Context/02_State_Snapshots",
    "00_Project_Context/03_Context_Receipts",
    "00_Control_Center",
    "00_Schemas",
    "01_Daily_Briefs",
    "02_Case_Reports",
    "03_Bid_Packs",
    "04_Export_Quote_Packs",
    "05_Supplier_Proof",
    "06_Receipts/approvals",
    "06_Receipts/owner_decisions",
    "06_Receipts/supplier_quotes",
    "06_Receipts/submissions",
    "06_Receipts/plugin_runs",
    "07_Config_Snapshots",
    "08_ChatGPT_Bridge/01_To_ChatGPT",
    "08_ChatGPT_Bridge/02_From_ChatGPT",
    "08_ChatGPT_Bridge/03_Reviewed_For_Codex_Hermes",
    "09_Plugin_Produced_Artifacts/Excel_Models",
    "09_Plugin_Produced_Artifacts/PDF_Packs",
    "09_Plugin_Produced_Artifacts/DOCX_Proposals",
    "09_Plugin_Produced_Artifacts/PPTX_Decks",
    "09_Plugin_Produced_Artifacts/Invoices",
    "09_Plugin_Produced_Artifacts/Email_Sequences",
    "09_Plugin_Produced_Artifacts/Dashboards",
    "10_Archive",
]


def run_gws(args: list[str]) -> dict:
    result = subprocess.run([GWS, *args], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout) if result.stdout.strip() else {}


def find_folder(name: str, parent_id: str = "") -> str:
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    data = run_gws([
        "drive", "files", "list",
        "--params", json.dumps({"q": query, "fields": "files(id,name,webViewLink)", "pageSize": 1}),
    ])
    files = data.get("files", [])
    return files[0]["id"] if files else ""


def create_folder(name: str, parent_id: str = "") -> str:
    metadata: dict[str, object] = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]
    data = run_gws([
        "drive", "files", "create",
        "--json", json.dumps(metadata),
        "--params", json.dumps({"fields": "id,name,webViewLink"}),
    ])
    return data["id"]


def find_or_create(name: str, parent_id: str, execute: bool) -> tuple[str, str]:
    existing = find_folder(name, parent_id) if execute else ""
    if existing:
        return existing, "existing"
    if execute:
        return create_folder(name, parent_id), "created"
    return f"[dry-run-folder:{name}]", "would_create"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the Drive Knowledge Bus folder tree")
    parser.add_argument("--execute", action="store_true", help="Actually create folders in Drive")
    parser.add_argument("--output", default=str(DEFAULT_STATE), help="State/receipt output JSON")
    args = parser.parse_args()

    root_id, root_action = find_or_create(ROOT_NAME, "", args.execute)
    folders = []
    for folder_path in FOLDER_PATHS:
        parent = root_id
        built = []
        for part in folder_path.split("/"):
            built.append(part)
            folder_id, action = find_or_create(part, parent, args.execute)
            folders.append({
                "path": "/".join(built),
                "id": folder_id,
                "action": action,
            })
            parent = folder_id

    state = {
        "drive_root_name": ROOT_NAME,
        "mode": "execute" if args.execute else "dry_run",
        "created_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "root_folder_id": root_id,
        "root_action": root_action,
        "folders": folders,
        "communication_bridge": "08_ChatGPT_Bridge",
        "chatgpt_to_codex_hermes": "08_ChatGPT_Bridge/02_From_ChatGPT",
        "codex_hermes_to_chatgpt": "08_ChatGPT_Bridge/01_To_ChatGPT",
        "safety_note": "Folder setup only. No bids, quotes, supplier messages, payments, or compliance claims are executed.",
    }
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"{'Created/verified' if args.execute else 'Planned'} Drive Knowledge Bus: {ROOT_NAME}")
    print(f"Root folder id: {root_id}")
    print(f"Wrote setup state: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
