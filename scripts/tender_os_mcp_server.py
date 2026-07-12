#!/usr/bin/env python3
"""FastMCP stdio server exposing bounded Tender Export OS capabilities to Hermes."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastmcp import FastMCP  # noqa: E402

from scripts.tender_os_mcp_tools import MCPToolResult, TenderOSTools  # noqa: E402


SERVER_NAME = "Tender Export OS — Governed Tools"
SERVER_TOOL_NAMES = [
    "capability_status",
    "get_case",
    "search_cases",
    "assess_opportunity",
    "get_source_health",
    "parse_local_documents",
    "capture_public_web",
    "get_approval_status",
    "evaluate_business_action",
]

mcp = FastMCP(
    SERVER_NAME,
    instructions=(
        "Use these tools for Tender Export OS internal reads, advisory analysis, local document evidence, "
        "and governed public-web capture. Every call is checked by local OPA policy. No tool can send a "
        "message, log into a portal, upload, submit, pay, use DSC, commit price/delivery, finalize HSN/ITC-HS, "
        "or make an origin/legal claim. A policy decision that says an external action could be allowed is not "
        "an execution tool and does not itself perform that action."
    ),
)
tools = TenderOSTools(record_decisions=True)


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "health", "read-only"},
)
def capability_status() -> MCPToolResult:
    """Report the live bounded stack and the heavy services deliberately excluded."""
    return tools.capability_status()


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "case", "read-only"},
)
def get_case(case_id: str) -> MCPToolResult:
    """Read one canonical master-case row by exact case ID; never invent a case."""
    return tools.get_case(case_id)


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "case", "search", "read-only"},
)
def search_cases(status: str = "", workflow_type: str = "", limit: int = 20) -> MCPToolResult:
    """Search canonical cases by exact status/workflow with a hard result limit of 50."""
    return tools.search_cases(status=status, workflow_type=workflow_type, limit=limit)


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "scoring", "fast-kill", "advisory"},
)
def assess_opportunity(case_id: str) -> MCPToolResult:
    """Run deterministic advisory scoring/Fast Kill checks without changing case state."""
    return tools.assess_opportunity(case_id)


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "source-health", "read-only"},
)
def get_source_health(source_name: str = "", limit: int = 20) -> MCPToolResult:
    """Read source-health evidence; login/CAPTCHA/paywall states remain manual blockers."""
    return tools.get_source_health(source_name=source_name, limit=limit)


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "documents", "local-evidence"},
)
def parse_local_documents(
    paths: list[str],
    case_id: str = "",
    workflow: str = "GENERAL",
    enable_ocr: bool = False,
) -> MCPToolResult:
    """Parse and hash 1–20 documents inside this workspace; produces internal evidence only."""
    return tools.parse_local_documents(
        paths=paths,
        case_id=case_id,
        workflow=workflow,
        enable_ocr=enable_ocr,
    )


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    tags={"tender-os", "public-web", "evidence"},
)
def capture_public_web(
    urls: list[str],
    source_name: str,
    case_id: str = "",
    follow_links: bool = False,
    max_pages: int = 5,
    max_depth: int = 1,
) -> MCPToolResult:
    """Capture robots-compliant public HTTPS evidence; no login, form, click, or bypass."""
    return tools.capture_public_web(
        urls=urls,
        source_name=source_name,
        case_id=case_id,
        follow_links=follow_links,
        max_pages=max_pages,
        max_depth=max_depth,
    )


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "approval", "read-only"},
)
def get_approval_status(case_id: str = "", approval_id: str = "") -> MCPToolResult:
    """Read approval metadata; an APPROVED string alone never unlocks execution."""
    return tools.get_approval_status(case_id=case_id, approval_id=approval_id)


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "policy", "approval", "read-only"},
)
def evaluate_business_action(
    action: str,
    case_id: str = "",
    approval_id: str = "",
) -> MCPToolResult:
    """Evaluate T0–T5 policy using real local receipts; never performs the target action."""
    return tools.evaluate_business_action(action=action, case_id=case_id, approval_id=approval_id)


def main() -> None:
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
