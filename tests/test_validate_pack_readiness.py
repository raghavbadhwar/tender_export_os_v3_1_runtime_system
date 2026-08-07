from __future__ import annotations

import json
from pathlib import Path

from scripts import codex_bid_pack_contract
from scripts import codex_export_quote_pack_contract
from scripts import validate_pack_readiness
from scripts.export_commercial_readiness import prepare_report
from scripts.hermes_create_codex_task import build_export_quote_pack_task, build_gov_bid_pack_task


GOV_CASE_ID = "GOV-20990101-001"
EXPORT_CASE_ID = "EXP-20990101-001"


def configure_project_root(monkeypatch, project_root: Path) -> None:
    monkeypatch.setattr(codex_bid_pack_contract, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(codex_export_quote_pack_contract, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(validate_pack_readiness, "PROJECT_ROOT", project_root)


def quote(case_id: str, supplier_id: str, digest_char: str) -> dict:
    return {
        "quote_id": f"Q-{supplier_id}",
        "case_id": case_id,
        "supplier_id": supplier_id,
        "quote_received_at": "2099-01-02T00:00:00+00:00",
        "quote_proof_type": "quotation_pdf",
        "quote_proof_path": f"receipts/{supplier_id}.pdf",
        "quote_proof_sha256": digest_char * 64,
        "quote_verification_status": "VERIFIED",
        "case_spec_match": "TRUE",
        "supplier_name": f"Supplier {supplier_id}",
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
    }


def export_commercial_readiness_report() -> dict:
    return prepare_report(
        {
            "case_id": EXPORT_CASE_ID,
            "workflow_type": "EXPORT",
            "pricing_status": "DRAFT_READY",
            "supplier_quote_proofs": [quote(EXPORT_CASE_ID, "S1", "a"), quote(EXPORT_CASE_ID, "S2", "b")],
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


def build_gov_pack(project_root: Path) -> tuple[Path, Path]:
    pack_root = project_root / "outputs" / "bid_packs" / GOV_CASE_ID
    packet_path = project_root / "runtime" / "codex_inbox" / f"{GOV_CASE_ID}_bid_pack.json"
    plugin_receipt_path = project_root / "receipts" / "plugin_runs" / f"{GOV_CASE_ID}_bid_pack.json"
    pack_root.mkdir(parents=True)
    packet_path.parent.mkdir(parents=True)
    plugin_receipt_path.parent.mkdir(parents=True)
    packet_path.write_text(json.dumps(build_gov_bid_pack_task(GOV_CASE_ID, ["outputs/case_reports/pricing.json"])), encoding="utf-8")
    plugin_receipt_path.write_text(
        json.dumps({"case_id": GOV_CASE_ID, "task_id": f"{GOV_CASE_ID}:artifacts", "runtime": "codex_app_server", "status": "SUCCESS", "artifacts": ["outputs/bid_packs/example.md"], "external_actions_executed": False}),
        encoding="utf-8",
    )
    artifacts = []
    for kind in codex_bid_pack_contract.load_contract()["required_artifact_kinds"]:
        path = "missing_items.md" if kind == "missing_items_list" else f"{kind}.md"
        (pack_root / path).write_text(f"# {kind}\n\nInternal draft for {GOV_CASE_ID}.\n", encoding="utf-8")
        artifacts.append({"kind": kind, "path": path})
    manifest_path = pack_root / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps({"schema_version": "bid_pack_manifest.v1", "case_id": GOV_CASE_ID, "workflow_type": "GOV", "generated_at": "2099-01-01T00:00:00+00:00", "codex_task_packet_path": str(packet_path.relative_to(project_root)), "artifacts": artifacts, "missing_items_path": "missing_items.md", "plugin_receipt_path": str(plugin_receipt_path.relative_to(project_root)), "external_actions_executed": False}),
        encoding="utf-8",
    )
    return pack_root, manifest_path


def build_export_pack(project_root: Path) -> tuple[Path, Path]:
    pack_root = project_root / "outputs" / "export_quote_packs" / EXPORT_CASE_ID
    packet_path = project_root / "runtime" / "codex_inbox" / f"{EXPORT_CASE_ID}_export_quote_pack.json"
    receipt_path = project_root / "receipts" / "plugin_runs" / f"{EXPORT_CASE_ID}_export_quote_pack.json"
    readiness_path = project_root / "outputs" / "case_reports" / EXPORT_CASE_ID / f"export_commercial_readiness_{EXPORT_CASE_ID}.json"
    pack_root.mkdir(parents=True)
    packet_path.parent.mkdir(parents=True)
    receipt_path.parent.mkdir(parents=True)
    readiness_path.parent.mkdir(parents=True)
    packet_path.write_text(json.dumps(build_export_quote_pack_task(EXPORT_CASE_ID, ["outputs/case_reports/pricing.json"])), encoding="utf-8")
    receipt_path.write_text(
        json.dumps({"case_id": EXPORT_CASE_ID, "task_id": f"{EXPORT_CASE_ID}:quote_pack", "runtime": "codex_app_server", "status": "SUCCESS", "artifacts": ["outputs/export_quote_packs/example.md"], "external_actions_executed": False}),
        encoding="utf-8",
    )
    readiness_path.write_text(json.dumps(export_commercial_readiness_report()), encoding="utf-8")
    artifacts = []
    for kind in codex_export_quote_pack_contract.load_contract()["required_artifact_kinds"]:
        path = "missing_items.md" if kind == "missing_items_list" else f"{kind}.md"
        (pack_root / path).write_text(f"# {kind}\n\nInternal draft for {EXPORT_CASE_ID}; no external commitments.\n", encoding="utf-8")
        artifacts.append({"kind": kind, "path": path})
    manifest_path = pack_root / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps({"schema_version": "export_quote_pack_manifest.v1", "case_id": EXPORT_CASE_ID, "workflow_type": "EXPORT", "generated_at": "2099-01-01T00:00:00+00:00", "codex_task_packet_path": str(packet_path.relative_to(project_root)), "commercial_readiness_path": str(readiness_path.relative_to(project_root)), "artifacts": artifacts, "missing_items_path": "missing_items.md", "plugin_receipt_path": str(receipt_path.relative_to(project_root)), "unapproved_claims_disclaimer": "Internal draft only; no final commercial or compliance claim is approved.", "final_claims_approved": False, "external_actions_executed": False}),
        encoding="utf-8",
    )
    return pack_root, manifest_path


def enrich_manifest(path: Path, *, case_id: str, workflow_type: str) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "approval_scope": {
                "proposed_action": "submit_tender_bid" if workflow_type == "GOV" else "send_export_quotation",
                "approval_boundary": "owner_decision_required_before_external_action",
                "scope_hash": "a" * 64,
                "final_claims_approved": False,
                "external_actions_executed": False,
            },
            "source_citations": [
                {
                    "source_path": f"outputs/case_reports/{case_id}/source_evidence.json",
                    "source_date": "2099-01-01",
                }
            ],
            "quote_proof_receipts": [
                {
                    "quote_id": "Q1",
                    "supplier_id": "S1",
                    "quote_proof_path": "receipts/q1.pdf",
                    "quote_proof_sha256": "a" * 64,
                },
                {
                    "quote_id": "Q2",
                    "supplier_id": "S2",
                    "quote_proof_path": "receipts/q2.pdf",
                    "quote_proof_sha256": "b" * 64,
                },
            ],
            "unresolved_unknowns": [],
        }
    )
    path.write_text(json.dumps(manifest), encoding="utf-8")


