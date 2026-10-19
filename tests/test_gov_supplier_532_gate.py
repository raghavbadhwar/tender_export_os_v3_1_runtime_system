from __future__ import annotations

import json
from pathlib import Path

from scripts.gov_supplier_532_gate import evaluate_supplier_532, record_gate_event, write_report
from scripts.quote_proof import classify_quote_proof
from scripts.validate_case_readiness import evaluate_case


HASH = "a" * 64


def case(*, gem: bool = True) -> dict[str, str]:
    return {
        "case_id": "GOV-1",
        "workflow_type": "GOV",
        "source_name": "GeM" if gem else "CPPP",
        "source_url": "https://gem.gov.in/bid/1" if gem else "https://eprocure.gov.in/tender/1",
    }


def candidate(index: int, source_type: str, **updates: str) -> dict[str, str]:
    value = {
        "supplier_id": f"SUP-{index}",
        "supplier_name": f"Supplier {index}",
        "source_type": source_type,
        "blacklisted": "FALSE",
        "watchlisted": "FALSE",
        "source_evidence_path": f"outputs/evidence/private/supplier/{index}.json",
        "source_evidence_sha256": HASH,
        "product_fit_status": "MATCHED",
        "capacity_delivery_evidence_path": f"outputs/evidence/private/supplier/{index}-capacity.json",
        "capacity_delivery_evidence_sha256": HASH,
        "gem_registered": "TRUE",
        "gem_registration_evidence_path": f"outputs/evidence/private/supplier/{index}-gem.json",
        "gem_registration_evidence_sha256": HASH,
    }
    value.update(updates)
    return value


def quote(index: int) -> dict[str, str]:
    return {
        "quote_id": f"Q-{index}",
        "case_id": "GOV-1",
        "supplier_id": f"SUP-{index}",
        "supplier_name": f"Supplier {index}",
        "quote_received_at": "2099-01-02T00:00:00+00:00",
        "quote_proof_type": "quotation_pdf",
        "quote_proof_path": f"receipts/supplier_quotes/Q-{index}.pdf",
        "quote_proof_sha256": "a" * 64,
        "quote_verification_status": "VERIFIED",
        "case_spec_match": "TRUE",
        "product_description": "Verified tender supply",
        "quantity": "100",
        "unit": "set",
        "unit_price_inr": "100",
        "currency": "INR",
        "gst_rate_pct": "18",
        "lead_time_days": "7",
        "delivery_terms": "Delivered at site",
        "payment_terms_offered": "30 days",
        "validity_days": "30",
        "supplier_specific_quote": "TRUE",
    }


def valid_candidates() -> list[dict[str, str]]:
    return [
        candidate(1, "gem_seller"),
        candidate(2, "india_b2b"),
        candidate(3, "local_cluster"),
        candidate(4, "india_b2b"),
        candidate(5, "past_history"),
    ]


def test_gov_532_requires_evidenced_candidates_sources_quotes_capacity_and_gem() -> None:
    report = evaluate_supplier_532(case(), [], [quote(1), quote(2)], valid_candidates())

    assert report["status"] == "PASS"
    assert report["counts"]["eligible_candidate_count"] == 5
    assert report["counts"]["source_type_count"] == 4
    assert report["counts"]["strict_quote_proof_count"] == 2
    assert report["counts"]["strict_quote_supplier_capacity_delivery_count"] == 2
    assert report["required_gem_registration"] is True


def test_532_fails_closed_for_watchlist_or_missing_capacity_delivery_evidence() -> None:
    candidates = valid_candidates()
    candidates[1]["watchlisted"] = "TRUE"
    candidates[0]["capacity_delivery_evidence_path"] = ""

    report = evaluate_supplier_532(case(), [], [quote(1), quote(2)], candidates)

    assert report["status"] == "BLOCKED"
    assert any("requires 5 eligible" in blocker for blocker in report["blockers"])
    assert any("capacity/delivery" in blocker for blocker in report["blockers"])


def test_non_gem_case_does_not_invent_a_gem_registration_requirement() -> None:
    candidates = valid_candidates()
    for item in candidates:
        item["gem_registered"] = ""
        item["gem_registration_evidence_path"] = ""
        item["gem_registration_evidence_sha256"] = ""

    report = evaluate_supplier_532(case(gem=False), [], [quote(1), quote(2)], candidates)

    assert report["status"] == "PASS"
    assert report["required_gem_registration"] is False


def test_supplier_specific_flag_without_retained_proof_asset_is_not_strict() -> None:
    result = classify_quote_proof(
        {
            "quote_id": "Q-MISSING",
            "case_id": "GOV-1",
            "supplier_id": "SUP-1",
            "quote_received_at": "2099-01-01T00:00:00+00:00",
            "quote_proof_type": "quotation_pdf",
            "supplier_specific_quote": "TRUE",
        }
    )

    assert result["is_strict_quote_proof"] is False
    assert "missing quote_proof_path" in result["blockers"]


def test_gate_write_records_canonical_internal_event(tmp_path: Path) -> None:
    report = evaluate_supplier_532(case(), [], [quote(1), quote(2)], valid_candidates())
    paths = write_report(report, tmp_path)
    events = tmp_path / "events.jsonl"

    event_id = record_gate_event(report, report_path=paths["json_path"], events_path=events, actor="pytest")

    event = json.loads(events.read_text(encoding="utf-8").strip())
    assert event["event_id"] == event_id
    assert event["event_type"] == "supplier.readiness_evaluated"


def test_case_readiness_uses_the_same_532_gate_before_pricing() -> None:
    ready_case = case()
    ready_case.update({"status": "PRICING_READY", "opportunity_title": "Fixture", "pricing_done": "TRUE"})

    result = evaluate_case(ready_case, [quote(1), quote(2)], [], suppliers=[], supplier_candidates=valid_candidates())
    blocked = evaluate_case(ready_case, [quote(1), quote(2)], [], suppliers=[], supplier_candidates=valid_candidates()[:4])

    assert not any("supplier 5-3-2 gate" in item for item in result["blockers"])
    assert any("supplier 5-3-2 gate" in item for item in blocked["blockers"])
