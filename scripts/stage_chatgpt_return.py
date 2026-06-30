#!/usr/bin/env python3
"""Stage a ChatGPT return for Hermes/Codex review without mutating state."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INBOX = PROJECT_ROOT / "outputs" / "chatgpt_bridge" / "from_chatgpt"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage a ChatGPT return for review")
    parser.add_argument("--input", required=True, help="Markdown/JSON return file from ChatGPT")
    parser.add_argument("--case-id", default="", help="Optional related case ID")
    parser.add_argument("--inbox", default=str(DEFAULT_INBOX), help="Local ChatGPT return inbox")
    parser.add_argument("--record-event", action="store_true", help="Append chatgpt.return_staged event")
    args = parser.parse_args()

    source = Path(args.input)
    if not source.is_absolute():
        source = PROJECT_ROOT / source
    if not source.exists():
        print(f"Input file not found: {source}")
        return 1

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    inbox = Path(args.inbox)
    if not inbox.is_absolute():
        inbox = PROJECT_ROOT / inbox
    staged_dir = inbox / f"{timestamp}_{args.case_id or 'general'}"
    staged_dir.mkdir(parents=True, exist_ok=True)

    staged_file = staged_dir / source.name
    shutil.copy2(source, staged_file)
    review_plan = {
        "return_id": f"CGPTRET-{timestamp}",
        "case_id": args.case_id,
        "staged_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "direction": "chatgpt_to_codex_hermes",
        "drive_folder": "08_ChatGPT_Bridge/02_From_ChatGPT",
        "staged_file": str(staged_file.relative_to(PROJECT_ROOT)),
        "review_required": True,
        "state_mutation_allowed": False,
        "required_review_steps": [
            "Check citations and evidence boundaries.",
            "Convert any accepted recommendation into a Hermes/Codex task or event.",
            "Do not update registers, send messages, submit bids, or confirm compliance from this return alone.",
            "Record owner approval before any gated external action.",
        ],
    }
    review_path = staged_dir / "review_plan.json"
    review_path.write_text(json.dumps(review_plan, indent=2), encoding="utf-8")
    print(f"Staged ChatGPT return: {staged_dir}")

    if args.record_event:
        append_event(
            "chatgpt.return_staged",
            "stage_chatgpt_return",
            case_id=args.case_id,
            object_type="chatgpt_return",
            object_id=review_plan["return_id"],
            payload={"staged_dir": str(staged_dir.relative_to(PROJECT_ROOT)), "case_id": args.case_id},
            citations=[str(staged_file.relative_to(PROJECT_ROOT)), str(review_path.relative_to(PROJECT_ROOT))],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
