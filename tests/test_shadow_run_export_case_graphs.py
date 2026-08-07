from __future__ import annotations

from scripts.shadow_run_export_case_graphs import build_shadow_report, select_cases


def export_case(case_id: str) -> dict[str, str]:
    return {"case_id": case_id, "workflow_type": "EXPORT", "opportunity_title": case_id, "buyer_name": "Buyer", "status": "WATCHLIST"}


def test_shadow_run_distinguishes_catalogue_targets_from_verified_rfqs() -> None:
    cases = [export_case(f"EXP-TA-{index}") for index in range(1, 5)] + [export_case("EXP-RFQ-1"), export_case("EXP-RFQ-2")]
    rfqs = [
        {"case_id": f"EXP-TA-{index}", "rfq_stage": "BUYER_VISIBLE", "evidence_status": "PARTIAL"}
        for index in range(1, 5)
    ] + [
        {"case_id": "EXP-RFQ-1", "rfq_stage": "RFQ_VERIFIED", "evidence_status": "RFQ_VERIFIED"},
        {"case_id": "EXP-RFQ-2", "rfq_stage": "RFQ_VERIFIED", "evidence_status": "RFQ_VERIFIED"},
    ]

    selected = select_cases(cases, rfqs)
    report = build_shadow_report(cases, rfqs)

    assert len(selected) == 6
    assert report["status"] == "PASS"
    assert report["summary"]["catalogue_targets_blocked_from_commercial_path"] == 4
    assert report["summary"]["rfq_cases_allowed_to_internal_commercial_evaluation"] == 2
    assert all(not record["external_effect_task_keys"] for record in report["records"])