def test_validate_gov_pack_readiness_requires_approval_scope_and_evidence(monkeypatch, tmp_path: Path) -> None:
    configure_project_root(monkeypatch, tmp_path)
    _, manifest_path = build_gov_pack(tmp_path)

    missing = validate_pack_readiness.validate_pack(manifest_path, workflow_type="GOV", expected_case_id=GOV_CASE_ID)
    assert missing["status"] == "FAIL"
    assert "approval_scope is required" in missing["errors"]

    enrich_manifest(manifest_path, case_id=GOV_CASE_ID, workflow_type="GOV")
    ready = validate_pack_readiness.validate_pack(manifest_path, workflow_type="GOV", expected_case_id=GOV_CASE_ID)
    assert ready["status"] == "PASS"
    assert ready["external_actions_executed"] is False


def test_validate_export_pack_readiness_rejects_unresolved_unknowns(monkeypatch, tmp_path: Path) -> None:
    configure_project_root(monkeypatch, tmp_path)
    _, manifest_path = build_export_pack(tmp_path)
    enrich_manifest(manifest_path, case_id=EXPORT_CASE_ID, workflow_type="EXPORT")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["unresolved_unknowns"] = ["origin evidence missing"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_pack_readiness.validate_pack(manifest_path, workflow_type="EXPORT", expected_case_id=EXPORT_CASE_ID)

    assert report["status"] == "FAIL"
    assert "unresolved_unknowns must be empty before approval-ready pack routing" in report["errors"]


def test_write_pack_readiness_creates_internal_event(monkeypatch, tmp_path: Path) -> None:
    configure_project_root(monkeypatch, tmp_path)
    _, manifest_path = build_gov_pack(tmp_path)
    enrich_manifest(manifest_path, case_id=GOV_CASE_ID, workflow_type="GOV")
    report = validate_pack_readiness.validate_pack(manifest_path, workflow_type="GOV", expected_case_id=GOV_CASE_ID)

    result = validate_pack_readiness.write_report(report, output_dir=tmp_path / "readiness", events_path=tmp_path / "events.jsonl")

    assert Path(result["json_path"]).is_file()
    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8").strip())
    assert event["event_type"] == "artifact.pack_readiness_validated"
    assert event["payload"]["status"] == "PASS"
