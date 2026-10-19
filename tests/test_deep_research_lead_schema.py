import json
from pathlib import Path

import yaml

from scripts.stage_deep_research_leads import load_schema, parse_input, validate_leads


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "deep_research_leads"
ROUTING = PROJECT_ROOT / "config" / "research_capture_routing.yaml"


def test_deep_research_lead_schema_contains_required_contract_fields() -> None:
    schema = load_schema()
    required = set(schema["required_fields"])
    assert {
        "lead_id",
        "research_report_id",
        "source_url",
        "buyer_name",
        "evidence_level",
        "recommended_repo_action",
        "owner_review_required",
    }.issubset(required)
    assert "PUBLIC_LISTING_ONLY" in schema["evidence_levels"]
    assert "CREATE_CASE_CANDIDATE_AFTER_EVIDENCE" in schema["allowed_recommended_repo_actions"]
    assert "SEND_QUOTE" in schema["forbidden_recommended_repo_actions"]


def test_deep_research_case_candidate_levels_match_routing_contract() -> None:
    schema = load_schema()
    routing = yaml.safe_load(ROUTING.read_text(encoding="utf-8"))
    routed_levels = set(routing["low_competition_orders"]["case_candidate_requires_any"])
    schema_levels = set(schema["evidence_levels"])
    case_candidate_levels = set(schema["case_candidate_evidence_levels"])

    assert routed_levels <= schema_levels
    assert routed_levels <= case_candidate_levels


def test_good_deep_research_leads_validate() -> None:
    schema = load_schema()
    leads, _meta = parse_input(FIXTURES / "good_leads.json")
    normalized, errors, warnings = validate_leads(leads, schema)
    assert errors == []
    assert warnings == []
    assert len(normalized) == 2
    assert normalized[0]["case_candidate_allowed"] is False
    assert normalized[1]["case_candidate_allowed"] is True


def test_forbidden_actions_in_staged_leads_are_rejected() -> None:
    schema = load_schema()
    leads, _meta = parse_input(FIXTURES / "forbidden_action_leads.json")
    _normalized, errors, _warnings = validate_leads(leads, schema)
    assert any("forbidden recommended_repo_action SEND_QUOTE" in error for error in errors)


def test_public_listing_only_cannot_become_bid_ready() -> None:
    schema = load_schema()
    leads, _meta = parse_input(FIXTURES / "public_listing_only.json")
    normalized, errors, warnings = validate_leads(leads, schema)
    assert errors == []
    assert normalized[0]["recommended_repo_action"] == "MANUAL_SOURCE_CHECK"
    assert normalized[0]["case_candidate_allowed"] is False
    assert normalized[0]["operational_stage"] == "LEAD_STAGING"
    assert any("PUBLIC_LISTING_ONLY is a lead" in warning for warning in warnings)


def test_required_field_validation_accepts_non_empty_lists() -> None:
    schema = load_schema()
    leads, _meta = parse_input(FIXTURES / "good_leads.json")
    leads[0]["missing_info"] = ["Full tender document", "BOQ", "EMD"]
    _normalized, errors, _warnings = validate_leads(leads, schema)
    assert errors == []


def test_markdown_unfenced_json_appendix_parses(tmp_path) -> None:
    source = json.loads((FIXTURES / "good_leads.json").read_text(encoding="utf-8"))
    report = tmp_path / "deep_research_report.md"
    report.write_text("# Report\n\n## JSON appendix\n\n" + json.dumps(source), encoding="utf-8")
    leads, meta = parse_input(report)
    assert len(leads) == 2
    assert meta["research_report_id"] == "DR-20260701-LOWCOMP-RADAR"


def test_weekly_items_appendix_converts_to_stageable_leads(tmp_path) -> None:
    report = tmp_path / "weekly_source_scout.md"
    report.write_text(
        "# Weekly Scout\n\n```json\n"
        + json.dumps(
            {
                "research_report_id": "DR-20260704-weekly-source-category-expansion-scout",
                "job_name": "TEOS Weekly Source & Category Expansion Scout",
                "items": [
                    {
                        "lead_id": "DR-20260704-SRC-GOV-001",
                        "workflow_type": "GOV",
                        "source_category": "CPPP public tender source family",
                        "sample_urls": ["https://eprocure.gov.in/eprocure/app"],
                        "why_monitor": "National radar for boring maintenance and institutional procurement.",
                        "missing_proof": ["detail page", "NIT/BOQ", "EMD"],
                        "evidence_level": "PUBLIC_LISTING_ONLY",
                        "recommended_repo_action": "WATCH",
                        "owner_review_required": True,
                    }
                ],
            }
        )
        + "\n```\n",
        encoding="utf-8",
    )
    schema = load_schema()
    leads, meta = parse_input(report)
    _normalized, errors, _warnings = validate_leads(leads, schema)
    assert errors == []
    assert meta["parse_note"].startswith("Converted")
    assert leads[0]["source_url"] == "https://eprocure.gov.in/eprocure/app"
    assert leads[0]["lead_title"] == "CPPP public tender source family"
