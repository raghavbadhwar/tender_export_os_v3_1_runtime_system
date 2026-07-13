from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from scripts import codex_bid_pack_contract as contract
from scripts import codex_task_runner as runner
from scripts import generate_approval_cards as approval_cards
from scripts.hermes_create_codex_task import build_gov_bid_pack_task


CASE_ID = "GOV-20990101-001"


def build_complete_pack(project_root: Path) -> tuple[Path, Path]:
    pack_root = project_root / "outputs" / "bid_packs" / CASE_ID
    packet_path = project_root / "runtime" / "codex_inbox" / f"{CASE_ID}_bid_pack.json"
    plugin_receipt_path = project_root / "receipts" / "plugin_runs" / f"{CASE_ID}_bid_pack.json"
    pack_root.mkdir(parents=True)
    packet_path.parent.mkdir(parents=True)
    plugin_receipt_path.parent.mkdir(parents=True)
    packet_path.write_text(json.dumps(build_gov_bid_pack_task(CASE_ID, ["outputs/case_reports/pricing.json"])), encoding="utf-8")
    plugin_receipt_path.write_text(
        json.dumps(
            {
                "case_id": CASE_ID,
                "task_id": f"{CASE_ID}:artifacts",
                "runtime": "codex_app_server",
                "status": "SUCCESS",
                "artifacts": ["outputs/bid_packs/example.md"],
                "external_actions_executed": False,
            }
        ),
        encoding="utf-8",
    )
    artifacts = []
    for kind in contract.load_contract()["required_artifact_kinds"]:
        path = "missing_items.md" if kind == "missing_items_list" else f"{kind}.md"
        (pack_root / path).write_text(f"# {kind}\n\nInternal draft for {CASE_ID}.\n", encoding="utf-8")
        artifacts.append({"kind": kind, "path": path})
    manifest_path = pack_root / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "bid_pack_manifest.v1",
                "case_id": CASE_ID,
                "workflow_type": "GOV",
                "generated_at": "2099-01-01T00:00:00+00:00",
                "codex_task_packet_path": str(packet_path.relative_to(project_root)),
                "artifacts": artifacts,
                "missing_items_path": "missing_items.md",
                "plugin_receipt_path": str(plugin_receipt_path.relative_to(project_root)),
                "external_actions_executed": False,
            }
        ),
        encoding="utf-8",
    )
    return pack_root, manifest_path


def configure_project_root(monkeypatch, project_root: Path) -> None:
    monkeypatch.setattr(contract, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(runner, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(runner, "INBOX", project_root / "runtime" / "codex_inbox")
    monkeypatch.setattr(approval_cards, "PROJECT_ROOT", project_root)


def test_gov_bid_pack_requires_current_persisted_verification_before_approval(monkeypatch, tmp_path: Path) -> None:
    configure_project_root(monkeypatch, tmp_path)
    pack_root, manifest_path = build_complete_pack(tmp_path)

    report = contract.verify_bid_pack(manifest_path, expected_case_id=CASE_ID)

    assert report["status"] == "PASS"
    assert all(check["open_verified"] and check["render_verified"] and check["parse_verified"] for check in report["artifact_checks"])
    assert report["plugin_receipt_check"]["valid"] is True
    event_file = tmp_path / "data" / "events.jsonl"
    contract.write_verification_receipt(report, output_path=pack_root / "verification_receipt.json", events_path=event_file)

    approval_report = contract.verify_bid_pack_approval_ready(
        manifest_path,
        pack_root / "verification_receipt.json",
        expected_case_id=CASE_ID,
    )
    assert approval_report["status"] == "PASS"
    assert approval_report["verification_receipt_check"]["valid"] is True
    assert event_file.is_file()

    ready, errors = approval_cards.gov_bid_pack_ready({"case_id": CASE_ID, "workflow_type": "GOV"}, {})
    assert ready is True
    assert errors == []


def test_verification_receipt_becomes_stale_when_a_pack_artifact_changes(monkeypatch, tmp_path: Path) -> None:
    configure_project_root(monkeypatch, tmp_path)
    pack_root, manifest_path = build_complete_pack(tmp_path)
    report = contract.verify_bid_pack(manifest_path, expected_case_id=CASE_ID)
    contract.write_verification_receipt(
        report,
        output_path=pack_root / "verification_receipt.json",
        events_path=tmp_path / "data" / "events.jsonl",
    )

    (pack_root / "risk_register.md").write_text("# changed\n\nA new internal risk was found.\n", encoding="utf-8")
    stale_report = contract.verify_bid_pack_approval_ready(
        manifest_path,
        pack_root / "verification_receipt.json",
        expected_case_id=CASE_ID,
    )

    assert stale_report["status"] == "FAIL"
    assert any("stale" in error for error in stale_report["errors"])


def test_runner_writes_only_internal_verification_receipt(monkeypatch, tmp_path: Path) -> None:
    configure_project_root(monkeypatch, tmp_path)
    pack_root, _ = build_complete_pack(tmp_path)
    result = runner.verify_gov_bid_pack(
        Namespace(
            case_id=CASE_ID,
            pack_dir="",
            manifest="",
            receipt="",
            events="data/events.jsonl",
            write_receipt=True,
            json=True,
        )
    )

    assert result == 0
    receipt = json.loads((pack_root / "verification_receipt.json").read_text(encoding="utf-8"))
    assert receipt["status"] == "PASS"
    assert receipt["external_actions_executed"] is False


def test_gov_bid_pack_packet_is_explicitly_internal_only() -> None:
    packet = build_gov_bid_pack_task(CASE_ID, ["outputs/case_reports/example.json"])

    assert packet["task_type"] == "GOV_BID_PACK"
    assert packet["workflow_type"] == "GOV"
    assert packet["external_actions_executed"] is False
    assert "approval card" in packet["approval_boundary"].lower()
    assert "verification_receipt.json" in packet["required_outputs"][-2]
