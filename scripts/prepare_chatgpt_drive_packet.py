#!/usr/bin/env python3
"""Prepare a bounded Drive packet from Codex/Hermes to ChatGPT."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path

from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTBOX = PROJECT_ROOT / "outputs" / "chatgpt_bridge" / "to_chatgpt"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a bounded ChatGPT Drive packet")
    parser.add_argument("--topic", default="daily_boardroom_snapshot", help="Packet topic")
    parser.add_argument("--outbox", default=str(DEFAULT_OUTBOX), help="Local ChatGPT outbox directory")
    parser.add_argument("--record-event", action="store_true", help="Append chatgpt.packet_prepared event")
    args = parser.parse_args()

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in args.topic).strip("_")
    packet_dir = Path(args.outbox)
    if not packet_dir.is_absolute():
        packet_dir = PROJECT_ROOT / packet_dir
    packet_dir = packet_dir / f"{timestamp}_{safe_topic}"
    packet_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = packet_dir / "chatgpt_snapshot.md"
    subprocess.run(
        ["python3", "scripts/generate_chatgpt_snapshot.py", "--output", str(snapshot_path)],
        cwd=PROJECT_ROOT,
        check=True,
    )

    docs_to_copy = [
        PROJECT_ROOT / "docs" / "CHATGPT_BOARDROOM.md",
        PROJECT_ROOT / "chatgpt_project" / "project_instructions.md",
    ]
    copied_docs = []
    for source in docs_to_copy:
        if source.exists():
            dest = packet_dir / source.name
            shutil.copy2(source, dest)
            copied_docs.append(str(dest.relative_to(PROJECT_ROOT)))

    manifest = {
        "packet_id": f"CGPT-{timestamp}",
        "topic": args.topic,
        "created_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "direction": "codex_hermes_to_chatgpt",
        "drive_folder": "08_ChatGPT_Bridge/01_To_ChatGPT",
        "files": [
            str(snapshot_path.relative_to(PROJECT_ROOT)),
            *copied_docs,
        ],
        "boundary": [
            "Bounded snapshot only; not raw operational database.",
            "ChatGPT may research, synthesize, and recommend.",
            "ChatGPT must not approve, send, submit, classify finally, claim origin, or mutate registers.",
            "Returned output must go through 08_ChatGPT_Bridge/02_From_ChatGPT and Hermes/Codex review.",
        ],
        "return_contract": {
            "return_folder": "08_ChatGPT_Bridge/02_From_ChatGPT",
            "expected_sections": [
                "executive_summary",
                "cited_findings",
                "recommended_strategy",
                "risks_and_assumptions",
                "suggested_hermes_codex_follow_up_tasks",
                "evidence_gaps",
            ],
        },
    }
    manifest_path = packet_dir / "packet_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Prepared ChatGPT packet: {packet_dir}")

    if args.record_event:
        append_event(
            "chatgpt.packet_prepared",
            "prepare_chatgpt_drive_packet",
            object_type="chatgpt_packet",
            object_id=manifest["packet_id"],
            payload={"packet_dir": str(packet_dir.relative_to(PROJECT_ROOT)), "topic": args.topic},
            citations=[str(manifest_path.relative_to(PROJECT_ROOT)), str(snapshot_path.relative_to(PROJECT_ROOT))],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
