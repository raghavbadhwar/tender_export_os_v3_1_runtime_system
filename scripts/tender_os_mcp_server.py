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
    "stage_case_transition",
    "attach_case_evidence",
    "stage_supplier_candidate",
    "record_quote_proof_review",
    "create_internal_approval_card",
    "record_case_outcome",
    "stage_learning_proposal",
    "reconcile_projection_from_receipt",
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


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "case", "internal-write", "receipted"},
)
def stage_case_transition(
    case_id: str,
    from_status: str,
    to_status: str,
    evidence_ids: list[str],
    citations: list[str],
    actor_profile: str,
    idempotency_key: str,
    reason: str,
) -> MCPToolResult:
    """Stage one validated, reversible case transition in the event ledger; never mutates CSV or executes externally."""
    return tools.stage_case_transition(
        case_id=case_id,
        from_status=from_status,
        to_status=to_status,
        evidence_ids=evidence_ids,
        citations=citations,
        actor_profile=actor_profile,
        idempotency_key=idempotency_key,
        reason=reason,
    )


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "evidence", "internal-write", "receipted"},
)
def attach_case_evidence(
    case_id: str,
    evidence_path: str,
    evidence_type: str,
    actor_profile: str,
    idempotency_key: str,
    citations: list[str],
) -> MCPToolResult:
    """Attach a hashed local evidence artifact through the event ledger; no external action is possible."""
    return tools.attach_case_evidence(
        case_id=case_id,
        evidence_path=evidence_path,
        evidence_type=evidence_type,
        actor_profile=actor_profile,
        idempotency_key=idempotency_key,
        citations=citations,
    )


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "supplier", "internal-write", "receipted"},
)
def stage_supplier_candidate(
    case_id: str,
    supplier_id: str,
    supplier_name: str,
    source_type: str,
    evidence_path: str,
    actor_profile: str,
    idempotency_key: str,
    citations: list[str],
) -> MCPToolResult:
    """Stage an evidence-backed supplier candidate without contacting the supplier or changing a projection."""
    return tools.stage_supplier_candidate(
        case_id=case_id,
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        source_type=source_type,
        evidence_path=evidence_path,
        actor_profile=actor_profile,
        idempotency_key=idempotency_key,
        citations=citations,
    )


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "quote-proof", "internal-write", "receipted"},
)
def record_quote_proof_review(
    case_id: str,
    supplier_id: str,
    quote_id: str,
    proof_status: str,
    reason: str,
    quote_proof_path: str = "",
    actor_profile: str = "",
    idempotency_key: str = "",
    citations: list[str] | None = None,
) -> MCPToolResult:
    """Record a validated or rejected supplier quote proof; never sends a quote request or commits price."""
    return tools.record_quote_proof_review(
        case_id=case_id,
        supplier_id=supplier_id,
        quote_id=quote_id,
        proof_status=proof_status,
        quote_proof_path=quote_proof_path,
        reason=reason,
        actor_profile=actor_profile,
        idempotency_key=idempotency_key,
        citations=citations or [],
    )


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "approval", "internal-write", "receipted"},
)
def create_internal_approval_card(
    case_id: str,
    proposed_action: str,
    scope_hash: str,
    card_path: str,
    evidence_ids: list[str],
    actor_profile: str,
    idempotency_key: str,
    citations: list[str],
) -> MCPToolResult:
    """Create a pending internal approval card; this does not approve or execute the proposed action."""
    return tools.create_internal_approval_card(
        case_id=case_id,
        proposed_action=proposed_action,
        scope_hash=scope_hash,
        card_path=card_path,
        evidence_ids=evidence_ids,
        actor_profile=actor_profile,
        idempotency_key=idempotency_key,
        citations=citations,
    )


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "outcome", "internal-write", "receipted"},
)
def record_case_outcome(
    case_id: str,
    outcome_id: str,
    outcome_status: str,
    evidence_path: str,
    actor_profile: str,
    idempotency_key: str,
    citations: list[str],
) -> MCPToolResult:
    """Record verified internal case outcome evidence; never sends, pays, or changes external state."""
    return tools.record_case_outcome(
        case_id=case_id,
        outcome_id=outcome_id,
        outcome_status=outcome_status,
        evidence_path=evidence_path,
        actor_profile=actor_profile,
        idempotency_key=idempotency_key,
        citations=citations,
    )


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "learning", "internal-write", "receipted"},
)
def stage_learning_proposal(
    proposal_id: str,
    case_ids: list[str],
    proposal_type: str,
    summary: str,
    evidence: list[str],
    tests: list[str],
    rollback: str,
    actor_profile: str,
    idempotency_key: str,
    citations: list[str],
) -> MCPToolResult:
    """Stage a reversible learning proposal; no memory, skill, policy, or model promotion occurs here."""
    return tools.stage_learning_proposal(
        proposal_id=proposal_id,
        case_ids=case_ids,
        proposal_type=proposal_type,
        summary=summary,
        evidence=evidence,
        tests=tests,
        rollback=rollback,
        actor_profile=actor_profile,
        idempotency_key=idempotency_key,
        citations=citations,
    )


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    tags={"tender-os", "projection", "internal-write", "receipted"},
)
def reconcile_projection_from_receipt(
    case_id: str,
    receipt_path: str,
    projection_name: str,
    actor_profile: str,
    idempotency_key: str,
    citations: list[str],
    receipt_sha256: str = "",
) -> MCPToolResult:
    """Stage projection reconciliation from a hashed receipt; direct CSV mutation is not exposed."""
    return tools.reconcile_projection_from_receipt(
        case_id=case_id,
        receipt_path=receipt_path,
        receipt_sha256=receipt_sha256,
        projection_name=projection_name,
        actor_profile=actor_profile,
        idempotency_key=idempotency_key,
        citations=citations,
    )


def main() -> None:
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
