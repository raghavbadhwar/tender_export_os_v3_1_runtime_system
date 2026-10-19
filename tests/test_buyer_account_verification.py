from __future__ import annotations

import hashlib
from pathlib import Path

from scripts import buyer_account_verification as verifier


def account_record(evidence: Path) -> dict:
    return {
        "case_id": "EXP-1",
        "buyer_id": "BUY-1",
        "legal_entity_name": "Example Retail Ltd",
        "country": "United Kingdom",
        "official_domain": "https://example.com",
        "product_category_fit": "CATALOGUE_HYPOTHESIS",
        "procurement_contact_path": "https://example.com/contact",
        "source_observed_at": "2099-01-01",
        "public_evidence_path": str(evidence),
        "public_evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
        "duplicate_check": {"status": "CLEAR"},
        "sanctions_review": {"status": "CLEAR_PUBLIC_SCREEN"},
        "confidence_score": 72,
        "proof_gaps": ["Buyer-specific RFQ has not been received."],
        "external_actions_executed": False,
    }


def test_catalogue_fit_remains_contact_path_not_rfq_verified(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(verifier, "PROJECT_ROOT", tmp_path)
    evidence = tmp_path / "public.html"
    evidence.write_text("Public retailer catalogue proof", encoding="utf-8")

    report = verifier.validate_account(account_record(evidence))

    assert report["status"] == "PASS"
    assert report["account_status"] == "CONTACT_PATH_VERIFIED"


def test_rfq_stage_requires_buyer_specific_proof_and_rfq_matched_category(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(verifier, "PROJECT_ROOT", tmp_path)
    evidence = tmp_path / "public.html"
    rfq = tmp_path / "rfq.pdf"
    evidence.write_text("Public company proof", encoding="utf-8")
    rfq.write_text("Buyer specific RFQ", encoding="utf-8")
    record = account_record(evidence)
    record["product_category_fit"] = "RFQ_MATCHED"
    record["buyer_specific_demand_evidence"] = {
        "type": "RFQ",
        "path": str(rfq),
        "sha256": hashlib.sha256(rfq.read_bytes()).hexdigest(),
    }
    record["proof_gaps"] = []

    report = verifier.validate_account(record)

    assert report["account_status"] == "RFQ_VERIFIED"


def test_ambiguous_sanctions_or_identity_proof_blocks_promotion(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(verifier, "PROJECT_ROOT", tmp_path)
    evidence = tmp_path / "public.html"
    evidence.write_text("Public company proof", encoding="utf-8")
    record = account_record(evidence)
    record["sanctions_review"] = {"status": "HIT_OR_AMBIGUOUS"}

    report = verifier.validate_account(record)

    assert report["status"] == "FAIL"
    assert report["account_status"] == "BLOCKED"
