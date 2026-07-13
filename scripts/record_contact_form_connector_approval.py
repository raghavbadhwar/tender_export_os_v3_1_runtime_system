#!/usr/bin/env python3
"""Record owner approval for the contact-form connector design without enabling execution."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validate_contact_form_connector_design import load_design, validate_design  # noqa: E402


DEFAULT_DESIGN = PROJECT_ROOT / "config" / "contact_form_connector_design.yaml"
DEFAULT_LANE = PROJECT_ROOT / "config" / "contact_form_lane.yaml"
DEFAULT_RECEIPT_DIR = PROJECT_ROOT / "receipts" / "contact_form_connector_approvals"


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def update_lane_approval(lane: dict[str, Any], *, approval_id: str, design_doc: str, approved_at: str) -> dict[str, Any]:
    updated = dict(lane)
    approved = dict(updated.get("approved_connector_design") or {})
    approved.update(
        {
            "approval_id": approval_id,
            "design_doc": design_doc,
            "approved_at": approved_at,
        }
    )
    updated["approved_connector_design"] = approved
    updated["status"] = "APPROVED_DESIGN_EXECUTION_DISABLED"
    updated["production_enabled"] = False
    return updated


def record_approval(
    *,
    approved_by: str,
    note: str = "",
    design_path: Path = DEFAULT_DESIGN,
    lane_path: Path = DEFAULT_LANE,
    receipt_dir: Path = DEFAULT_RECEIPT_DIR,
    apply: bool = False,
) -> dict[str, Any]:
    design = load_design(design_path)
    validation = validate_design(design)
    if validation["status"] != "PASS":
        return {
            "status": "BLOCKED",
            "applied": False,
            "errors": validation["errors"],
            "message": "Contact-form connector design cannot be approved until validation passes.",
        }
    lane = load_yaml(lane_path)
    approved_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    approval_id = f"CFCD-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    receipt = {
        "schema_version": "contact_form_connector_design_approval.v1",
        "approval_id": approval_id,
        "approved": True,
        "approved_by": approved_by,
        "approved_at": approved_at,
        "note": note,
        "design_doc": str(design_path.relative_to(PROJECT_ROOT) if design_path.is_relative_to(PROJECT_ROOT) else design_path),
        "design_sha256": sha256_file(design_path),
        "lane_doc": str(lane_path.relative_to(PROJECT_ROOT) if lane_path.is_relative_to(PROJECT_ROOT) else lane_path),
        "production_enabled": False,
        "external_actions_authorized": False,
        "form_submission_authorized": False,
        "safety_note": "Approves connector design controls only. It does not authorize a specific contact form submission, browser action, message send, quote, bid, upload, payment, DSC, or external commitment.",
    }
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / f"{approval_id}.json"
    if apply:
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        updated_lane = update_lane_approval(
            lane,
            approval_id=approval_id,
            design_doc=receipt["design_doc"],
            approved_at=approved_at,
        )
        write_yaml(lane_path, updated_lane)
    return {
        "status": "APPROVED" if apply else "DRY_RUN",
        "applied": apply,
        "approval_id": approval_id,
        "receipt_path": str(receipt_path),
        "lane_path": str(lane_path),
        "production_enabled": False,
        "external_actions_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-by", required=True)
    parser.add_argument("--note", default="")
    parser.add_argument("--design", default=str(DEFAULT_DESIGN))
    parser.add_argument("--lane", default=str(DEFAULT_LANE))
    parser.add_argument("--receipt-dir", default=str(DEFAULT_RECEIPT_DIR))
    parser.add_argument("--apply", action="store_true", help="Write the approval receipt and update the disabled lane metadata.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = record_approval(
        approved_by=args.approved_by,
        note=args.note,
        design_path=Path(args.design).expanduser(),
        lane_path=Path(args.lane).expanduser(),
        receipt_dir=Path(args.receipt_dir).expanduser(),
        apply=args.apply,
    )
    print(json.dumps(result, indent=2) if args.json else result["status"])
    return 0 if result["status"] in {"APPROVED", "DRY_RUN", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
