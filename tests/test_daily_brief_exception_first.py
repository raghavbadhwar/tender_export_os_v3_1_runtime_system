from __future__ import annotations

from scripts.generate_daily_brief import render_exception_first_owner_summary


def test_daily_brief_exception_first_summary_uses_operating_desk_contract() -> None:
    html = render_exception_first_owner_summary(
        {
            "exception_first": {
                "one_primary_action": "Review approval APR-1.",
                "exceptions": [{"case_id": "GOV-1"}],
                "pending_owner_decisions": [{"approval_id": "APR-1"}],
                "expiring_deadlines_or_approvals": [{"case_id": "GOV-1"}],
                "substantive_replies": [{"communication_id": "COM-1"}],
                "missing_strict_proofs": [{"case_id": "GOV-1"}],
                "overdue_payments": [{"case_id": "GOV-1"}],
                "top_three_evidenced_opportunities": [
                    {
                        "case_id": "GOV-1",
                        "title": "Stationery",
                        "workflow_type": "GOV",
                        "evidence_level": "DOCUMENTS_DOWNLOADED",
                    }
                ],
                "forecast_maturity": {
                    "status": "INSUFFICIENT_MATURE_SAMPLE",
                    "mature_sample_size": 0,
                    "minimum_mature_sample": 30,
                },
            }
        }
    )

    assert "Review approval APR-1" in html
    assert "Top evidenced opportunity" in html
    assert "Missing strict proofs: 1" in html
    assert "Forecast maturity" in html
