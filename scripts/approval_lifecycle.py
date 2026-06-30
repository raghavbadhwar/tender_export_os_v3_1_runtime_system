#!/usr/bin/env python3
"""Approval timeout and execution lifecycle helpers."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - health checks install PyYAML
    yaml = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = PROJECT_ROOT / "config" / "approval_policy.yaml"

EXECUTION_TRANSITIONS = {
    "": {"AWAITING_EXECUTION"},
    "AWAITING_EXECUTION": {"SUPPLIER_RESPONSE_PENDING", "SUBMISSION_PENDING", "BUYER_RESPONSE_PENDING", "PAYMENT_PENDING"},
    "SUPPLIER_RESPONSE_PENDING": {"DOCUMENT_RECEIPT_PENDING", "FOLLOW_UP_DUE", "COMPLETED", "FAILED"},
    "SUBMISSION_PENDING": {"BUYER_RESPONSE_PENDING", "FOLLOW_UP_DUE", "COMPLETED", "FAILED"},
    "BUYER_RESPONSE_PENDING": {"FOLLOW_UP_DUE", "WON", "LOST", "COMPLETED", "FAILED"},
    "DOCUMENT_RECEIPT_PENDING": {"COMPLETED", "FOLLOW_UP_DUE", "FAILED"},
    "PAYMENT_PENDING": {"PAYMENT_RECEIVED", "FOLLOW_UP_DUE", "FAILED"},
    "FOLLOW_UP_DUE": {"SUPPLIER_RESPONSE_PENDING", "BUYER_RESPONSE_PENDING", "COMPLETED", "FAILED"},
    "PAYMENT_RECEIVED": {"COMPLETED"},
    "WON": {"COMPLETED"},
    "LOST": set(),
    "COMPLETED": set(),
    "FAILED": set(),
}


def parse_datetime(value: str, now: dt.datetime | None = None) -> dt.datetime:
    if not value:
        return now or dt.datetime.now(dt.timezone.utc)
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    if yaml is None:
        return {}
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def timeout_hours(policy: dict[str, Any] | None = None) -> int:
    policy = policy or load_policy()
    timeout = policy.get("approval_timeout_policy", {})
    try:
        return int(timeout.get("default_timeout_hours", 48))
    except (TypeError, ValueError):
        return 48


def approval_timeout_at(created_at: str, policy: dict[str, Any] | None = None) -> str:
    created = parse_datetime(created_at)
    return (created + dt.timedelta(hours=timeout_hours(policy))).isoformat()


def classify_approval(approval: dict[str, str], now: dt.datetime | None = None, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    current_time = now or dt.datetime.now(dt.timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=dt.timezone.utc)
    status = approval.get("approval_status", "")
    if status != "PENDING":
        return {"state": status or "UNKNOWN", "expired": False, "timeout_at": approval.get("approval_timeout_at", "")}
    created_at = approval.get("created_at") or approval.get("requested_at") or approval.get("approved_at") or current_time.isoformat()
    timeout_at = approval.get("approval_timeout_at") or approval_timeout_at(created_at, policy)
    expired = current_time >= parse_datetime(timeout_at)
    return {
        "state": "EXPIRED_APPROVAL" if expired else "PENDING",
        "expired": expired,
        "timeout_at": timeout_at,
        "next_status": "CHANGES_REQUESTED" if expired else "APPROVAL_REQUIRED",
    }


def validate_execution_transition(current: str, proposed: str) -> dict[str, Any]:
    allowed = EXECUTION_TRANSITIONS.get(current, set())
    return {
        "allowed": proposed in allowed,
        "current": current,
        "proposed": proposed,
        "allowed_next": sorted(allowed),
    }


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    parser = argparse.ArgumentParser(description="Review approval timeout and execution lifecycle state")
    parser.add_argument("--approvals", default=str(PROJECT_ROOT / "data" / "approvals_receipts.csv"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = [classify_approval(row) for row in load_csv(Path(args.approvals))]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(f"{result['state']} timeout_at={result.get('timeout_at', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
