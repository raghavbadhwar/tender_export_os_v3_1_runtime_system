from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from scripts import codex_export_quote_pack_contract as contract
from scripts import codex_task_runner as runner
from scripts import generate_approval_cards as approval_cards
from scripts.export_commercial_readiness import prepare_report
from scripts.hermes_create_codex_task import build_export_quote_pack_task


CASE_ID = "EXP-20990101-001"


def commercial_readiness_report() -> dict:
    return prepare_report(
        {
            "case_id": CASE_ID,
            "workflow_type": "EXPORT",
            "pricing_status": "DRAFT_READY",
            "supplier_quote_proofs": [
                {
                    "quote_id": "Q-S1",
                    "case_id": CASE_ID,
                    "supplier_id": "S1",
                    "quote_received_at": "2099-01-02T00:00:00+00:00",
                    "quote_proof_type": "quotation_pdf",
                    "quote_proof_path": "receipts/s1.pdf",
                    "quote_proof_sha256": "a" * 64,
                    "quote_verification_status": "VERIFIED",
                    "case_spec_match": "TRUE",
                    "supplier_name": "Supplier S1",
                    "product_description": "Verified export product",
                    "quantity": "100",
                    "unit_price_usd": "1.5",
                    "currency": "USD",
                    "price_basis": "FOB",
                    "lead_time_days": "14",
                    "delivery_terms": "FOB origin port",
                    "payment_terms_offered": "30% advance",
                    "validity_days": "30",
                    "supplier_specific_quote": "TRUE",
                },
                {
                    "quote_id": "Q-S2",
                    "case_id": CASE_ID,
                    "supplier_id": "S2",
                    "quote_received_at": "2099-01-02T00:00:00+00:00",
                    "quote_proof_type": "quotation_pdf",
                    "quote_proof_path": "receipts/s2.pdf",
                    "quote_proof_sha256": "b" * 64,
                    "quote_verification_status": "VERIFIED",
                    "case_spec_match": "TRUE",
                    "supplier_name": "Supplier S2",
                    "product_description": "Verified export product",
                    "quantity": "100",
                    "unit_price_usd": "1.5",
                    "currency": "USD",
                    "price_basis": "FOB",
                    "lead_time_days": "14",
                    "delivery_terms": "FOB origin port",
                    "payment_terms_offered": "30% advance",
                    "validity_days": "30",
                    "supplier_specific_quote": "TRUE",
                },
            ],
            "cost_inputs_usd": {
                "supplier_base": 100,
                "packaging": 5,
                "inland_freight": 5,
                "cha_customs_docs": 5,
                "port_handling": 5,
                "international_freight": 10,
                "insurance": 2,
                "bank_charges_pct": 1,
                "inspection_certification": 1,
                "sample_cost": 1,
                "currency_buffer_pct": 3,
                "payment_risk_pct": 2,
                "margin_pct": 15,
            },
            "cost_assumptions": {
                "packaging": "EXPORT-PACKAGING-2026Q3",
                "inland_freight": "EXPORT-INLAND-FREIGHT-2026Q3",
                "cha_customs_docs": "EXPORT-CHA-DOCS-2026Q3",
                "port_handling": "EXPORT-PORT-HANDLING-2026Q3",
                "international_freight": "EXPORT-INTERNATIONAL-FREIGHT-2026Q3",
                "insurance": "EXPORT-INSURANCE-2026Q3",
                "bank_charges_pct": "EXPORT-BANK-CHARGES-2026Q3",
                "inspection_certification": "EXPORT-INSPECTION-CERT-2026Q3",
                "sample_cost": "EXPORT-SAMPLE-COST-2026Q3",
                "currency_buffer_pct": "EXPORT-CURRENCY-BUFFER-2026Q3",
                "payment_risk_pct": "EXPORT-PAYMENT-RISK-2026Q3",
                "margin_pct": "EXPORT-MARGIN-2026Q3",
            },
            "quote_validity_days": 30,
            "payment_risk_note": "Internal draft pending buyer payment-term confirmation.",
            "candidate_hsn_itchs": {"value": "6913", "status": "DRAFT"},
            "scomet_review": {"status": "CLEAR_DRAFT"},
            "origin_questions": ["Confirm supplier origin evidence before any claim."],
            "destination_requirements": ["Confirm destination labeling requirements."],
            "incoterm_rationale": "EXW, FOB, and CIF are internal comparisons until the buyer confirms requirements.",
            "unresolved_items": [],
            "external_actions_executed": False,
        }
    )


