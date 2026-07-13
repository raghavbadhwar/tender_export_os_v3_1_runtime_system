#!/usr/bin/env python3
"""Generate final production-readiness receipt or blocker summary."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.record_computer_use_read_only_canary import validate_canary_receipt
from scripts.validate_contact_form_lane import validate_contact_form_lane


PLAN = PROJECT_ROOT / "plan" / "upgrade-hermes-tender-export-os-1.md"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "production_readiness"
OWNER_SIGNOFF = PROJECT_ROOT / "receipts" / "production_readiness" / "owner_signoff.json"
BLOCKING_TASKS = {
    "TASK-092": {
        "reason": "clean 14-day shadow pilot still pending",
        "owner": "Hermes Chief Operator",
        "next_action": "Run an explicitly activated shadow pilot for 14 clean days with no external-action markers or policy violations.",
        "proof_required": "A shadow pilot report with status PASS and production_routing_enabled=false.",
        "current_evidence": "outputs/shadow_pilot/",
    },
    "TASK-093": {
        "reason": "production routing gate blocked until TASK-092 passes",
        "owner": "Hermes Chief Operator",
        "next_action": "Evaluate each profile after the clean pilot and keep failing profiles in shadow or disabled state.",
        "proof_required": "A profile routing readiness report showing eligible profiles and production_routing_enabled=false until owner signoff.",
        "current_evidence": "outputs/profile_routing_readiness/",
    },
    "TASK-095": {
        "reason": "contact-form connector design is drafted but not owner-approved or enabled",
        "owner": "Owner + Tooling Integration Lead",
        "next_action": "Review config/contact_form_connector_design.yaml and explicitly approve, reject, or request changes. Production stays disabled until approval is recorded.",
        "proof_required": "Approved connector design receipt plus passing lane/design validators; production_enabled must remain false until approval.",
        "current_evidence": "config/contact_form_lane.yaml and config/contact_form_connector_design.yaml",
    },
    "TASK-096": {
        "reason": "live Drive sync proof blocked by auth timeout",
        "owner": "Owner",
        "next_action": "Renew or repair Google Drive/gws auth, then rerun the Knowledge Bus revalidation with a non-sensitive packet.",
        "proof_required": "Drive revalidation report proving dry-run routing and live auth check success; live upload only if explicitly authorized.",
        "current_evidence": "outputs/drive_revalidation/",
    },
    "TASK-097": {
        "reason": "Computer Use readiness and an owner-approved read-only canary are required before any portal-assist session",
        "owner": "Owner + Hermes Chief Operator",
        "next_action": "When desktop readiness passes, create a case-scoped read-only-canary approval, manually observe only a public-page canary, and record its evidence. Portal assist remains disabled.",
        "proof_required": "Computer Use readiness status READY_FOR_READ_ONLY_CANARY plus a PASS read-only canary receipt with a matching case-scoped approval; portal_assist_enabled must remain false.",
        "current_evidence": "outputs/computer_use_readiness/",
    },
    "TASK-101": {
        "reason": "30-day production pilot prepared but not activated; prerequisite gates still pending",
        "owner": "Hermes Chief Operator + Owner",
        "next_action": "After TASK-092 and TASK-093 pass, explicitly activate the 30-day production pilot and complete it with weekly owner reviews.",
        "proof_required": "Production pilot report with pass criteria met, weekly review evidence, and production_external_authority_expanded=false unless separately approved.",
        "current_evidence": "outputs/production_pilot/",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    return payload if isinstance(payload, dict) else {}


def latest_file(pattern: str) -> Path | None:
    files = sorted(PROJECT_ROOT.glob(pattern), key=lambda path: path.stat().st_mtime if path.exists() else 0)
    return files[-1] if files else None


def latest_json(pattern: str) -> tuple[Path | None, dict[str, Any]]:
    path = latest_file(pattern)
    return path, load_json(path) if path else {}


def has_contact_form_approval() -> bool:
    lane = load_yaml(PROJECT_ROOT / "config" / "contact_form_lane.yaml")
    return validate_contact_form_lane(lane).get("status") == "PASS"


def has_owner_signoff() -> bool:
    signoff = load_json(OWNER_SIGNOFF)
    return signoff.get("approved") is True and bool(signoff.get("approved_at")) and bool(signoff.get("approved_by"))


def evidence_snapshot() -> dict[str, Any]:
    shadow_path, shadow = latest_json("outputs/shadow_pilot/shadow_pilot_*.json")
    routing_path, routing = latest_json("outputs/profile_routing_readiness/profile_routing_readiness_*.json")
    drive_path, drive = latest_json("receipts/drive_setup/knowledge_bus_revalidation_*.json")
    computer_path, computer = latest_json("outputs/computer_use_readiness/computer_use_readiness_*.json")
    canary_path, canary = latest_json("receipts/computer_use_canaries/*.json")
    if canary_path:
        canary_validation = validate_canary_receipt(canary)
    else:
        canary_validation = {"status": "MISSING", "errors": ["no read-only canary receipt found"]}
    production_path, production = latest_json("outputs/production_pilot/production_pilot_*.json")
    owner_action_path, owner_action = latest_json("outputs/production_readiness/owner_action_packet_*.json")
    gate_path, gate = latest_json("outputs/production_readiness/production_readiness_gate_*.json")
    plan_audit_path, plan_audit = latest_json("outputs/production_readiness/upgrade_plan_status_audit_*.json")
    return {
        "shadow_pilot": {"path": str(shadow_path) if shadow_path else "", "status": shadow.get("status")},
        "profile_routing": {
            "path": str(routing_path) if routing_path else "",
            "status": routing.get("status"),
            "eligible_profile_count": routing.get("eligible_profile_count"),
            "blockers": routing.get("blockers", []),
        },
        "contact_form": {"path": "config/contact_form_lane.yaml", "approved_connector_design": has_contact_form_approval()},
        "drive_revalidation": {
            "path": str(drive_path) if drive_path else "",
            "status": drive.get("status"),
            "remediation_steps": drive.get("remediation_steps", []),
        },
        "computer_use": {
            "path": str(computer_path) if computer_path else "",
            "status": computer.get("status"),
            "blockers": computer.get("blockers", []),
            "remediation_steps": computer.get("remediation_steps", []),
        },
        "computer_use_canary": {
            "path": str(canary_path) if canary_path else "",
            "status": canary_validation.get("status"),
            "errors": canary_validation.get("errors", []),
            "case_id": canary_validation.get("case_id", ""),
        },
        "production_pilot": {"path": str(production_path) if production_path else "", "status": production.get("status")},
        "owner_signoff": {"path": str(OWNER_SIGNOFF), "present": has_owner_signoff()},
        "owner_action_packet": {
            "path": str(owner_action_path) if owner_action_path else "",
            "blocking_task_count": owner_action.get("blocking_task_count"),
            "external_actions_executed": owner_action.get("external_actions_executed"),
            "production_routing_enabled": owner_action.get("production_routing_enabled"),
        },
        "production_readiness_gate": {
            "path": str(gate_path) if gate_path else "",
            "status": gate.get("status"),
            "command_count": gate.get("command_count"),
            "failure_count": gate.get("failure_count"),
            "external_actions_executed": gate.get("external_actions_executed"),
            "production_routing_enabled": gate.get("production_routing_enabled"),
        },
        "plan_status_audit": {
            "path": str(plan_audit_path) if plan_audit_path else "",
            "status": plan_audit.get("status"),
            "task_count": plan_audit.get("task_count"),
            "errors": plan_audit.get("errors", []),
            "warnings": plan_audit.get("warnings", []),
            "external_actions_executed": plan_audit.get("external_actions_executed"),
            "production_routing_enabled": plan_audit.get("production_routing_enabled"),
        },
    }


def build_blockers_from_evidence(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    checks = {
        "TASK-092": evidence["shadow_pilot"].get("status") == "PASS",
        "TASK-093": evidence["profile_routing"].get("status") == "PASS",
        "TASK-095": evidence["contact_form"].get("approved_connector_design") is True,
        "TASK-096": evidence["drive_revalidation"].get("status") == "PASS",
        "TASK-097": (
            evidence["computer_use"].get("status") == "READY_FOR_READ_ONLY_CANARY"
            and evidence["computer_use_canary"].get("status") == "PASS"
        ),
        "TASK-101": evidence["production_pilot"].get("status") == "PASS",
    }
    evidence_key = {
        "TASK-092": "shadow_pilot",
        "TASK-093": "profile_routing",
        "TASK-095": "contact_form",
        "TASK-096": "drive_revalidation",
        "TASK-097": "computer_use",
        "TASK-101": "production_pilot",
    }
    blockers: list[dict[str, Any]] = []
    for task_id, passed in checks.items():
        if passed:
            continue
        blocker = {"task_id": task_id, **BLOCKING_TASKS[task_id]}
        if task_id == "TASK-097":
            readiness_status = evidence["computer_use"].get("status") or "MISSING"
            canary_status = evidence["computer_use_canary"].get("status") or "MISSING"
            if readiness_status != "READY_FOR_READ_ONLY_CANARY":
                blocker["reason"] = f"Computer Use runtime readiness is {readiness_status}; read-only canary cannot proceed yet"
                blocker["next_action"] = "Repair the local Computer Use readiness blocker, rerun the readiness validator, then stop at the owner-approved read-only canary gate."
            elif canary_status != "PASS":
                blocker["reason"] = "Computer Use runtime is ready, but no valid owner-approved read-only canary receipt exists"
                blocker["next_action"] = "Create a case-scoped read-only-canary approval, manually observe only a public-page canary, then record its local evidence. Portal assist remains disabled."
        blocker["observed_evidence"] = evidence[evidence_key[task_id]]
        if task_id == "TASK-097":
            blocker["observed_evidence"] = {
                **evidence[evidence_key[task_id]],
                "canary": evidence["computer_use_canary"],
            }
        blockers.append(blocker)
    return blockers


def generate_receipt() -> dict:
    evidence = evidence_snapshot()
    blockers = build_blockers_from_evidence(evidence)
    owner_signoff_present = evidence["owner_signoff"]["present"] is True
    status = "BLOCKED" if blockers else ("READY" if owner_signoff_present else "READY_FOR_OWNER_SIGNOFF")
    return {
        "schema_version": "final_production_readiness_receipt.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "plan_path": str(PLAN),
        "evidence": evidence,
        "blocking_tasks": blockers,
        "blocker_owner_count": len({row["owner"] for row in blockers}),
        "all_blockers_have_owner_action_and_proof": all(
            row.get("owner") and row.get("next_action") and row.get("proof_required")
            for row in blockers
        ),
        "plan_completed": bool(not blockers and owner_signoff_present),
        "owner_signoff_present": owner_signoff_present,
        "owner_signoff_required": not owner_signoff_present,
        "external_authority_expanded": False,
        "note": "Implementation completion is not permission for autonomous external commitments.",
    }


def cli_payload(receipt: dict[str, Any], *, receipt_path: Path) -> dict[str, Any]:
    blockers = receipt.get("blocking_tasks") if isinstance(receipt.get("blocking_tasks"), list) else []
    task_ids = [str(row.get("task_id")) for row in blockers if isinstance(row, dict) and row.get("task_id")]
    return {
        "status": receipt["status"],
        "receipt": str(receipt_path),
        # Preserve the legacy count field while making the aggregate status
        # unambiguous and usable without reopening the JSON receipt.
        "blocking_tasks": len(blockers),
        "blocking_task_count": len(blockers),
        "blocking_task_ids": task_ids,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    receipt = generate_receipt()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"final_readiness_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    receipt["receipt_path"] = str(path)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    payload = cli_payload(receipt, receipt_path=path)
    print(json.dumps(payload, indent=2) if args.json else f"Final readiness {receipt['status']}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
