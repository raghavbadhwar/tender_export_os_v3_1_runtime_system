from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

from scripts.record_contact_form_connector_approval import record_approval
from scripts.validate_contact_form_lane import validate_contact_form_lane


ROOT = Path(__file__).resolve().parents[1]


def test_contact_form_connector_approval_dry_run_does_not_mutate_lane(tmp_path: Path) -> None:
    design = tmp_path / "design.yaml"
    lane = tmp_path / "lane.yaml"
    shutil.copy(ROOT / "config" / "contact_form_connector_design.yaml", design)
    shutil.copy(ROOT / "config" / "contact_form_lane.yaml", lane)
    before = lane.read_text(encoding="utf-8")

    result = record_approval(
        approved_by="owner",
        design_path=design,
        lane_path=lane,
        receipt_dir=tmp_path / "receipts",
        apply=False,
    )

    assert result["status"] == "DRY_RUN"
    assert result["applied"] is False
    assert lane.read_text(encoding="utf-8") == before
    assert not Path(result["receipt_path"]).exists()


def test_contact_form_connector_approval_updates_disabled_lane_and_receipt(tmp_path: Path) -> None:
    design = tmp_path / "design.yaml"
    lane = tmp_path / "lane.yaml"
    shutil.copy(ROOT / "config" / "contact_form_connector_design.yaml", design)
    shutil.copy(ROOT / "config" / "contact_form_lane.yaml", lane)

    result = record_approval(
        approved_by="owner",
        note="Approve controls only.",
        design_path=design,
        lane_path=lane,
        receipt_dir=tmp_path / "receipts",
        apply=True,
    )

    lane_payload = yaml.safe_load(lane.read_text(encoding="utf-8"))
    receipt = json.loads(Path(result["receipt_path"]).read_text(encoding="utf-8"))
    validation = validate_contact_form_lane(lane_payload)

    assert result["status"] == "APPROVED"
    assert receipt["external_actions_authorized"] is False
    assert receipt["form_submission_authorized"] is False
    assert lane_payload["production_enabled"] is False
    assert lane_payload["status"] == "APPROVED_DESIGN_EXECUTION_DISABLED"
    assert lane_payload["approved_connector_design"]["approval_id"] == result["approval_id"]
    assert validation["status"] == "PASS"
    assert validation["has_approved_design"] is True
