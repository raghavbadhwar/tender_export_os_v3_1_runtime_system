#!/usr/bin/env python3
"""Validate GOV/EXPORT pack readiness before approval-card routing."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.codex_bid_pack_contract import verify_bid_pack
    from scripts.codex_export_quote_pack_contract import FORBIDDEN_FINAL_CLAIMS, verify_export_quote_pack
    from scripts.event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from codex_bid_pack_contract import verify_bid_pack  # type: ignore
    from codex_export_quote_pack_contract import FORBIDDEN_FINAL_CLAIMS, verify_export_quote_pack  # type: ignore
    from event_ledger import append_event  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "pack_readiness"


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def resolve_manifest(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("manifest must be a JSON object")
    return value


def _artifact_text_errors(path: Path) -> list[str]:
    if path.suffix.casefold() not in {".md", ".txt", ".html", ".htm", ".csv", ".json"}:
        return []
    try:
        text = path.read_text(encoding="utf-8").casefold()
    except OSError:
        return [f"cannot read text artifact: {path}"]
    return [f"prohibited final claim phrase found in {path.name}: {phrase}" for phrase in FORBIDDEN_FINAL_CLAIMS if phrase in text]


def _pack_root(manifest_path: Path) -> Path:
    return manifest_path.parent


def approval_scope_errors(manifest: dict[str, Any]) -> list[str]:
    scope = manifest.get("approval_scope")
    if not isinstance(scope, dict):
        return ["approval_scope is required"]
    errors: list[str] = []
    for field in ("proposed_action", "approval_boundary", "scope_hash"):
        if not clean(scope.get(field)):
            errors.append(f"approval_scope.{field} is required")
    if scope.get("external_actions_executed") is not False:
        errors.append("approval_scope.external_actions_executed must be false")
    if scope.get("final_claims_approved") is not False:
        errors.append("approval_scope.final_claims_approved must be false")
    return errors


def source_citation_errors(manifest: dict[str, Any]) -> list[str]:
    citations = manifest.get("source_citations")
    if not isinstance(citations, list) or not citations:
        return ["source_citations must be a non-empty list"]
    errors: list[str] = []
    for index, citation in enumerate(citations, start=1):
        if not isinstance(citation, dict):
            errors.append(f"source_citations[{index}] must be an object")
            continue
        if not (clean(citation.get("source_path")) or clean(citation.get("source_url"))):
            errors.append(f"source_citations[{index}] requires source_path or source_url")
        if not clean(citation.get("source_date")):
            errors.append(f"source_citations[{index}].source_date is required")
    return errors


def quote_proof_errors(manifest: dict[str, Any]) -> list[str]:
    receipts = manifest.get("quote_proof_receipts")
    if not isinstance(receipts, list) or len(receipts) < 2:
        return ["quote_proof_receipts requires at least two supplier-specific quote proof entries"]
    errors: list[str] = []
    suppliers: set[str] = set()
    for index, receipt in enumerate(receipts, start=1):
        if not isinstance(receipt, dict):
            errors.append(f"quote_proof_receipts[{index}] must be an object")
            continue
        supplier = clean(receipt.get("supplier_id")) or clean(receipt.get("supplier_name"))
        if not supplier:
            errors.append(f"quote_proof_receipts[{index}] requires supplier_id or supplier_name")
        else:
            suppliers.add(supplier.casefold())
        for field in ("quote_id", "quote_proof_path", "quote_proof_sha256"):
            if not clean(receipt.get(field)):
                errors.append(f"quote_proof_receipts[{index}].{field} is required")
    if len(suppliers) < 2:
        errors.append("quote_proof_receipts must cover two distinct suppliers")
    return errors


def unresolved_unknown_errors(manifest: dict[str, Any]) -> list[str]:
    unresolved = manifest.get("unresolved_unknowns")
    if unresolved is None:
        return ["unresolved_unknowns list is required"]
    if not isinstance(unresolved, list):
        return ["unresolved_unknowns must be a list"]
    if unresolved:
        return ["unresolved_unknowns must be empty before approval-ready pack routing"]
    return []


def artifact_claim_errors(manifest: dict[str, Any], manifest_path: Path) -> list[str]:
    errors: list[str] = []
    root = _pack_root(manifest_path)
    for artifact in manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []:
        if not isinstance(artifact, dict) or not clean(artifact.get("path")):
            continue
        path = (root / clean(artifact["path"])).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            errors.append(f"artifact path escapes pack root: {artifact.get('path')}")
            continue
        errors.extend(_artifact_text_errors(path))
    return errors


def validate_pack(manifest_path: Path, *, workflow_type: str = "", expected_case_id: str = "") -> dict[str, Any]:
    manifest_path = resolve_manifest(manifest_path)
    manifest = load_manifest(manifest_path)
    workflow = clean(workflow_type or manifest.get("workflow_type")).upper()
    if workflow == "GOV":
        base = verify_bid_pack(manifest_path, expected_case_id=expected_case_id)
    elif workflow == "EXPORT":
        base = verify_export_quote_pack(manifest_path, expected_case_id=expected_case_id)
    else:
        base = {"status": "FAIL", "errors": ["workflow_type must be GOV or EXPORT"], "external_actions_executed": False}
    errors = list(base.get("errors") or [])
    errors.extend(approval_scope_errors(manifest))
    errors.extend(source_citation_errors(manifest))
    errors.extend(quote_proof_errors(manifest))
    errors.extend(unresolved_unknown_errors(manifest))
    errors.extend(artifact_claim_errors(manifest, manifest_path))
    report = {
        "schema_version": "pack_readiness.v1",
        "case_id": clean(manifest.get("case_id")),
        "workflow_type": workflow,
        "manifest_path": str(manifest_path),
        "validated_at": utc_now(),
        "base_verification_status": base.get("status"),
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "external_actions_executed": False,
    }
    report["readiness_sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return report


def write_report(report: dict[str, Any], *, output_dir: Path, events_path: Path = DEFAULT_EVENTS_PATH) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    case_id = clean(report["case_id"])
    output_path = output_dir / f"pack_readiness_{case_id}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    event = append_event(
        "artifact.pack_readiness_validated",
        "codex_task_runner",
        case_id=case_id,
        object_type="artifact",
        object_id=f"{case_id}:pack_readiness",
        source="validate_pack_readiness",
        payload={
            "report_path": str(output_path.relative_to(PROJECT_ROOT)) if output_path.is_relative_to(PROJECT_ROOT) else str(output_path),
            "schema_version": report["schema_version"],
            "status": report["status"],
            "readiness_sha256": report["readiness_sha256"],
        },
        citations=[report["manifest_path"], str(output_path.relative_to(PROJECT_ROOT)) if output_path.is_relative_to(PROJECT_ROOT) else str(output_path)],
        idempotency_key=f"pack-readiness:{case_id}:{report['readiness_sha256']}",
        events_file=events_path,
    )
    return {"json_path": str(output_path), "event_id": str(event["event_id"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--workflow-type", default="")
    parser.add_argument("--case-id", default="")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--events", default=str(DEFAULT_EVENTS_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = validate_pack(Path(args.manifest).expanduser(), workflow_type=args.workflow_type, expected_case_id=args.case_id)
    payload: dict[str, Any] = {"status": report["status"], "mode": "write" if args.write else "dry_run", "report": report, "external_actions_executed": False}
    if args.write:
        payload.update(write_report(report, output_dir=Path(args.output_dir).expanduser(), events_path=Path(args.events).expanduser()))
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"Pack readiness: {report['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
