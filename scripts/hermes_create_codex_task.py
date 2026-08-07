#!/usr/bin/env python3
"""Create a fallback Codex task file for manual/app-server-unavailable flows."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INBOX = PROJECT_ROOT / "runtime" / "codex_inbox"
SUPPORTED_ARTIFACT_KINDS = {
    "spreadsheet",
    "pdf",
    "docx",
    "pptx",
    "dashboard",
    "parser",
    "bid_pack",
    "quote_pack",
}


def _project_path(value: str) -> Path:
    candidate = Path(value).expanduser()
    path = (PROJECT_ROOT / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    try:
        path.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"Path escapes project root: {value}") from exc
    return path


def _relative_project_path(value: str) -> str:
    return str(_project_path(value).relative_to(PROJECT_ROOT.resolve()))


def _allowed_output(path_value: str, allowed_paths: list[str]) -> bool:
    output = _project_path(path_value)
    return any(output.is_relative_to(_project_path(root)) for root in allowed_paths)


def build_artifact_request(
    case_id: str,
    artifact_kind: str,
    input_artifacts: list[dict[str, str]],
    expected_outputs: list[str],
    allowed_paths: list[str],
    required_output_schema: str,
    prohibited_claims: list[str],
    *,
    workflow_type: str = "",
) -> dict[str, Any]:
    """Build a typed Codex artifact request with path and source-hash boundaries."""
    if artifact_kind not in SUPPORTED_ARTIFACT_KINDS:
        raise ValueError(f"Unsupported artifact kind: {artifact_kind}")
    if not case_id or "/" in case_id or "\\" in case_id or ".." in case_id:
        raise ValueError("case_id must be a bounded identifier")
    if not input_artifacts:
        raise ValueError("At least one source artifact hash is required")
    if not expected_outputs or not allowed_paths or not required_output_schema or not prohibited_claims:
        raise ValueError("Expected outputs, allowed paths, output schema, and prohibited claims are required")

    source_hashes: list[dict[str, str]] = []
    for artifact in input_artifacts:
        if not isinstance(artifact, dict) or not artifact.get("path") or not artifact.get("sha256"):
            raise ValueError("Every source artifact requires path and sha256")
        path = _project_path(str(artifact["path"]))
        digest = str(artifact["sha256"])
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.lower()):
            raise ValueError(f"Invalid sha256 for source artifact: {artifact['path']}")
        if not path.is_file():
            raise ValueError(f"Source artifact does not exist: {artifact['path']}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest.lower():
            raise ValueError(f"Source artifact sha256 mismatch: {artifact['path']}")
        source_hashes.append({"path": str(path.relative_to(PROJECT_ROOT.resolve())), "sha256": digest.lower()})

    normalized_allowed = [_relative_project_path(value) for value in allowed_paths]
    normalized_outputs = [_relative_project_path(value) for value in expected_outputs]
    if any(not _allowed_output(output, allowed_paths) for output in expected_outputs):
        raise ValueError("Expected output escapes allowed_paths")
    normalized_schema = _relative_project_path(required_output_schema)
    inferred_workflow = workflow_type or ("GOV" if case_id.startswith("GOV-") else "EXPORT" if case_id.startswith("EXP-") else "SYSTEM")
    if inferred_workflow not in {"GOV", "EXPORT", "SYSTEM"}:
        raise ValueError("workflow_type must be GOV, EXPORT, or SYSTEM")
    packet = {
        "schema_version": "codex_artifact_task.v1",
        "task_type": "CODEX_ARTIFACT",
        "case_id": case_id,
        "artifact_kind": artifact_kind,
        "workflow_type": inferred_workflow,
        "task": "Produce an internal draft artifact only; preserve unknowns and prohibited claims.",
        "source_artifact_hashes": source_hashes,
        "expected_outputs": normalized_outputs,
        "allowed_paths": normalized_allowed,
        "required_output_schema": normalized_schema,
        "prohibited_claims": [str(claim) for claim in prohibited_claims],
        "approval_boundary": "Codex may not send, upload, submit, pay, sign, contact, or finalize commercial/legal/classification/origin/delivery claims.",
        "external_actions_executed": False,
    }
    packet["input_fingerprint"] = hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return packet


def build_gov_bid_pack_task(case_id: str, input_artifacts: list[str]) -> dict[str, Any]:
    """Build a bounded, approval-safe packet for Codex artifact production."""
    pack_root = f"outputs/bid_packs/{case_id}"
    receipt_path = f"receipts/plugin_runs/{case_id}_bid_pack.json"
    packet = {
        "schema_version": "codex_bid_pack_task.v1",
        "task_type": "GOV_BID_PACK",
        "case_id": case_id,
        "workflow_type": "GOV",
        "task": "Build an internal draft bid pack only; do not submit, upload, contact, pay, use DSC, or make final commitments.",
        "input_artifacts": input_artifacts,
        "output_root": pack_root,
        "required_artifact_kinds": [
            "bid_cover",
            "boq",
            "compliance_matrix",
            "eligibility_declaration",
            "supplier_summary",
            "emd_security_plan",
            "delivery_plan",
            "risk_register",
            "missing_items_list",
        ],
        "required_outputs": [
            f"{pack_root}/artifact_manifest.json",
            f"{pack_root}/missing_items.md",
            f"{pack_root}/verification_receipt.json",
            receipt_path,
        ],
        "verification_required": ["open", "render", "parse", "manifest", "missing_items", "plugin_receipt"],
        "approval_boundary": "No approval card may be created until codex_task_runner verifies the completed pack.",
        "external_actions_executed": False,
    }
    packet["input_fingerprint"] = hashlib.sha256(
        json.dumps(packet, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return packet


def build_export_quote_pack_task(case_id: str, input_artifacts: list[str]) -> dict[str, Any]:
    """Build a bounded internal EXPORT quote-pack packet for Codex."""
    pack_root = f"outputs/export_quote_packs/{case_id}"
    receipt_path = f"receipts/plugin_runs/{case_id}_export_quote_pack.json"
    packet = {
        "schema_version": "codex_export_quote_pack_task.v1",
        "task_type": "EXPORT_QUOTE_PACK",
        "case_id": case_id,
        "workflow_type": "EXPORT",
        "task": "Build an internal draft export quote pack only; do not send, contact, quote externally, accept an order, ship, invoice, pay, or make final price, classification, origin, or delivery commitments.",
        "input_artifacts": input_artifacts,
        "output_root": pack_root,
        "required_artifact_kinds": [
            "proforma_invoice_draft", "product_specification", "supplier_summary", "pricing_waterfall",
            "compliance_caveats", "incoterm_payment_proposal", "validity_delivery_assumptions", "missing_items_list",
        ],
        "required_outputs": [
            f"{pack_root}/artifact_manifest.json", f"{pack_root}/missing_items.md", f"{pack_root}/verification_receipt.json", receipt_path,
        ],
        "verification_required": ["open", "render", "parse", "commercial_readiness", "manifest", "missing_items", "plugin_receipt"],
        "approval_boundary": "No export quotation approval card may be created until codex_task_runner verifies the completed pack.",
        "external_actions_executed": False,
        "final_claims_approved": False,
    }
    packet["input_fingerprint"] = hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Create fallback Codex task")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--bid-pack", action="store_true", help="Create the governed GOV bid-pack task packet")
    parser.add_argument("--export-quote-pack", action="store_true", help="Create the governed EXPORT quote-pack task packet")
    parser.add_argument("--artifact-kind", choices=sorted(SUPPORTED_ARTIFACT_KINDS), help="Create a generic governed artifact request")
    parser.add_argument("--source-artifact", action="append", default=[], metavar="PATH=SHA256", help="Hashed source artifact for --artifact-kind")
    parser.add_argument("--expected-output", action="append", default=[], help="Expected output path for --artifact-kind")
    parser.add_argument("--allowed-path", action="append", default=[], help="Allowed output directory for --artifact-kind")
    parser.add_argument("--required-output-schema", default="config/schemas/codex_artifact_task.schema.json")
    parser.add_argument("--prohibited-claim", action="append", default=[], help="Claim Codex must not finalize")
    parser.add_argument("--input-artifact", action="append", default=[], help="Input artifact path for --bid-pack; may be repeated")
    parser.add_argument("--reason", default="Codex App-Server Runtime unavailable or not selected.")
    args = parser.parse_args()

    selected_types = sum(bool(value) for value in (args.bid_pack, args.export_quote_pack, args.artifact_kind))
    if selected_types > 1:
        parser.error("Choose only one governed artifact task type.")
    if not args.bid_pack and not args.export_quote_pack and not args.artifact_kind and not args.task:
        parser.error("Provide --task, --bid-pack, --export-quote-pack, or --artifact-kind.")
    timestamp = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    path = INBOX / f"{timestamp}_{args.case_id}.json"
    INBOX.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "case_id": args.case_id,
        "task": args.task or "Build governed internal Codex pack.",
        "reason": args.reason,
        "approval_boundary": "No external, financial, legal, DSC, final quote, HSN/ITC-HS, origin, or delivery commitment action.",
        "status": "PENDING_CODEX_FALLBACK",
    }
    if args.bid_pack:
        payload.update(build_gov_bid_pack_task(args.case_id, args.input_artifact))
        payload["status"] = "PENDING_CODEX_BID_PACK"
    if args.export_quote_pack:
        payload.update(build_export_quote_pack_task(args.case_id, args.input_artifact))
        payload["status"] = "PENDING_CODEX_EXPORT_QUOTE_PACK"
    if args.artifact_kind:
        source_artifacts: list[dict[str, str]] = []
        for item in args.source_artifact:
            source_path, separator, digest = item.partition("=")
            if not separator or not source_path or not digest:
                parser.error("--source-artifact must use PATH=SHA256")
            source_artifacts.append({"path": source_path, "sha256": digest})
        try:
            packet = build_artifact_request(
                args.case_id,
                args.artifact_kind,
                source_artifacts,
                args.expected_output,
                args.allowed_path,
                args.required_output_schema,
                args.prohibited_claim or ["final price", "final classification", "origin", "delivery commitment"],
            )
        except ValueError as exc:
            parser.error(str(exc))
        payload.update(packet)
        payload["status"] = "PENDING_CODEX_ARTIFACT"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
