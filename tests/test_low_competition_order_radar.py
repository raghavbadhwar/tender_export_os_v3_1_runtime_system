import datetime as dt
from pathlib import Path

from scripts.low_competition_order_radar import (
    DEFAULT_CATEGORIES,
    DEFAULT_KEYWORDS,
    DEFAULT_SCORING,
    load_yaml_config,
    score_case,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KEYWORDS = load_yaml_config(DEFAULT_KEYWORDS)
CATEGORIES = load_yaml_config(DEFAULT_CATEGORIES)
SCORING = load_yaml_config(DEFAULT_SCORING)
TODAY = dt.date(2026, 7, 1)


def make_case(**updates):
    row = {
        "case_id": "GOV-LOW-001",
        "source_name": "Example Public Tender Portal",
        "source_url": "https://example.com/tender/low",
        "opportunity_title": "Supply of miscellaneous item",
        "buyer_name": "Example Buyer",
        "product_or_service": "misc item",
        "estimated_value_inr": "200000",
        "emd_amount_inr": "5000",
        "deadline_date": "2026-07-20",
        "oem_required": "FALSE",
        "past_experience_required": "FALSE",
        "turnover_required_inr": "",
        "delivery_location": "",
        "evidence_level": "PUBLIC_LISTING_ONLY",
        "deep_read_done": "FALSE",
        "notes": "",
    }
    row.update(updates)
    return row


def score(row, supplier_readiness=None, buyer_repeat=None):
    return score_case(
        row,
        keyword_config=KEYWORDS,
        categories_config=CATEGORIES,
        scoring_config=SCORING,
        supplier_readiness=supplier_readiness or {},
        buyer_repeat=buyer_repeat or {},
        today=TODAY,
    )


def test_retender_and_date_extension_get_positive_score() -> None:
    baseline = score(make_case(opportunity_title="Supply of miscellaneous item"))
    retender = score(make_case(opportunity_title="Retender for supply of miscellaneous item date extension corrigendum"))

    assert retender["low_competition_score"] > baseline["low_competition_score"]
    assert "retender_corrigenda" in retender["keyword_hits"]
    assert any("deadline/date extension" in reason for reason in retender["why_this_is_easier"])


def test_high_emd_oem_and_manufacturer_only_reduce_or_block_score() -> None:
    normal = score(make_case(evidence_level="DOCUMENTS_DOWNLOADED", deep_read_done="TRUE"))
    high_emd = score(make_case(evidence_level="DOCUMENTS_DOWNLOADED", deep_read_done="TRUE", emd_amount_inr="250000"))
    oem = score(make_case(evidence_level="DOCUMENTS_DOWNLOADED", deep_read_done="TRUE", oem_required="TRUE"))
    manufacturer_only = score(
        make_case(
            evidence_level="DOCUMENTS_DOWNLOADED",
            deep_read_done="TRUE",
            opportunity_title="Manufacturer only supply of office stationery",
            product_or_service="office stationery",
        )
    )

    assert high_emd["low_competition_score"] < normal["low_competition_score"]
    assert any("EMD" in risk for risk in high_emd["risk_flags"])
    assert oem["low_competition_score"] < normal["low_competition_score"]
    assert any("OEM" in risk for risk in oem["risk_flags"])
    assert manufacturer_only["classification"] in {"AVOID", "WATCHLIST"}
    assert manufacturer_only["classification"] == "AVOID"


def test_supplier_ready_and_repeat_buyer_raise_score() -> None:
    case = make_case(
        opportunity_title="Office stationery printing cartridge rate contract",
        product_or_service="office stationery printing toner cartridge",
        evidence_level="DOCUMENTS_DOWNLOADED",
        deep_read_done="TRUE",
        buyer_name="Repeat District Buyer",
    )
    base = score(case)
    enriched = score(
        case,
        supplier_readiness={
            "office_stationery_printing": {
                "supplier_readiness_score": 85,
                "number_of_suppliers": 5,
                "quote_proof_count": 2,
            }
        },
        buyer_repeat={"repeat district buyer": {"buyer_repeat_score": 80, "past_tender_count": 4}},
    )

    assert enriched["low_competition_score"] >= base["low_competition_score"]
    assert enriched["supplier_readiness_score"] == 85
    assert enriched["repeat_buyer_score"] == 80
    assert any("mapped supplier base" in reason for reason in enriched["why_this_is_easier"])


def test_public_listing_only_is_lead_not_bid_ready() -> None:
    card = score(make_case(opportunity_title="Retender supply of miscellaneous item"))

    assert card["bid_ready"] is False
    assert card["evidence_level"] == "PUBLIC_LISTING_ONLY"
    assert "Keep as lead" in card["recommended_next_action"]
    assert any("documents must be downloaded" in item for item in card["missing_info"])


def test_missing_supplier_evidence_creates_watchlist_instead_of_easy_capture() -> None:
    card = score(
        make_case(
            opportunity_title="Office stationery printing cartridge rate contract",
            product_or_service="office stationery printing toner cartridge",
            evidence_level="DOCUMENTS_DOWNLOADED",
            deep_read_done="TRUE",
        ),
        supplier_readiness={"office_stationery_printing": {"supplier_readiness_score": 20, "number_of_suppliers": 1}},
    )

    assert card["classification"] in {"WATCHLIST", "AVOID"}
    assert any("supplier readiness needs" in item for item in card["missing_info"])
