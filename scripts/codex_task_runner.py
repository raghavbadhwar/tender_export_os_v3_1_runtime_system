#!/usr/bin/env python3
"""List fallback Codex inbox tasks. Execution remains manual and approval-gated."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INBOX = PROJECT_ROOT / "runtime" / "codex_inbox"


def main() -> int:
    INBOX.mkdir(parents=True, exist_ok=True)
    tasks = sorted(INBOX.glob("*.json"))
    if not tasks:
        print("No fallback Codex tasks found.")
        return 0
    for path in tasks:
        payload = json.loads(path.read_text(encoding="utf-8"))
        print(f"{path.name}: {payload.get('case_id')} | {payload.get('status')} | {payload.get('task')}")
    print("Use Codex App-Server Runtime when available. This runner intentionally does not execute external actions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
