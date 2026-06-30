#!/usr/bin/env python3
"""Create a fallback Codex task file for manual/app-server-unavailable flows."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INBOX = PROJECT_ROOT / "runtime" / "codex_inbox"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create fallback Codex task")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--reason", default="Codex App-Server Runtime unavailable or not selected.")
    args = parser.parse_args()

    timestamp = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    path = INBOX / f"{timestamp}_{args.case_id}.json"
    INBOX.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "case_id": args.case_id,
        "task": args.task,
        "reason": args.reason,
        "approval_boundary": "No external, financial, legal, DSC, final quote, HSN/ITC-HS, origin, or delivery commitment action.",
        "status": "PENDING_CODEX_FALLBACK",
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
