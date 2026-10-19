#!/usr/bin/env python3
"""Fail-closed preflight guard for consequential Tender OS business actions.

This command never performs the requested action. It verifies policy and the
owner approval receipt, then emits a sanitized attempt receipt for the external
connector or owner-operated workflow to consume.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

try:
    from scripts.event_ledger import append_event
    from scripts.tender_os_policy import (
        PROJECT_ROOT,
        TenderPolicyEngine,
        display_path,
        iso_utc,
        now_utc,
        SingleUseApprovalStore,
        canonical_effect_intent_hash,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import append_event  # type: ignore
    from tender_os_policy import (  # type: ignore
        PROJECT_ROOT,
        TenderPolicyEngine,
        display_path,
        iso_utc,
        now_utc,
        SingleUseApprovalStore,
        canonical_effect_intent_hash,
    )


DEFAULT_RECEIPT_ROOT = PROJECT_ROOT / "receipts" / "business_effect_attempts"


def classify_decision(decision: dict[str, Any]) -> str:
    if decision.get("allow") is True:
        return "allowed"
    if str(decision.get("reason_code", "")).startswith("POLICY_"):
        return "failed"
    return "blocked_missing_approval"


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def guard_business_effect(
    action: str,
    *,
    case_id: str = "",
    approval_id: str = "",
    actor: str = "hermes_business_effect_guard",
    engine: TenderPolicyEngine | None = None,
    receipt_root: Path = DEFAULT_RECEIPT_ROOT,
    record_event: bool = True,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = engine or TenderPolicyEngine()
    decision = policy.evaluate(
        action,
        case_id=case_id,
        approval_id=approval_id,
        actor=actor,
        record=True,
    )
    status = classify_decision(decision)
    stamp = now_utc()
    intent_hash = canonical_effect_intent_hash(
        action=str(decision.get("action") or action),
        case_id=case_id,
        approval_id=approval_id,
        intent=intent,
    )
    claim_result: dict[str, Any] = {"claimed": False, "reason_code": "NOT_REQUIRED"}
    if bool(decision.get("allow")) and bool(decision.get("approval_required")):
        scope_hash = str(decision.get("approval", {}).get("scope_hash", ""))
        store = SingleUseApprovalStore(receipt_root / "approval_consumption.sqlite3")
        claim_result = store.claim(
            approval_id=approval_id,
            intent_hash=intent_hash,
            scope_hash=scope_hash,
            claimed_at=iso_utc(stamp),
        )
        if not claim_result.get("claimed"):
            status = "blocked_replay" if claim_result.get("reason_code") == "APPROVAL_REPLAY" else "blocked_intent_drift" if claim_result.get("reason_code") == "APPROVAL_INTENT_DRIFT" else "failed"
            decision["allow"] = False
            decision["reason_code"] = str(claim_result.get("reason_code", "APPROVAL_CLAIM_FAILED"))
    attempt_id = f"BEA-{stamp.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:10]}"
    receipt_path = receipt_root / f"{attempt_id}.json"
    receipt = {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "attempted_at": iso_utc(stamp),
        "status": status,
        "action": str(decision.get("action") or action),
        "case_id": case_id,
        "approval_id": approval_id,
        "approval_receipt_id": str(
            decision.get("approval", {}).get("receipt_id", "")
        ),
        "approval_claim": {
            "status": str(claim_result.get("reason_code", "")),
            "intent_sha256": intent_hash,
            "scope_hash": str(decision.get("approval", {}).get("scope_hash", "")),
        },
        "policy_decision_id": str(decision.get("decision_id", "")),
        "policy_receipt_path": str(decision.get("receipt_path", "")),
        "reason_code": str(decision.get("reason_code", "")),
        "actor": actor,
        "external_action_executed": False,
        "safety": "Identifiers only; no credentials or raw business payload stored.",
    }
    try:
        atomic_json(receipt_path, receipt)
        receipt["receipt_path"] = display_path(receipt_path, root=PROJECT_ROOT)
        if record_event:
            append_event(
                "business_effect.attempt_recorded",
                actor,
                case_id=case_id,
                object_type="business_effect_attempt",
                object_id=attempt_id,
                source="business_effect_guard",
                payload={
                    "attempt_id": attempt_id,
                    "status": status,
                    "action": receipt["action"],
                    "approval_id": approval_id
                    or (
                        "MISSING"
                        if bool(decision.get("approval_required"))
                        else "NOT_REQUIRED"
                    ),
                    "policy_decision_id": receipt["policy_decision_id"],
                    "receipt_path": receipt["receipt_path"],
                    "external_action_executed": False,
                },
                citations=[
                    str(decision.get("receipt_path", "")),
                    receipt["receipt_path"],
                ],
                events_file=policy.events_file,
            )
    except (OSError, ValueError) as exc:
        receipt.update(
            {
                "status": "failed",
                "reason_code": "BUSINESS_EFFECT_AUDIT_WRITE_FAILED",
                "error": type(exc).__name__,
                "receipt_path": "",
            }
        )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True)
    parser.add_argument("--case-id", default="")
    parser.add_argument("--approval-id", default="")
    parser.add_argument("--actor", default="hermes_business_effect_guard")
    args = parser.parse_args()
    result = guard_business_effect(
        args.action,
        case_id=args.case_id,
        approval_id=args.approval_id,
        actor=args.actor,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return {"allowed": 0, "blocked_missing_approval": 3, "blocked_replay": 3, "blocked_intent_drift": 3, "failed": 4}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
