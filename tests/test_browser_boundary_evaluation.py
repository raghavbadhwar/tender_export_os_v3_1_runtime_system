from __future__ import annotations

from pathlib import Path

from scripts.agent_browser_capture import DEFAULT_OUTPUT_ROOT as BROWSER_OUTPUT_ROOT
from scripts.evaluate_browser_boundaries import evaluate, load_spec, validate_spec
from scripts.public_web_evidence_scraper import DEFAULT_OUTPUT_ROOT as STATIC_OUTPUT_ROOT


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "config" / "browser_boundary_eval.yaml"
PRIVATE_ROOT = ROOT / "outputs" / "evidence" / "private"


def test_browser_boundary_spec_covers_all_required_safety_cases_and_profiles() -> None:
    spec = load_spec(SPEC)
    assert validate_spec(spec, project_root=ROOT) == []
    report = evaluate(spec, project_root=ROOT)

    assert report["status"] == "PASS"
    assert {item["boundary"] for item in report["scenario_results"]} == {
        "robots_denial",
        "captcha",
        "login_wall",
        "prompt_injection",
        "redirect",
        "duplicate_content",
        "javascript_rendered",
        "paywall",
        "unreachable_source",
        "source_text_conflict",
    }
    assert len(report["profile_results"]) == len(spec["profiles"]) * len(spec["scenarios"])
    assert all(item["status"] == "PASS" for item in report["profile_results"])
    assert report["external_actions_executed"] is False


def test_raw_browser_evidence_defaults_to_private_evidence_roots() -> None:
    assert BROWSER_OUTPUT_ROOT.resolve().is_relative_to(PRIVATE_ROOT.resolve())
    assert STATIC_OUTPUT_ROOT.resolve().is_relative_to(PRIVATE_ROOT.resolve())
