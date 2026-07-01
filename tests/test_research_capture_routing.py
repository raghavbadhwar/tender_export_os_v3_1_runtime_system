from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_routing() -> dict:
    return yaml.safe_load((PROJECT_ROOT / "config" / "research_capture_routing.yaml").read_text(encoding="utf-8"))


def test_deep_research_owns_market_discovery() -> None:
    routing = load_routing()
    assert "broad_market_discovery" in routing["deep_research_owns"]
    assert "low_competition_category_discovery" in routing["deep_research_owns"]
    assert routing["decision_rule"]["market_strategy"] == "deep_research"
    assert routing["decision_rule"]["judgment_unknown_sources"] == "deep_research"


def test_python_owns_known_source_capture() -> None:
    routing = load_routing()
    assert "known_source_scan" in routing["python_playwright_owns"]
    assert "public_listing_capture" in routing["python_playwright_owns"]
    assert "pdf_boq_excel_parsing" in routing["python_playwright_owns"]
    assert routing["decision_rule"]["exact_known_source_repetition"] == "python_playwright"
    assert routing["decision_rule"]["document_capture_and_parsing"] == "python_playwright"


def test_python_is_forbidden_from_broad_unbounded_web_research() -> None:
    routing = load_routing()
    assert "broad_unbounded_web_research" in routing["forbidden_for_python"]
    assert "captcha_bypass" in routing["forbidden_for_python"]
    assert "submit_bids" in routing["forbidden_for_deep_research"]
    assert routing["decision_rule"]["memory_and_audit"] == "repo"


def test_low_competition_split_is_explicit() -> None:
    routing = load_routing()
    low_competition = routing["low_competition_orders"]
    assert "theses" in low_competition["deep_research_role"]
    assert "dedupe" in low_competition["python_playwright_role"]
    assert low_competition["public_listing_only"] == "lead_not_bid_ready_case"
