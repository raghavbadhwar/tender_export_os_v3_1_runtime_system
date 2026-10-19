from __future__ import annotations

from scripts.export_commercial_readiness import prepare_report, validate_contract


def quote(case_id: str, supplier_id: str) -> dict:
    return {
        "quote_id": f"Q-{supplier_id}",
        "case_id": case_id,
        "supplier_id": supplier_id,
        "quote_received_at": "2099-01-02T00:00:00+00:00",
        "quote_proof_type": "quotation_pdf",
        "quote_proof_path": f"receipts/{supplier_id}.pdf",
        "quote_proof_sha256": "a" * 64,
        "quote_verification_status": "VERIFIED",
        "case_spec_match": "TRUE",
        "supplier_name": f"Supplier {supplier_id}",
        "product_description": "Verified export product",
        "quantity": "100",
        "unit": "piece",
        "unit_price_usd": "1.5",
        "currency": "USD",
        "price_basis": "FOB",
        "lead_time_days": "14",
        "delivery_terms": "FOB origin port",
        "payment_terms_offered": "30% advance",
        "validity_days": "30",
        "supplier_specific_quote": "TRUE",
    }


def report() -> dict:
    return {
        "case_id": "EXP-1",
        "workflow_type": "EXPORT",
        "pricing_status": "DRAFT_READY",
        "supplier_quote_proofs": [quote("EXP-1", "S1"), quote("EXP-1", "S2")],
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
        "payment_risk_note": "Draft assumption pending buyer payment-term confirmation.",
        "candidate_hsn_itchs": {"value": "6913", "status": "DRAFT"},
        "scomet_review": {"status": "CLEAR_DRAFT"},
        "origin_questions": ["Confirm supplier origin evidence before any claim."],
        "destination_requirements": ["Confirm destination labeling requirements."],
        "incoterm_rationale": "EXW/FOB/CIF scenarios are internal comparators until buyer requirements are verified.",
        "unresolved_items": [],
        "external_actions_executed": False,
    }


def test_export_commercial_readiness_requires_all_costs_and_two_quote_proofs() -> None:
    value = prepare_report(report())

    assert validate_contract(value) == []
    assert set(value["draft_scenarios_usd"]) == {"EXW", "FOB", "CIF"}

    missing = report()
    missing["supplier_quote_proofs"] = [quote("EXP-1", "S1")]
    missing["cost_inputs_usd"].pop("insurance")
    errors = validate_contract(prepare_report(missing))
    assert any("two distinct" in error for error in errors)
    assert any("insurance" in error for error in errors)


def test_scomet_signal_blocks_export_quote_readiness() -> None:
    value = report()
    value["scomet_review"] = {"status": "SUSPECTED"}

    errors = validate_contract(prepare_report(value))

    assert any("SCOMET" in error for error in errors)

    value["pricing_status"] = "BLOCKED"
    value["unresolved_items"] = ["SCOMET specialist review required."]
    blocked = prepare_report(value)
    assert validate_contract(blocked) == []


def test_export_cost_assumptions_are_required_for_draft_ready() -> None:
    value = report()
    value["cost_assumptions"].pop("insurance")

    errors = validate_contract(prepare_report(value))

    assert any("cost_assumptions.insurance is required" in error for error in errors)


def test_export_zero_cost_needs_zero_value_assumption() -> None:
    value = report()
    value["cost_inputs_usd"]["insurance"] = 0

    errors = validate_contract(prepare_report(value))

    assert any("cannot justify a zero cost" in error for error in errors)
