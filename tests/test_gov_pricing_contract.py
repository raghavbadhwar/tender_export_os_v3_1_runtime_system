from __future__ import annotations

import json
from pathlib import Path

from scripts.gov_pricing_contract import load_contract, validate_report, write_pricing


ASSUMPTION_IDS = {
    "gst": "GOV-GST-2026Q3",
    "freight": "GOV-FREIGHT-2026Q3",
    "packaging": "GOV-PACKAGING-2026Q3",
    "installation": "GOV-INSTALLATION-2026Q3",
    "warranty_reserve": "GOV-WARRANTY-2026Q3",
    "documentation": "GOV-DOCUMENTATION-2026Q3",
    "portal_fee": "GOV-FEES-2026Q3",
    "document_fee": "GOV-DOCUMENT-FEE-2026Q3",
    "bid_submission_fee": "GOV-BID-SUBMISSION-FEE-2026Q3",
    "emd_opportunity_cost": "GOV-EMD-COST-2026Q3",
    "pbg_cost": "GOV-PBG-COST-2026Q3",
    "working_capital_financing": "GOV-WORKING-CAPITAL-2026Q3",
    "payment_delay_buffer": "GOV-PAYMENT-DELAY-2026Q3",
    "penalty_reserve": "GOV-PENALTY-RESERVE-2026Q3",
    "risk_buffer": "GOV-RISK-BUFFER-2026Q3",
    "margin": "GOV-MARGIN-2026Q3",
}


def component(key: str, amount: float, *, status: str = "ASSUMED") -> dict:
    value = {"key": key, "status": status, "amount_inr": amount, "source_date": "2099-01-01"}
    if status == "OBSERVED":
        value["evidence_path"] = f"receipts/{key}.pdf"
    else:
        value["assumption_id"] = ASSUMPTION_IDS[key]
    return value


def report() -> dict:
    components = [
        component(key, 100000 if key == "supplier_base_cost" else 0, status="OBSERVED" if key == "supplier_base_cost" else "ASSUMED")
        for key in load_contract()["required_component_keys"]
    ]
    return {
        "schema_version": "gov_pricing.v1",
        "case_id": "GOV-1",
        "workflow_type": "GOV",
        "generated_at": "2026-07-13T00:00:00+00:00",
        "supplier_gate_status": "PASS",
        "supplier_quote_proofs": [
            {"quote_id": "Q1", "supplier_id": "S1", "quote_proof_path": "receipts/q1.pdf", "source_date": "2099-01-01"},
            {"quote_id": "Q2", "supplier_id": "S2", "quote_proof_path": "receipts/q2.pdf", "source_date": "2099-01-01"},
        ],
        "cost_waterfall": {"currency": "INR", "components": components},
        "working_capital": {
            "supplier_payment_day": 0,
            "buyer_payment_day": 45,
            "gap_days": 45,
            "cash_gap_inr": 100000,
            "annual_financing_rate_pct": 18,
            "source_date": "2099-01-01",
        },
        "l1_sensitivity": [
            {"scenario": "base", "bid_price_inr": 120000, "gross_margin_inr": 20000, "gross_margin_pct": 16.67, "decision_warning": "acceptable"},
            {"scenario": "competitor -5%", "bid_price_inr": 114000, "gross_margin_inr": 14000, "gross_margin_pct": 12.28, "decision_warning": "review"},
            {"scenario": "competitor -20%", "bid_price_inr": 96000, "gross_margin_inr": -4000, "gross_margin_pct": -4.17, "decision_warning": "loss_or_too_thin"},
        ],
        "margin_scenarios": [
            {"name": "conservative", "margin_pct": 10, "bid_price_inr": 110000},
            {"name": "recommended", "margin_pct": 15, "bid_price_inr": 115000},
            {"name": "aggressive", "margin_pct": 20, "bid_price_inr": 120000},
        ],
        "assumptions": [{"assumption_id": "ASM-freight", "basis": "Internal dated freight assumption"}],
        "source_dates": [{"source_name": "Supplier quote", "source_date": "2099-01-01", "evidence_path": "receipts/q1.pdf"}],
        "unresolved_items": [],
        "pricing_status": "DRAFT_READY",
        "final_bid_price_inr": 115000,
        "external_actions_executed": False,
    }


def test_pricing_contract_requires_every_cost_family_and_allows_loss_sensitivity() -> None:
    assert validate_report(report()) == []

    incomplete = report()
    incomplete["cost_waterfall"]["components"] = incomplete["cost_waterfall"]["components"][:-1]
    errors = validate_report(incomplete)
    assert any("missing required components" in error for error in errors)


def test_unknown_costs_must_remain_blocked_and_owner_visible() -> None:
    blocked = report()
    freight = next(item for item in blocked["cost_waterfall"]["components"] if item["key"] == "freight")
    freight.clear()
    freight.update({"key": "freight", "status": "UNKNOWN", "amount_inr": "", "reason": "Freight quote not captured"})
    blocked["pricing_status"] = "BLOCKED"
    blocked["final_bid_price_inr"] = ""
    blocked["unresolved_items"] = ["Freight quote not captured"]

    assert validate_report(blocked) == []
    blocked["pricing_status"] = "DRAFT_READY"
    blocked["final_bid_price_inr"] = 115000
    assert any("DRAFT_READY pricing may not contain UNKNOWN" in error for error in validate_report(blocked))


def test_assumed_cost_requires_active_versioned_assumption() -> None:
    value = report()
    freight = next(item for item in value["cost_waterfall"]["components"] if item["key"] == "freight")
    freight["assumption_id"] = "ASM-freight"

    errors = validate_report(value)

    assert any("does not reference an active versioned pricing assumption" in error for error in errors)


def test_write_pricing_creates_cited_artifacts_and_event(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    result = write_pricing(report(), output_dir=tmp_path / "case", events_path=events, actor="pytest")

    assert result["json_path"].is_file()
    assert result["markdown_path"].is_file()
    event = json.loads(events.read_text(encoding="utf-8").strip())
    assert event["event_type"] == "pricing.gov_draft_recorded"
    assert event["payload"]["pricing_status"] == "DRAFT_READY"
