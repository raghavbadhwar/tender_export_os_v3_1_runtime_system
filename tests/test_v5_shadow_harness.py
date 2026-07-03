from scripts.run_v5_forecast_shadow_harness import summarize_payload


def test_shadow_harness_counts_weak_promotions_avoided() -> None:
    summary = summarize_payload(
        {
            "run_id": "RUN-TEST",
            "date": "20260703",
            "summary": {"proof_required_candidates": 1},
            "low_competition_candidates": [
                {
                    "case_id": "GOV-1",
                    "evidence_label": "PUBLIC_LISTING_ONLY",
                    "bid_ready": False,
                    "next_safe_action": "Capture local source proof before any external action.",
                }
            ],
        }
    )

    assert summary["proof_gated_status"] == "PASS"
    assert summary["weak_promotions_avoided"] == 1


def test_shadow_harness_blocks_external_action_for_weak_evidence() -> None:
    summary = summarize_payload(
        {
            "run_id": "RUN-TEST",
            "date": "20260703",
            "research_forecasts": [
                {
                    "case_or_research_id": "DEM-1",
                    "evidence_label": "RAW_LEAD",
                    "next_safe_action": "Contact buyer and send quote",
                }
            ],
        }
    )

    assert summary["proof_gated_status"] == "BLOCKED"
    assert summary["unsafe_weak_actions"] == 1
