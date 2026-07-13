from __future__ import annotations

import asyncio
import json
from pathlib import Path

import jsonschema

from scripts.tender_os_mcp_server import SERVER_TOOL_NAMES, mcp
from scripts.tender_os_mcp_tools import MCPToolResult, TenderOSTools
from scripts.tender_os_policy import TenderPolicyEngine


def unrecorded_tools() -> TenderOSTools:
    return TenderOSTools(policy=TenderPolicyEngine(), record_decisions=False)


def test_server_exposes_only_the_bounded_nine_tools() -> None:
    async def list_names() -> list[str]:
        return [tool.name for tool in await mcp.list_tools()]

    assert asyncio.run(list_names()) == SERVER_TOOL_NAMES
    assert not any(
        forbidden in name
        for name in SERVER_TOOL_NAMES
        for forbidden in ("send", "submit", "upload", "pay", "dsc", "commit")
    )


def test_get_case_returns_the_typed_contract() -> None:
    result = unrecorded_tools().get_case("GOV-20260630-001")
    assert isinstance(result, MCPToolResult)
    assert result.status == "success"
    assert result.external_side_effects is False
    assert result.data["case"]["case_id"] == "GOV-20260630-001"
    assert result.policy_decision_id.startswith("POL-")
    assert result.source_hashes


def test_result_matches_versioned_json_schema() -> None:
    result = unrecorded_tools().get_case("GOV-20260630-001")
    schema = json.loads(
        Path("config/schemas/mcp_tool_result.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(result.model_dump(mode="json"), schema)


def test_search_cases_is_bounded() -> None:
    result = unrecorded_tools().search_cases(limit=1000)
    assert result.status == "success"
    assert result.data["limit"] == 50
    assert result.data["count"] <= 50


def test_assessment_is_advisory_and_non_mutating() -> None:
    result = unrecorded_tools().assess_opportunity("GOV-20260630-001")
    assert result.status == "success"
    assert result.data["advisory_only"] is True
    assert 0 <= result.data["score"]["total"] <= 100
    assert result.data["fast_kill"]["schema_version"] == "gov_fast_kill.v1"
    assert result.external_side_effects is False


def test_document_tool_rejects_paths_outside_workspace(tmp_path: Path) -> None:
    document = tmp_path / "outside.txt"
    document.write_text("private outside file", encoding="utf-8")
    result = unrecorded_tools().parse_local_documents([str(document)])
    assert result.status == "failed"
    assert "escapes" in result.missing_information[0]


def test_policy_probe_never_exposes_execution() -> None:
    result = unrecorded_tools().evaluate_business_action("submit_tender_bid", "GOV-20260630-001")
    assert result.status == "blocked"
    assert result.data["execution_tool_exposed"] is False
    assert result.approval_required is True


def test_capability_status_reports_selected_stack_and_exclusions() -> None:
    result = unrecorded_tools().capability_status()
    assert result.status == "success"
    assert result.data["active"]["fastmcp"] != "missing"
    assert result.data["active"]["opa"] != "missing"
    assert result.data["mcp_external_execution_tools_exposed"] is False
    assert "temporal" in result.data["deliberately_excluded"]
