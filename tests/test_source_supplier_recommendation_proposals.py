from __future__ import annotations

from scripts.recommend_source_weights import recommendation_for


def test_source_weight_recommendation_is_proposal_not_automatic_change() -> None:
    recommendation = recommendation_for(
        {
            "source_name": "GeM",
            "workflow": "GOV",
            "health_status": "Working",
            "relevance_score": "95",
            "avg_leads_per_week": "12",
            "total_checks": "46",
            "successful_cases": "7",
            "consecutive_failures": "0",
            "login_required": "FALSE",
            "paywalled": "FALSE",
            "last_checked_date": "2099-01-10",
            "last_lead_found": "2099-01-08",
        }
    )

    assert recommendation["proposal_type"] == "SOURCE_WEIGHT_RECOMMENDATION"
    assert recommendation["proposal_status"] == "RECOMMENDATION_ONLY_NOT_APPLIED"
    assert recommendation["sample_size"] == 53
    assert recommendation["observation_window"] == {"start": "2099-01-08", "end": "2099-01-10"}
    assert recommendation["uncertainty"] == "LOW"
    assert recommendation["automatic_change_allowed"] is False
    assert "false_positive_impact" in recommendation
    assert "false_negative_impact" in recommendation
    assert "rollback_plan" in recommendation
