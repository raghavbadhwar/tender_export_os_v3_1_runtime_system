#!/usr/bin/env python3
"""Generate a concise owner action packet from the latest production-readiness blockers."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "production_readiness"

TASK_GUIDANCE = {
    "TASK-092": {
        "priority": 1,
        "action_type": "wait_and_monitor",
        "owner_command": "Let the 14-day shadow pilot continue through its planned end date, then rerun readiness.",
        "verification_commands": [
            ".venv/bin/python scripts/run_shadow_profile_probes.py --write-log --write-evaluations --json",
            ".venv/bin/python scripts/generate_shadow_pilot_report.py --json",
            ".venv/bin/python scripts/evaluate_profile_production_routing.py --json",
        ],
        "external_authority_required": False,
    },
    "TASK-093": {
        "priority": 2,
        "action_type": "post_pilot_review",
        "owner_command": "After TASK-092 passes, review profile routing readiness; do not enable production routing before owner signoff.",
        "verification_commands": [
            ".venv/bin/python scripts/evaluate_profile_production_routing.py --json",
            ".venv/bin/python scripts/generate_final_readiness_receipt.py --json",
        ],
        "external_authority_required": False,
    },
    "TASK-095": {
        "priority": 3,
        "action_type": "explicit_owner_approval",
        "owner_command": (
            "If you approve only the contact-form connector design controls, run the approval recorder. "
            "This still does not authorize any specific form submission."
        ),
        "verification_commands": [
            ".venv/bin/python scripts/record_contact_form_connector_approval.py --approved-by owner --note 'Approve connector design controls only; no submissions authorized' --apply --json",
            ".venv/bin/python scripts/validate_contact_form_lane.py --json",
            ".venv/bin/python scripts/generate_final_readiness_receipt.py --json",
        ],
        "external_authority_required": True,
    },
    "TASK-096": {
        "priority": 4,
        "action_type": "external_auth_repair",
        "owner_command": "Renew Google Drive/gws auth with Drive scope, then rerun revalidation.",
        "verification_commands": [
            "gws auth login -s drive,sheets",
            ".venv/bin/python scripts/revalidate_drive_knowledge_bus_sync.py --json",
            ".venv/bin/python scripts/generate_final_readiness_receipt.py --json",
        ],
        "external_authority_required": True,
    },
    "TASK-097": {
        "priority": 5,
        "action_type": "owner_authorized_read_only_canary",
        "owner_command": "If runtime readiness is clear, approve one named case for a manually observable public-page canary. Do not enable portal assist or authorize login, form submission, upload, payment, DSC, CAPTCHA bypass, or commitments.",
        "verification_commands": [
            "hermes computer-use doctor",
            ".venv/bin/python scripts/validate_computer_use_readiness.py --json",
            ".venv/bin/python scripts/record_computer_use_read_only_canary.py --case-id <CASE_ID> --approval-reference <READ_ONLY_CANARY_APPROVAL_ID> --observed-by owner --observed-at <ISO8601_TIMESTAMP> --evidence <LOCAL_EVIDENCE_FILE> --write --json",
            ".venv/bin/python scripts/generate_final_readiness_receipt.py --json",
        ],
        "external_authority_required": True,
    },
    "TASK-101": {
        "priority": 6,
        "action_type": "production_pilot_activation_after_prereqs",
        "owner_command": "Activate the 30-day production pilot only after TASK-092 and TASK-093 pass and owner authorization is explicit.",
        "verification_commands": [
            ".venv/bin/python scripts/generate_production_pilot_report.py --prepare --json",
            ".venv/bin/python scripts/generate_final_readiness_receipt.py --json",
        ],
        "external_authority_required": True,
    },
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def latest_readiness_receipt(output_dir: Path = OUTPUT_DIR) -> tuple[Path | None, dict[str, Any]]:
    candidates = sorted(output_dir.glob("final_readiness_*.json"), key=lambda path: path.stat().st_mtime)
    if not candidates:
        return None, {}
    path = candidates[-1]
    return path, load_json(path)


def build_packet(readiness: dict[str, Any], *, readiness_path: Path | None = None, generated_at: str | None = None) -> dict[str, Any]:
    blockers = readiness.get("blocking_tasks") if isinstance(readiness.get("blocking_tasks"), list) else []
    actions: list[dict[str, Any]] = []
    for blocker in blockers:
        if not isinstance(blocker, dict):
            continue
        task_id = str(blocker.get("task_id") or "")
        guidance = TASK_GUIDANCE.get(task_id, {})
        actions.append(
            {
                "task_id": task_id,
                "priority": guidance.get("priority", 99),
                "action_type": guidance.get("action_type", "manual_review"),
                "owner": blocker.get("owner", ""),
                "reason": blocker.get("reason", ""),
                "observed_evidence": blocker.get("observed_evidence", {}),
                "owner_command": guidance.get("owner_command") or blocker.get("next_action", ""),
                "proof_required": blocker.get("proof_required", ""),
                "verification_commands": guidance.get("verification_commands", []),
                "external_authority_required": bool(guidance.get("external_authority_required")),
            }
        )
    actions.sort(key=lambda row: (int(row["priority"]), row["task_id"]))
    return {
        "schema_version": "owner_action_packet.v1",
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "readiness_receipt": str(readiness_path) if readiness_path else readiness.get("receipt_path", ""),
        "readiness_status": readiness.get("status", "UNKNOWN"),
        "blocking_task_count": len(actions),
        "actions": actions,
        "production_routing_enabled": False,
        "external_actions_executed": False,
        "safety_note": "Action packet only. It does not approve, enable, submit, upload, pay, use DSC, contact anyone, authenticate, or expand external authority.",
    }


def render_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Tender Export OS Owner Action Packet",
        "",
        f"- Generated at: `{packet['generated_at']}`",
        f"- Readiness status: `{packet['readiness_status']}`",
        f"- Blocking tasks: `{packet['blocking_task_count']}`",
        f"- Production routing enabled: `{packet['production_routing_enabled']}`",
        "",
        packet["safety_note"],
        "",
    ]
    for action in packet["actions"]:
        lines.extend(
            [
                f"## {action['priority']}. {action['task_id']} — {action['action_type']}",
                "",
                f"- Owner: {action['owner']}",
                f"- Reason: {action['reason']}",
                f"- Required owner action: {action['owner_command']}",
                f"- Proof required: {action['proof_required']}",
                f"- External authority required: `{action['external_authority_required']}`",
                "",
                "Verification commands:",
                "",
            ]
        )
        for command in action["verification_commands"]:
            lines.append(f"```bash\n{command}\n```")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_packet(packet: dict[str, Any], output_dir: Path = OUTPUT_DIR) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"owner_action_packet_{stamp}.json"
    md_path = output_dir / f"owner_action_packet_{stamp}.md"
    json_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(packet), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", default="")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.readiness:
        readiness_path = Path(args.readiness).expanduser()
        readiness = load_json(readiness_path)
    else:
        readiness_path, readiness = latest_readiness_receipt()
    if not readiness:
        raise SystemExit("No production-readiness receipt found. Run scripts/generate_final_readiness_receipt.py first.")
    packet = build_packet(readiness, readiness_path=readiness_path)
    paths = write_packet(packet, Path(args.output_dir).expanduser())
    payload = {
        "status": "PASS",
        "blocking_task_count": packet["blocking_task_count"],
        "json": paths["json"],
        "markdown": paths["markdown"],
        "external_actions_executed": False,
        "production_routing_enabled": False,
    }
    print(json.dumps(payload, indent=2) if args.json else f"Owner action packet: {paths['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
