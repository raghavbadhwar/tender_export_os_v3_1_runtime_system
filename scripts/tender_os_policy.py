#!/usr/bin/env python3
"""Fail-closed OPA authorization for Tender Export OS tools and actions.

The model can name an action and an approval ID, but it cannot declare that an
approval is valid. This module resolves the action tier from versioned config,
checks the canonical local approval register plus card/owner-decision receipts,
and then asks OPA for the final decision.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

import yaml

try:
    from scripts.event_ledger import EVENTS_FILE, append_event
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import EVENTS_FILE, append_event  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "tender_tool_policy.yaml"
DEFAULT_REGO = PROJECT_ROOT / "policies" / "tender_os_authorization.rego"
DEFAULT_RECEIPT_ROOT = PROJECT_ROOT / "receipts" / "policy_decisions"


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_utc(value: dt.datetime | None = None) -> str:
    current = value or now_utc()
    if current.tzinfo is None:
        current = current.replace(tzinfo=dt.timezone.utc)
    return current.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat()


def parse_datetime(value: str) -> dt.datetime | None:
    if not str(value or "").strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def project_path(raw: str | Path, *, root: Path = PROJECT_ROOT) -> Path:
    path = Path(raw).expanduser()
    path = path if path.is_absolute() else root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes Tender OS root: {raw}") from exc
    return resolved


def display_path(path: Path, *, root: Path = PROJECT_ROOT) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


class TenderPolicyEngine:
    """Resolve local evidence and evaluate the final authorization in OPA."""

    def __init__(
        self,
        *,
        config_path: Path = DEFAULT_CONFIG,
        rego_path: Path = DEFAULT_REGO,
        approvals_path: Path | None = None,
        receipt_root: Path = DEFAULT_RECEIPT_ROOT,
        events_file: Path = EVENTS_FILE,
        project_root: Path = PROJECT_ROOT,
        opa_binary: str | None = None,
        clock: Any = now_utc,
    ) -> None:
        self.project_root = project_root.resolve()
        self.config_path = config_path.resolve()
        self.rego_path = rego_path.resolve()
        self.config = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        configured_approvals = self.config.get("approval_register", "data/approvals_receipts.csv")
        self.approvals_path = (
            approvals_path.resolve()
            if approvals_path is not None
            else project_path(configured_approvals, root=self.project_root)
        )
        self.receipt_root = receipt_root.resolve()
        self.events_file = events_file.resolve()
        self.opa_binary = opa_binary if opa_binary is not None else shutil.which("opa")
        self.clock = clock

    @property
    def actions(self) -> dict[str, dict[str, Any]]:
        value = self.config.get("actions", {})
        return value if isinstance(value, dict) else {}

    def action_spec(self, action: str) -> tuple[str, dict[str, Any]]:
        if action in self.actions:
            return action, dict(self.actions[action] or {})
        for canonical, raw_spec in self.actions.items():
            spec = dict(raw_spec or {})
            if action in [str(value) for value in spec.get("aliases", [])]:
                return canonical, spec
        return action, {
            "tier": 5,
            "mode": "unknown",
            "external_effect": True,
            "approval_required": False,
            "prohibited": True,
        }

    def _receipt_path(self, raw: str) -> Path | None:
        if not str(raw or "").strip():
            return None
        try:
            return project_path(raw, root=self.project_root)
        except ValueError:
            return None

    def _card_json_path(self, row: dict[str, str]) -> Path | None:
        card = self._receipt_path(row.get("approval_card_path", ""))
        if card is None:
            return None
        return card.with_suffix(".json")

    def _approval_candidates(
        self,
        canonical_action: str,
        spec: dict[str, Any],
        *,
        case_id: str,
        approval_id: str,
    ) -> list[dict[str, str]]:
        accepted_actions = {canonical_action, *[str(value) for value in spec.get("aliases", [])]}
        rows = load_csv(self.approvals_path)
        candidates = []
        for row in rows:
            if approval_id and row.get("approval_id") != approval_id:
                continue
            if case_id and row.get("case_id") != case_id:
                continue
            if row.get("action_approved") not in accepted_actions:
                continue
            candidates.append(row)
        return sorted(
            candidates,
            key=lambda row: row.get("approved_at") or row.get("requested_at") or "",
            reverse=True,
        )

    def _verify_one_approval(
        self,
        row: dict[str, str],
        canonical_action: str,
        spec: dict[str, Any],
        *,
        case_id: str,
    ) -> dict[str, Any]:
        failures: list[str] = []
        if row.get("approval_status") != "APPROVED":
            failures.append("approval status is not APPROVED")
        if not row.get("approved_by"):
            failures.append("approved_by is missing")
        if case_id and row.get("case_id") != case_id:
            failures.append("case scope does not match")

        if self.config.get("reject_reused_approval_after_external_effect", True):
            if row.get("external_effect") != "PENDING_APPROVED_EXECUTION":
                failures.append("approval is already executed, consumed, or not execution-ready")

        owner_receipt_path = self._receipt_path(row.get("receipt_path", ""))
        owner_receipt = load_json(owner_receipt_path) if owner_receipt_path and owner_receipt_path.is_file() else {}
        if self.config.get("require_owner_decision_receipt", True):
            if not owner_receipt:
                failures.append("owner decision receipt is missing or unreadable")
            else:
                if owner_receipt.get("approval_id") != row.get("approval_id"):
                    failures.append("owner decision receipt approval_id mismatch")
                if owner_receipt.get("case_id") != row.get("case_id"):
                    failures.append("owner decision receipt case_id mismatch")
                if owner_receipt.get("decision_status") != "APPROVED":
                    failures.append("owner decision receipt is not approved")
                accepted_actions = {canonical_action, *[str(value) for value in spec.get("aliases", [])]}
                if owner_receipt.get("action_approved") not in accepted_actions:
                    failures.append("owner decision receipt action mismatch")
                if owner_receipt.get("external_effect") != "PENDING_APPROVED_EXECUTION":
                    failures.append("owner decision receipt is consumed or not execution-ready")

        card_json_path = self._card_json_path(row)
        card = load_json(card_json_path) if card_json_path and card_json_path.is_file() else {}
        scope_hash = row.get("scope_hash", "")
        if self.config.get("require_scope_hash", True):
            if not scope_hash:
                failures.append("approval scope hash is missing")
            elif not card:
                failures.append("structured approval card is missing or unreadable")
            elif card.get("scope_hash") != scope_hash:
                failures.append("approval scope hash does not match card")
            elif card.get("case_id") != row.get("case_id"):
                failures.append("approval card case scope mismatch")
            elif card.get("proposed_action") not in {
                canonical_action,
                *[str(value) for value in spec.get("aliases", [])],
            }:
                failures.append("approval card action scope mismatch")

        timeout = parse_datetime(row.get("approval_timeout_at", ""))
        if timeout is None and card:
            timeout = parse_datetime(str(card.get("approval_timeout_at", "")))
        if timeout is None:
            approved_at = parse_datetime(row.get("approved_at", ""))
            if approved_at is not None:
                timeout = approved_at + dt.timedelta(
                    hours=int(self.config.get("approval_max_age_hours", 48))
                )
        current = self.clock()
        if current.tzinfo is None:
            current = current.replace(tzinfo=dt.timezone.utc)
        if timeout is None:
            failures.append("approval expiry cannot be established")
        elif current.astimezone(dt.timezone.utc) >= timeout:
            failures.append("approval is expired")

        required_controls = [str(value) for value in spec.get("required_controls", [])]
        receipt_controls = owner_receipt.get("controls", {}) if isinstance(owner_receipt, dict) else {}
        if not isinstance(receipt_controls, dict):
            receipt_controls = {}
        missing_controls = [name for name in required_controls if receipt_controls.get(name) is not True]

        return {
            "valid": not failures,
            "reason": "; ".join(failures) if failures else "current scoped owner approval verified",
            "approval_id": row.get("approval_id", ""),
            "case_id": row.get("case_id", ""),
            "receipt_id": row.get("receipt_id", ""),
            "receipt_path": display_path(owner_receipt_path, root=self.project_root) if owner_receipt_path else "",
            "scope_hash": scope_hash,
            "expires_at": iso_utc(timeout) if timeout else "",
            "required_controls": required_controls,
            "missing_controls": missing_controls,
            "controls_satisfied": not missing_controls,
            "controls_reason": (
                f"required controls missing from owner receipt: {', '.join(missing_controls)}"
                if missing_controls
                else "all required controls verified"
            ),
        }

    def verify_approval(
        self,
        canonical_action: str,
        spec: dict[str, Any],
        *,
        case_id: str,
        approval_id: str,
    ) -> dict[str, Any]:
        if not spec.get("approval_required", False):
            return {
                "valid": True,
                "reason": "approval is not required for this action",
                "approval_id": "",
                "case_id": case_id,
                "receipt_id": "",
                "receipt_path": "",
                "scope_hash": "",
                "expires_at": "",
                "required_controls": [],
                "missing_controls": [],
                "controls_satisfied": True,
                "controls_reason": "no special controls required",
            }
        candidates = self._approval_candidates(
            canonical_action,
            spec,
            case_id=case_id,
            approval_id=approval_id,
        )
        if not candidates:
            return {
                "valid": False,
                "reason": "no matching local approval register row was found",
                "approval_id": approval_id,
                "case_id": case_id,
                "receipt_id": "",
                "receipt_path": "",
                "scope_hash": "",
                "expires_at": "",
                "required_controls": [str(value) for value in spec.get("required_controls", [])],
                "missing_controls": [str(value) for value in spec.get("required_controls", [])],
                "controls_satisfied": not spec.get("required_controls"),
                "controls_reason": "a valid approval must be verified before controls can unlock execution",
            }
        evaluations = [
            self._verify_one_approval(row, canonical_action, spec, case_id=case_id)
            for row in candidates
        ]
        for result in evaluations:
            if result["valid"]:
                return result
        return evaluations[0]

    def _opa_decision(self, input_document: dict[str, Any]) -> dict[str, Any]:
        if not self.opa_binary or not Path(self.opa_binary).exists():
            raise RuntimeError("OPA binary is unavailable")
        completed = subprocess.run(
            [
                self.opa_binary,
                "eval",
                "--format=json",
                "--data",
                str(self.rego_path),
                "--stdin-input",
                str(self.config.get("opa_package", "data.tenderos.authz.decision")),
            ],
            input=json.dumps(input_document),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()[:1000]
            raise RuntimeError(f"OPA evaluation failed: {detail}")
        payload = json.loads(completed.stdout)
        try:
            decision = payload["result"][0]["expressions"][0]["value"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("OPA returned no decision") from exc
        if not isinstance(decision, dict) or not isinstance(decision.get("allow"), bool):
            raise RuntimeError("OPA returned an invalid decision object")
        return decision

    def _record(self, decision: dict[str, Any], input_document: dict[str, Any]) -> str:
        self.receipt_root.mkdir(parents=True, exist_ok=True)
        receipt_path = self.receipt_root / f"{decision['decision_id']}.json"
        receipt = {
            "schema_version": 1,
            "decision": decision,
            "input": input_document,
            "safety": "No credential values or model-supplied approval assertions are stored.",
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        receipt_display = display_path(receipt_path, root=self.project_root)
        append_event(
            "policy.decision_recorded",
            "tender_os_policy",
            case_id=str(input_document.get("case_id", "")),
            object_type="policy_decision",
            object_id=str(decision["decision_id"]),
            source="opa_local",
            payload={
                "decision_id": decision["decision_id"],
                "action": decision["action"],
                "tier": decision["tier"],
                "allowed": decision["allow"],
                "status": decision["status"],
                "reason_code": decision["reason_code"],
                "approval_required": decision["approval_required"],
                "receipt_path": receipt_display,
                "policy_sha256": decision["policy_sha256"],
            },
            citations=[
                display_path(self.config_path, root=self.project_root),
                display_path(self.rego_path, root=self.project_root),
                receipt_display,
            ],
            events_file=self.events_file,
        )
        return receipt_display

    def evaluate(
        self,
        action: str,
        *,
        case_id: str = "",
        approval_id: str = "",
        actor: str = "hermes_mcp",
        record: bool = False,
    ) -> dict[str, Any]:
        canonical_action, spec = self.action_spec(action)
        approval = self.verify_approval(
            canonical_action,
            spec,
            case_id=case_id,
            approval_id=approval_id,
        )
        controls = {
            "satisfied": bool(approval.get("controls_satisfied", True)),
            "reason": str(approval.get("controls_reason", "")),
            "required": list(approval.get("required_controls", [])),
            "missing": list(approval.get("missing_controls", [])),
        }
        input_document = {
            "action": canonical_action,
            "requested_action": action,
            "actor": actor,
            "case_id": case_id,
            "tier": int(spec.get("tier", 5)),
            "mode": str(spec.get("mode", "unknown")),
            "external_effect": bool(spec.get("external_effect", True)),
            "approval_required": bool(spec.get("approval_required", False)),
            "prohibited": bool(spec.get("prohibited", False)),
            "credentials_present": False,
            "approval": approval,
            "controls": controls,
        }
        stamp = self.clock()
        decision_id = f"POL-{stamp.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:10]}"
        try:
            opa = self._opa_decision(input_document)
        except (OSError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            opa = {
                "allow": False,
                "status": "blocked",
                "reason_code": "POLICY_ENGINE_UNAVAILABLE",
                "reason": str(exc),
            }
        decision = {
            "decision_id": decision_id,
            "evaluated_at": iso_utc(stamp),
            "policy_name": str(self.config.get("policy_name", "")),
            "policy_version": self.config.get("version", 1),
            "policy_sha256": sha256_file(self.rego_path),
            "config_sha256": sha256_file(self.config_path),
            "action": canonical_action,
            "requested_action": action,
            "case_id": case_id,
            "tier": int(spec.get("tier", 5)),
            "mode": str(spec.get("mode", "unknown")),
            "allow": bool(opa.get("allow", False)),
            "status": str(opa.get("status", "blocked")),
            "reason_code": str(opa.get("reason_code", "POLICY_ENGINE_INVALID")),
            "reason": str(opa.get("reason", "Policy denied by default.")),
            "approval_required": bool(spec.get("approval_required", False)),
            "approval": approval,
            "required_controls": controls,
            "receipt_path": "",
        }
        if record:
            try:
                decision["receipt_path"] = self._record(decision, input_document)
            except (OSError, ValueError) as exc:
                decision.update(
                    {
                        "allow": False,
                        "status": "blocked",
                        "reason_code": "POLICY_AUDIT_WRITE_FAILED",
                        "reason": f"Policy decision could not be written to the canonical audit trail: {exc}",
                        "receipt_path": "",
                    }
                )
        return decision


def self_test() -> dict[str, Any]:
    engine = TenderPolicyEngine()
    low_risk = engine.evaluate("mcp.get_case", record=False)
    unapproved = engine.evaluate(
        "send_buyer_introductory_outreach",
        case_id="NONEXISTENT-CASE",
        record=False,
    )
    prohibited = engine.evaluate("captcha_bypass", record=False)
    checks = {
        "opa_policy_compiles": subprocess.run(
            [engine.opa_binary or "opa", "check", str(engine.rego_path)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode
        == 0
        if engine.opa_binary
        else False,
        "t0_allowed": low_risk.get("allow") is True,
        "unapproved_external_blocked": unapproved.get("allow") is False,
        "prohibited_blocked": prohibited.get("allow") is False
        and prohibited.get("reason_code") == "PROHIBITED_ACTION",
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", default="")
    parser.add_argument("--case-id", default="")
    parser.add_argument("--approval-id", default="")
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "PASS" else 1
    if not args.action:
        parser.error("--action is required unless --self-test is used")
    result = TenderPolicyEngine().evaluate(
        args.action,
        case_id=args.case_id,
        approval_id=args.approval_id,
        record=args.record,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["allow"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