def build_complete_pack(project_root: Path) -> tuple[Path, Path]:
    pack_root = project_root / "outputs" / "export_quote_packs" / CASE_ID
    packet_path = project_root / "runtime" / "codex_inbox" / f"{CASE_ID}_export_quote_pack.json"
    receipt_path = project_root / "receipts" / "plugin_runs" / f"{CASE_ID}_export_quote_pack.json"
    readiness_path = project_root / "outputs" / "case_reports" / CASE_ID / f"export_commercial_readiness_{CASE_ID}.json"
    pack_root.mkdir(parents=True)
    packet_path.parent.mkdir(parents=True)
    receipt_path.parent.mkdir(parents=True)
    readiness_path.parent.mkdir(parents=True)
    packet_path.write_text(json.dumps(build_export_quote_pack_task(CASE_ID, ["outputs/case_reports/pricing.json"])), encoding="utf-8")
    receipt_path.write_text(
        json.dumps(
            {
                "case_id": CASE_ID,
                "task_id": f"{CASE_ID}:quote_pack",
                "runtime": "codex_app_server",
                "status": "SUCCESS",
                "artifacts": ["outputs/export_quote_packs/example.md"],
                "external_actions_executed": False,
            }
        ),
        encoding="utf-8",
    )
    readiness_path.write_text(json.dumps(commercial_readiness_report()), encoding="utf-8")
    artifacts = []
    for kind in contract.load_contract()["required_artifact_kinds"]:
        path = "missing_items.md" if kind == "missing_items_list" else f"{kind}.md"
        (pack_root / path).write_text(
            f"# {kind}\n\nInternal draft for {CASE_ID}; no external commitments.\n",
            encoding="utf-8",
        )
        artifacts.append({"kind": kind, "path": path})
    manifest_path = pack_root / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "export_quote_pack_manifest.v1",
                "case_id": CASE_ID,
                "workflow_type": "EXPORT",
                "generated_at": "2099-01-01T00:00:00+00:00",
                "codex_task_packet_path": str(packet_path.relative_to(project_root)),
                "commercial_readiness_path": str(readiness_path.relative_to(project_root)),
                "artifacts": artifacts,
                "missing_items_path": "missing_items.md",
                "plugin_receipt_path": str(receipt_path.relative_to(project_root)),
                "unapproved_claims_disclaimer": "Internal draft only; no final commercial or compliance claim is approved.",
                "final_claims_approved": False,
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


def test_export_quote_pack_requires_current_persisted_verification_before_quote_approval(monkeypatch, tmp_path: Path) -> None:
    configure_project_root(monkeypatch, tmp_path)
    pack_root, manifest_path = build_complete_pack(tmp_path)

    report = contract.verify_export_quote_pack(manifest_path, expected_case_id=CASE_ID)

    assert report["status"] == "PASS"
    assert all(check["open_verified"] and check["render_verified"] and check["parse_verified"] for check in report["artifact_checks"])
    assert report["plugin_receipt_check"]["valid"] is True
    contract.write_verification_receipt(
        report,
        output_path=pack_root / "verification_receipt.json",
        events_path=tmp_path / "data" / "events.jsonl",
    )

    approval_report = contract.verify_export_quote_pack_approval_ready(
        manifest_path,
        pack_root / "verification_receipt.json",
        expected_case_id=CASE_ID,
    )
    assert approval_report["status"] == "PASS"
    ready, errors = approval_cards.export_quote_pack_ready(
        {"case_id": CASE_ID, "workflow_type": "EXPORT", "proposed_action": "send_export_quotation"},
        {},
    )
    assert ready is True
    assert errors == []


def test_export_quote_receipt_becomes_stale_when_a_pack_artifact_changes(monkeypatch, tmp_path: Path) -> None:
    configure_project_root(monkeypatch, tmp_path)
    pack_root, manifest_path = build_complete_pack(tmp_path)
    report = contract.verify_export_quote_pack(manifest_path, expected_case_id=CASE_ID)
    contract.write_verification_receipt(
        report,
        output_path=pack_root / "verification_receipt.json",
        events_path=tmp_path / "data" / "events.jsonl",
    )

    (pack_root / "pricing_waterfall.md").write_text("# changed\n\nA revised internal scenario exists.\n", encoding="utf-8")
    stale_report = contract.verify_export_quote_pack_approval_ready(
        manifest_path,
        pack_root / "verification_receipt.json",
        expected_case_id=CASE_ID,
    )

    assert stale_report["status"] == "FAIL"
    assert any("stale" in error for error in stale_report["errors"])


def test_runner_writes_only_internal_export_verification_receipt(monkeypatch, tmp_path: Path) -> None:
    configure_project_root(monkeypatch, tmp_path)
    pack_root, _ = build_complete_pack(tmp_path)

    result = runner.verify_export_quote_pack(
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


def test_export_quote_packet_is_explicitly_internal_only() -> None:
    packet = build_export_quote_pack_task(CASE_ID, ["outputs/case_reports/example.json"])

    assert packet["task_type"] == "EXPORT_QUOTE_PACK"
    assert packet["workflow_type"] == "EXPORT"
    assert packet["external_actions_executed"] is False
    assert packet["final_claims_approved"] is False
    assert "approval card" in packet["approval_boundary"].lower()
