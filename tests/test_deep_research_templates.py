from __future__ import annotations

from pathlib import Path

from scripts.stage_deep_research_leads import load_schema, validate_leads


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "prompts" / "deep_research"
GENERIC_TEMPLATES = {
    "export_category_country_thesis.md",
    "competitor_assortment_gap.md",
    "source_scouting.md",
}
ALL_TEMPLATES = GENERIC_TEMPLATES | {"importer_retailer_discovery.md"}


def test_deep_research_templates_use_real_staging_contracts_and_no_mutation_boundary() -> None:
    for name in ALL_TEMPLATES:
        text = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
        assert "Do not mutate" in text or "Do not write or mutate" in text
        assert "no external action" in text.lower()
        assert "authorized by this packet" in text.lower()
        assert "--dry-run" in text
        assert "source_citations" in text
    for name in GENERIC_TEMPLATES:
        text = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
        assert "config/schemas/deep_research_lead_schema.yaml" in text
        assert "scripts/stage_deep_research_leads.py" in text
        assert "recommended_repo_action" in text
    retailer = (TEMPLATE_ROOT / "importer_retailer_discovery.md").read_text(encoding="utf-8")
    assert "config/schemas/buyer_market_research_return.yaml" in retailer
    assert "scripts/stage_buyer_market_research.py" in retailer
    assert "catalogue fit is only a demand hypothesis" in retailer.lower()


def test_generic_template_return_shape_is_accepted_by_existing_lead_staging_schema() -> None:
    schema = load_schema()
    lead = {
        "lead_id": "DR-TEMPLATE-001",
        "research_report_id": "DR-TEMPLATE-20260712",
        "source_url": "https://example.com/source",
        "source_name": "Example public source",
        "buyer_name": "UNKNOWN",
        "buyer_type": "RESEARCH",
        "workflow_type": "RESEARCH",
        "category": "Example category",
        "lead_title": "Example bounded source lead",
        "location": "Global",
        "deadline": "UNKNOWN",
        "evidence_level": "PUBLIC_LISTING_ONLY",
        "why_interesting": "A cited public source exists.",
        "why_low_competition": "Hypothesis only; evidence remains to be captured.",
        "fulfilment_hypothesis": "Validate with the deterministic public evidence lane.",
        "risks": ["No operational evidence yet."],
        "missing_info": ["Official evidence packet."],
        "recommended_repo_action": "WATCH",
        "owner_review_required": True,
        "source_citations": ["https://example.com/source"],
    }
    _, errors, _ = validate_leads([lead], schema)
    assert errors == []
