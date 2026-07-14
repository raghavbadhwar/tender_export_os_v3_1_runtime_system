#!/usr/bin/env python3
"""Enqueue exception-first Hermes review cards without running models."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOARD = "tender-export-os"
ROUTE_ORCHESTRATOR = "teos-orchestrator"
ALLOWED_EXCEPTION_TRIGGERS = frozenset(
    {
        "deadline",
        "source_degradation",
        "failed_job",
        "substantive_reply",
        "approval_expiry",
        "quote_contradiction",
        "missing_receipt",
        "projection_contradiction",
        "overdue_payment",
        "forecast_maturity",
    }
)
Runner = Callable[..., subprocess.CompletedProcess[str]]
PRIORITY_VALUES = {"low": 25, "normal": 50, "high": 75, "urgent": 100}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def packet_exists(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def packet_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def exception_triggers(path: Path) -> list[str]:
    payload = packet_json(path)
    values = payload.get("trigger_types", payload.get("trigger_type", []))
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    return sorted({str(value).strip() for value in values if str(value).strip()} & ALLOWED_EXCEPTION_TRIGGERS)


def packet_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def latest_existing(pattern: str) -> Path | None:
    matches = [path for path in Path.cwd().glob(pattern) if packet_exists(path)]
    return max(matches, key=lambda path: path.stat().st_mtime) if matches else None


def idempotency_key(kind: str, packet_path: Path) -> str:
    resolved = str(packet_path.resolve())
    digest = hashlib.sha1(f"{kind}:{resolved}".encode("utf-8")).hexdigest()[:16]
    return f"agentic-review:{kind}:{digest}"


def card_payload(kind: str, *, title: str, assignee: str, packet_path: Path, prompt_path: str, priority: str = "normal") -> dict[str, Any] | None:
    if not packet_exists(packet_path):
        return None
    return {
        "kind": kind,
        "title": title,
        "board": BOARD,
        "project": BOARD,
        "status": "todo",
        "assignee": assignee,
        "route_via": ROUTE_ORCHESTRATOR if assignee != "tender-export-os" else ROUTE_ORCHESTRATOR,
        "priority": priority,
        "packet_path": rel(packet_path),
        "packet_sha256": packet_sha256(packet_path),
        "evidence_paths": [rel(packet_path)],
        "prompt_path": prompt_path,
        "idempotency_key": idempotency_key(kind, packet_path),
        "external_actions_allowed": False,
        "model_runs_executed_by_enqueuer": False,
        "max_in_progress_per_profile": 1,
        "required_completion_fields": [
            "case_id",
            "evidence",
            "gate",
            "artifact_paths",
            "validator_receipt_path",
            "stop_reason",
            "retry_method",
            "smallest_safe_next_action",
        ],
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }


def enqueue_morning_review(packet_path: Path) -> dict[str, Any] | None:
    return card_payload(
        "morning_review",
        title="Morning Chief Operator Review",
        assignee="tender-export-os",
        packet_path=packet_path,
        prompt_path="prompts/hermes/morning_chief_operator.md",
        priority="high",
    )


def enqueue_exceptions(packet_path: Path) -> dict[str, Any] | None:
    triggers = exception_triggers(packet_path)
    if not triggers:
        return None
    card = card_payload(
        "intraday_exception",
        title="Intraday Exception Officer Review",
        # The orchestrator deliberately has no file/packet-read capability.
        # Exception packets can span multiple cases, so route their evidence
        # review to the Chief Operator rather than weakening the orchestrator.
        assignee="tender-export-os",
        packet_path=packet_path,
        prompt_path="prompts/hermes/intraday_exception_officer.md",
        priority="high",
    )
    card["trigger_types"] = triggers
    card["trigger_validation"] = "allowlisted_canonical_event_types"
    return card


def enqueue_weekly_learning(packet_path: Path) -> dict[str, Any] | None:
    return card_payload(
        "weekly_learning",
        title="Weekly Learning Council",
        assignee="learning-evaluation",
        packet_path=packet_path,
        prompt_path="prompts/hermes/weekly_learning_council.md",
        priority="normal",
    )


def hermes_command(card: dict[str, Any]) -> list[str]:
    # Hermes Kanban accepts the task body as an option; its CLI does not accept
    # arbitrary task JSON or a --status=todo flag.  Keep the packet reference
    # and authority boundary in the durable task body rather than trying to
    # serialize a private packet into the command line.
    body = "\n".join(
        [
            "TEOS_AGENTIC_REVIEW_V1",
            f"Kind: {card['kind']}",
            f"Packet: {card['packet_path']}",
            f"Packet SHA256: {card['packet_sha256']}",
            f"Prompt: {card['prompt_path']}",
            f"Route via: {card['route_via']}",
            f"Required completion fields: {', '.join(card['required_completion_fields'])}",
            "External actions allowed: false",
            "The enqueuer did not run a model. Read the packet, cite evidence, and stop at every approval gate.",
        ]
    )
    return [
        "hermes",
        "kanban",
        "--board",
        BOARD,
        "create",
        card["title"],
        "--body",
        body,
        "--assignee",
        card["assignee"],
        "--priority",
        str(PRIORITY_VALUES.get(str(card["priority"]).lower(), PRIORITY_VALUES["normal"])),
        "--workspace",
        f"dir:{PROJECT_ROOT}",
        "--tenant",
        "agentic-review",
        "--idempotency-key",
        card["idempotency_key"],
        "--max-runtime",
        "900",
        "--max-retries",
        "1",
        "--created-by",
        "enqueue_agentic_reviews",
        "--json",
    ]


def run_cards(
    cards: list[dict[str, Any]],
    *,
    write: bool = False,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    commands = [hermes_command(card) for card in cards]
    results = []
    if write:
        for command in commands:
            completed = runner(command, cwd=PROJECT_ROOT, check=False, text=True, capture_output=True)
            results.append({"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    failure_count = sum(1 for item in results if item["returncode"] != 0)
    return {
        "status": "FAIL" if failure_count else "PASS",
        "kanban_mutated": bool(write and any(item["returncode"] == 0 for item in results)),
        "card_count": len(cards),
        "failure_count": failure_count,
        "cards": cards,
        "commands": commands,
        "results": results,
        "external_actions_executed": False,
        "model_runs_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--morning-packet", default="")
    parser.add_argument("--exception-packet", default="")
    parser.add_argument("--weekly-packet", default="")
    parser.add_argument("--morning-packet-glob", default="")
    parser.add_argument("--exception-packet-glob", default="")
    parser.add_argument("--weekly-packet-glob", default="")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    cards = []
    morning_packet = Path(args.morning_packet).expanduser() if args.morning_packet else latest_existing(args.morning_packet_glob) if args.morning_packet_glob else None
    exception_packet = Path(args.exception_packet).expanduser() if args.exception_packet else latest_existing(args.exception_packet_glob) if args.exception_packet_glob else None
    weekly_packet = Path(args.weekly_packet).expanduser() if args.weekly_packet else latest_existing(args.weekly_packet_glob) if args.weekly_packet_glob else None
    if morning_packet:
        card = enqueue_morning_review(morning_packet)
        if card:
            cards.append(card)
    if exception_packet:
        card = enqueue_exceptions(exception_packet)
        if card:
            cards.append(card)
    if weekly_packet:
        card = enqueue_weekly_learning(weekly_packet)
        if card:
            cards.append(card)
    result = run_cards(cards, write=args.write)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False))
    return 1 if args.write and result["failure_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
