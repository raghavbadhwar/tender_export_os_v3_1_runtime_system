"""Dry-run first Drive writer facade.

This module records planned Google Drive writes and centralizes the safety rule:
no upload happens unless an explicit caller passes ``execute=True``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from scripts.lib.shared_brain_write_lock import write_lock


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_drive_plan(folder_paths: Iterable[str], output: Path, execute: bool = False) -> dict:
    output = output if output.is_absolute() else PROJECT_ROOT / output
    with write_lock():
        plan = {
            "mode": "execute" if execute else "dry_run",
            "drive_root_name": "Tender Export OS - Knowledge Bus",
            "folders": [{"path": path, "action": "would_create_or_verify" if not execute else "requires_connector_execute"} for path in folder_paths],
            "safety_note": "No upload, external send, bid submission, payment, DSC use, or compliance claim is performed by dry-run planning.",
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        return plan
