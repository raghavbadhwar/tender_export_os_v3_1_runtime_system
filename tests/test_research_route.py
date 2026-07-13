from __future__ import annotations

from pathlib import Path

import yaml

from scripts.research_route import select_route, validate_route_configs


ROOT = Path(__file__).resolve().parents[1]


def test_unknown_broad_discovery_routes_to_deep_research() -> None:
    route = select_route(
        "export_category_country_thesis",
        source_known=False,
        login_required=False,
        repetition_needed=False,
    )

    assert route["route"] == "chatgpt_deep_research"
    assert route["may_mutate_registers"] is False
    assert route["operational_evidence_required_before_case_progression"] is True


def test_known_repeated_capture_routes_to_deterministic_browser_lane() -> None:
    route = select_route(
        "known_source_scan",
        source_known=True,
        login_required=False,
        repetition_needed=True,
    )

    assert route["route"] == "python_playwright_agent_browser"
    assert route["mode"] == "READ_ONLY_PUBLIC_EVIDENCE"
    assert route["external_actions_allowed"] is False


def test_login_capture_stops_for_owner_authorized_manual_session() -> None:
    route = select_route(
        "portal_document_capture",
        source_known=True,
        login_required=True,
        repetition_needed=True,
    )

    assert route["route"] == "python_playwright_manual_session"
    assert route["status"] == "NEEDS_INPUT"
    assert route["escalation_label"] == "MANUAL_LOGIN_REQUIRED"
    assert route["owner_approval_required"] is True


def test_documents_route_to_codex_and_control_plane_to_hermes() -> None:
    assert select_route("pdf_boq_parsing", True, False, True)["route"] == "codex_artifact_runtime"
    assert select_route("approval_routing", True, False, True)["route"] == "hermes_control_plane"


def test_research_configs_share_one_limits_boundaries_and_evidence_contract() -> None:
    paths = [
        ROOT / "config/research_capture_routing.yaml",
        ROOT / "config/public_web_scraping.yaml",
        ROOT / "config/agent_browser_research.yaml",
        ROOT / "config/deep_source_runtime.yaml",
    ]
    result = validate_route_configs(paths)

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["contract_version"] == 2
    assert result["evidence_root"] == "outputs/evidence/private"
    assert result["redacted_root"] == "outputs/evidence/redacted"
    assert result["hard_limits"] == {
        "max_pages": 50,
        "max_depth": 3,
        "timeout_seconds": 120,
        "max_file_size_mb": 100,
    }
    assert set(result["escalation_labels"]) >= {
        "MANUAL_LOGIN_REQUIRED",
        "CAPTCHA_BLOCKED",
        "PAYWALL_BLOCKED",
        "OWNER_APPROVAL_REQUIRED",
    }


def test_no_route_contract_allows_access_control_bypass() -> None:
    for name in (
        "research_capture_routing.yaml",
        "public_web_scraping.yaml",
        "agent_browser_research.yaml",
        "deep_source_runtime.yaml",
    ):
        data = yaml.safe_load((ROOT / "config" / name).read_text(encoding="utf-8"))
        boundary = data["shared_contract"]["access_boundaries"]
        assert boundary["captcha_bypass"] is False
        assert boundary["login_bypass"] is False
        assert boundary["paywall_bypass"] is False
        assert boundary["external_actions"] is False
