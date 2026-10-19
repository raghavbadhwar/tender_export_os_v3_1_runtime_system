from scripts.generate_daily_brief import get_trailing_30_day_metrics, render_trailing_metrics


def test_owner_brief_trailing_30_day_metrics() -> None:
    cases = [
        {"case_id": "GOV-1", "created_at": "2026-06-25", "status": "REJECTED", "score_gov": "75"},
        {"case_id": "EXP-1", "created_at": "2026-06-20", "status": "WON", "score_export": "85"},
        {"case_id": "OLD-1", "created_at": "2026-04-01", "status": "LOST", "score_gov": "10"},
    ]
    approvals = [
        {"approval_status": "PENDING", "created_at": "2026-06-25T00:00:00+00:00"},
        {"approval_status": "APPROVED", "created_at": "2026-06-25T00:00:00+00:00"},
    ]
    source_health = [{"source_name": "Example", "health_status": "Needs Login"}]
    metrics = get_trailing_30_day_metrics(cases, approvals, source_health, "20260630")
    assert metrics["created"] == 2
    assert metrics["rejected"] == 1
    assert metrics["won"] == 1
    assert metrics["pending_approvals"] == 1
    assert metrics["expired_approvals"] == 1
    assert metrics["average_score"] == 80.0
    assert "Pending approvals" in render_trailing_metrics(metrics)
