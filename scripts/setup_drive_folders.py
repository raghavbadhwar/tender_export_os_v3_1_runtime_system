#!/usr/bin/env python3
"""Plan Google Drive Knowledge Bus folders with local write locking."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.drive_writer import PROJECT_ROOT, build_drive_plan
from scripts.setup_drive_knowledge_bus import FOLDER_PATHS, ROOT_NAME


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or execute Drive folder setup")
    parser.add_argument("--dry-run", action="store_true", help="Plan only. This is the default and safe mode.")
    parser.add_argument("--execute", action="store_true", help="Reserved for connector-backed setup; dry-run remains recommended.")
    parser.add_argument("--output", default="outputs/drive_folder_setup_plan.json")
    args = parser.parse_args()
    execute = bool(args.execute and not args.dry_run)
    plan = build_drive_plan(FOLDER_PATHS, Path(args.output), execute=execute)
    plan["drive_root_name"] = ROOT_NAME
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"{'Execute plan' if execute else 'Dry-run plan'} written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
