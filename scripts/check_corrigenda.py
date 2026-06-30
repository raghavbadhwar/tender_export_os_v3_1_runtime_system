#!/usr/bin/env python3
"""Detect tender corrigenda changes and emit review-safe status."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

from scripts.event_ledger import append_event

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def corrigendum_hash(items: Iterable[dict]) -> str:
    normalized = json.dumps(list(items), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def detect_corrigenda(case_id: str, previous_hash: str, items: list[dict]) -> dict:
    current = corrigendum_hash(items)
    changed = bool(items) and current != (previous_hash or "")
    return {
        "case_id": case_id,
        "corrigenda_count": len(items),
        "corrigendum_hash": current,
        "corrigenda_status": "CHANGED_REVIEW_REQUIRED" if changed else "NO_CHANGE",
        "changed": changed,
        "summary": "; ".join(str(item.get("title", item.get("url", ""))) for item in items[:5]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check corrigenda from a JSON fixture or discovered links")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--input", required=True, help="JSON list of corrigenda items")
    parser.add_argument("--previous-hash", default="")
    parser.add_argument("--record-event", action="store_true")
    args = parser.parse_args()
    path = Path(args.input)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    items = json.loads(path.read_text(encoding="utf-8"))
    result = detect_corrigenda(args.case_id, args.previous_hash, items)
    if args.record_event and result["changed"]:
        append_event(
            "corrigendum.detected",
            "check_corrigenda",
            case_id=args.case_id,
            object_type="corrigendum",
            object_id=result["corrigendum_hash"],
            payload=result,
            citations=[str(path.relative_to(PROJECT_ROOT))],
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
