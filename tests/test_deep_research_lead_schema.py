from pathlib import Path

from scripts.stage_deep_research_leads import load_schema, parse_input, validate_leads


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "deep_research_leads"


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
