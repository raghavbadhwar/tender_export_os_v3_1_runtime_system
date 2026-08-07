from __future__ import annotations

import datetime as dt

from scripts.generate_production_pilot_report import build_report, strict_quote_proof_rate, weekly_review_count


def test_weekly_review_count_dedupes_by_iso_week() -> None:
    rows = [
        {"run_date": "2026-07-01", "actions_taken": "weekly owner review", "notes": ""},
        {"run_date": "2026-07-02", "actions_taken": "weekly owner review", "notes": ""},
        {"run_date": "2026-07-08", "actions_taken": "", "notes": "Weekly review complete"},
    ]

    assert weekly_review_count(rows) == 2


def test_strict_quote_proof_rate_counts_verified_or_supplier_specific() -> None:
    rows = [
        {"supplier_specific_quote": "TRUE", "quote_verification_status": ""},
        {"supplier_specific_quote": "", "quote_verification_status": "VERIFIED"},
        {"supplier_specific_quote": "", "quote_verification_status": "INDICATIVE"},
    ]

    assert strict_quote_proof_rate(rows) == 66.67


def test_production_pilot_without_activation_is_pending_not_historical_blocked() -> None:
    report = build_report(
        config={"duration_days": 30, "pass_criteria": {"weekly_owner_reviews_min": 4}},
        end_date=dt.date(2026, 7, 13),
        state={"status": "PENDING_PREREQUISITES"},
    )

    assert report["status"] == "PENDING_PREREQUISITES"
    assert report["window"]["days"] == 0
    assert report["production_external_authority_expanded"] is False
    assert report["blockers"] == ["production pilot pending prerequisite gates"]
