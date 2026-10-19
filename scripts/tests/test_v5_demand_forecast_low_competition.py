import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_v5_demand_forecast_low_competition import (
    active_case_forecasts,
    demand_research_forecasts,
    low_comp_signal_from_case,
    low_competition_candidates,
)


EXTERNAL_WORDS = {"send", "contact", "quote", "submit", "upload", "pay", "dsc", "commit", "invoice"}


def low_comp_json(items):
    return {
        "sections": {
            "best_easy_to_capture_orders": items,
            "retenders_corrigenda_date_extensions": [],
            "repeat_buyers": [],
            "supplier_ready_categories": [],
            "low_emd_opportunities": [],
            "badly_titled_under_seen_opportunities": [],
        }
    }


class V5DemandForecastTests(unittest.TestCase):
    def write_low_comp(self, items):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with handle:
            json.dump(low_comp_json(items), handle)
        return Path(handle.name)

    def test_public_listing_only_is_not_bid_ready(self):
        path = self.write_low_comp(
            [
                {
                    "case_id": "GOV-TEST-001",
                    "buyer": "Example Buyer",
                    "title": "Retender for office stationery",
                    "category_label": "Office stationery",
                    "source": "Example Portal",
                    "source_url": "https://example.com/tender",
                    "low_competition_score": 88,
                    "evidence_level": "PUBLIC_LISTING_ONLY",
                    "bid_ready": True,
                    "missing_info": ["documents/RFQ/source proof required"],
                    "recommended_next_action": "Send supplier quote request",
                }
            ]
        )

        rows = low_competition_candidates(path)

        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["bid_ready"])
        self.assertIn("documents/RFQ/source proof", rows[0]["proof_gap"])
        self.assertNotIn("send", rows[0]["next_safe_action"].lower())

    def test_mock_and_fixture_rows_are_filtered(self):
        path = self.write_low_comp(
            [
                {
                    "case_id": "MOCK-GOV-001",
                    "buyer": "Example Buyer",
                    "title": "Office consumables",
                    "category_label": "Office consumables",
                    "low_competition_score": 90,
                    "evidence_level": "PUBLIC_LISTING_ONLY",
                },
                {
                    "case_id": "GOV-TEST-002",
                    "buyer": "Fixture District Office",
                    "title": "Fixture tender",
                    "category_label": "Office consumables",
                    "low_competition_score": 90,
                    "evidence_level": "PUBLIC_LISTING_ONLY",
                },
            ]
        )

        self.assertEqual(low_competition_candidates(path), [])

    def test_zero_score_placeholder_without_case_id_is_filtered(self):
        path = self.write_low_comp(
            [
                {
                    "case_id": "",
                    "buyer": "Example Buyer",
                    "title": "Placeholder",
                    "category_label": "Office consumables",
                    "low_competition_score": 0,
                    "evidence_level": "PUBLIC_LISTING_ONLY",
                }
            ]
        )

        self.assertEqual(low_competition_candidates(path), [])

    def test_research_lane_stays_research_only(self):
        rows = demand_research_forecasts(
            [
                {
                    "research_id": "DEM-TEST-001",
                    "category_name": "Handicrafts and Artisan Products",
                    "country": "UK",
                    "buyer_type": "Importer",
                    "source_tier": "TIER_1_INSTITUTIONAL",
                    "source_name": "Example Trade Desk",
                    "source_url": "https://example.com/research",
                    "market_fit_score": "85",
                    "source_reliability_score": "80",
                    "evidence_density_score": "70",
                    "recommended_next_action": "Contact buyer for quote",
                    "approval_required": "FALSE",
                }
            ]
        )

        self.assertEqual(rows[0]["evidence_label"], "RESEARCH_ONLY_NOT_RFQ")
        self.assertIn("buyer-specific RFQ/source detail", rows[0]["proof_gap"])
        self.assertNotIn("contact", rows[0]["next_safe_action"].lower())
        self.assertTrue(rows[0]["approval_required_before_external_action"])

    def test_forecast_never_recommends_external_action_for_raw_lead(self):
        rows = active_case_forecasts(
            [
                {
                    "case_id": "EXP-TEST-001",
                    "workflow_type": "EXPORT",
                    "buyer_name": "Example Importer",
                    "product_or_service": "Spices",
                    "source_name": "Example Marketplace",
                    "source_url": "https://example.com/rfq",
                    "status": "NEW",
                    "evidence_level": "RAW_LEAD",
                    "days_to_deadline": "14",
                    "notes": "Buyer asks us to send quote",
                }
            ]
        )

        action = rows[0]["next_safe_action"].lower()
        self.assertIn("capture", action)
        self.assertFalse(any(word in action for word in EXTERNAL_WORDS))

    def test_low_competition_signal_detects_retender_or_corrigendum(self):
        baseline, _ = low_comp_signal_from_case({"opportunity_title": "Supply of office supplies"})
        retender, reason = low_comp_signal_from_case({"opportunity_title": "Retender corrigendum date extension for office supplies"})

        self.assertGreater(retender, baseline)
        self.assertIn(reason, {"retender", "corrigendum", "date extension"})


if __name__ == "__main__":
    unittest.main()
