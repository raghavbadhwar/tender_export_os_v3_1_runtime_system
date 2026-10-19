from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

from scripts.record_computer_use_read_only_canary import record_canary, validate_canary_receipt


ROOT = Path(__file__).resolve().parents[1]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixture_paths(tmp_path: Path) -> dict[str, Path]:
    cases = tmp_path / "master_cases.csv"
    approvals = tmp_path / "approvals.csv"
    evidence = tmp_path / "canary-observation.txt"
    config = tmp_path / "computer-use.yaml"
    write_csv(cases, ["case_id"], [{"case_id": "GOV-CANARY-001"}])
    write_csv(
        approvals,
        ["approval_id", "case_id", "approval_status", "action_approved", "approval_timeout_at"],
        [
            {
                "approval_id": "APR-CU-001",
                "case_id": "GOV-CANARY-001",
                "approval_status": "APPROVED",
                "action_approved": "computer_use_read_only_canary",
                "approval_timeout_at": "2099-01-01T00:00:00+00:00",
            }
        ],
    )
    evidence.write_text("Owner observed a public page. No login or external action occurred.\n", encoding="utf-8")
    config.write_text((ROOT / "config" / "computer_use_portal_assist.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    return {"cases": cases, "approvals": approvals, "evidence": evidence, "config": config}


def kwargs(paths: dict[str, Path], tmp_path: Path) -> dict:
    return {
        "case_id": "GOV-CANARY-001",
        "approval_reference": "APR-CU-001",
        "observed_by": "owner",
        "observed_at": "2026-07-13T12:00:00+05:30",
        "evidence": str(paths["evidence"]),
        "cases_path": paths["cases"],
        "approvals_path": paths["approvals"],
        "receipts_dir": tmp_path / "receipts",
        "events_path": tmp_path / "events.jsonl",
        "run_log_path": tmp_path / "agent_run_log.csv",
        "config_path": paths["config"],
    }


def test_dry_run_validates_owner_scope_without_writing(tmp_path: Path) -> None:
    paths = fixture_paths(tmp_path)
    result = record_canary(**kwargs(paths, tmp_path))

    assert result["status"] == "PASS"
    assert result["mode"] == "dry_run"
    assert result["canonical_event_appended"] is False
    assert not (tmp_path / "receipts").exists()
    assert not (tmp_path / "events.jsonl").exists()


def test_write_records_safe_receipt_event_and_run_log(tmp_path: Path) -> None:
    paths = fixture_paths(tmp_path)
    result = record_canary(**kwargs(paths, tmp_path), write=True)

    receipt_path = Path(result["receipt_path"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8").strip())
    validation = validate_canary_receipt(
        receipt,
        project_root=ROOT,
        cases_path=paths["cases"],
        approvals_path=paths["approvals"],
    )

    assert result["status"] == "PASS"
    assert receipt["external_actions_executed"] is False
    assert receipt["portal_assist_enabled"] is False
    assert receipt["form_submission_attempted"] is False
    assert event["event_type"] == "computer_use.read_only_canary_recorded"
    assert event["object_type"] == "computer_use_canary"
    assert validation["status"] == "PASS"
    assert "computer_use_read_only_canary_recorded" in (tmp_path / "agent_run_log.csv").read_text(encoding="utf-8")


def test_write_refuses_non_canary_approval_scope(tmp_path: Path) -> None:
    paths = fixture_paths(tmp_path)
    payload = yaml.safe_load(paths["config"].read_text(encoding="utf-8"))
    assert payload["canary_contract"]["required_approval_action"] == "computer_use_read_only_canary"
    result = record_canary(**(kwargs(paths, tmp_path) | {"approval_reference": "MISSING"}), write=True)

    assert result["status"] == "BLOCKED"
    assert result["canonical_event_appended"] is False
    assert not (tmp_path / "events.jsonl").exists()
