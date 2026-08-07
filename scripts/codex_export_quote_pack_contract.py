#!/usr/bin/env python3
"""Verify an internal EXPORT quote pack before a quotation approval card is created."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.codex_bid_pack_contract import verify_artifact, verify_plugin_receipt
    from scripts.export_commercial_readiness import validate_contract as validate_commercial_readiness
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from codex_bid_pack_contract import verify_artifact, verify_plugin_receipt  # type: ignore
    from export_commercial_readiness import validate_contract as validate_commercial_readiness  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"
SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "export_quote_pack_manifest.schema.json"
FORBIDDEN_FINAL_CLAIMS = ("we guarantee", "confirmed hsn", "confirmed origin", "confirmed delivery", "final price")


def load_contract(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Export quote-pack contract must be an object: {path}")
    return value


def resolve_under(path_value: str, root: Path) -> Path:
    candidate = Path(path_value).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"artifact path escapes its allowed root: {path_value}") from exc
    return resolved


def resolve_project(path_value: str) -> Path:
    candidate = Path(path_value).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (PROJECT_ROOT / candidate).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {path_value}") from exc
    return resolved


def text_claim_errors(path: Path) -> list[str]:
    if path.suffix.casefold() not in {".md", ".txt", ".html", ".htm", ".csv", ".json"}:
        return []
    try:
        content = path.read_text(encoding="utf-8").lower()
    except OSError:
        return ["could not read text artifact for final-claim check"]
    return [f"unapproved final claim phrase found: {phrase}" for phrase in FORBIDDEN_FINAL_CLAIMS if phrase in content]


def commercial_readiness_errors(path: Path, *, case_id: str) -> list[str]:
    if not path.is_file():
        return ["commercial readiness report missing"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"commercial readiness report invalid JSON: {exc}"]
    if not isinstance(value, dict):
        return ["commercial readiness report must be a JSON object"]
    errors = validate_commercial_readiness(value)
    if value.get("case_id") != case_id:
        errors.append("commercial readiness case_id mismatch")
    if value.get("pricing_status") != "DRAFT_READY":
        errors.append("commercial readiness must be DRAFT_READY")
    return errors


def verify_export_quote_pack(manifest_path: Path, *, expected_case_id: str = "") -> dict[str, Any]:
    contract = load_contract()
    if not manifest_path.is_file():
        return {"status": "FAIL", "errors": [f"export quote manifest missing: {manifest_path}"], "external_actions_executed": False}
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": [f"export quote manifest invalid JSON: {exc}"], "external_actions_executed": False}
    if not isinstance(manifest, dict):
        return {"status": "FAIL", "errors": ["export quote manifest must be a JSON object"], "external_actions_executed": False}
    errors: list[str] = []
    for field in contract["required_top_level"]:
        if field not in manifest or manifest.get(field) in (None, ""):
            errors.append(f"manifest missing {field}")
    if manifest.get("schema_version") != contract["schema_version"]:
        errors.append(f"manifest schema_version must be {contract['schema_version']}")
    if manifest.get("workflow_type") != "EXPORT":
        errors.append("manifest workflow_type must be EXPORT")
    if manifest.get("external_actions_executed") is not False:
        errors.append("manifest external_actions_executed must be false")
    if manifest.get("final_claims_approved") is not False:
        errors.append("manifest final_claims_approved must be false")
    if "draft" not in str(manifest.get("unapproved_claims_disclaimer") or "").lower():
        errors.append("manifest must carry an explicit draft-only disclaimer")
    case_id = str(manifest.get("case_id") or "")
    if expected_case_id and case_id != expected_case_id:
        errors.append(f"manifest case_id must be {expected_case_id}")
    pack_root = manifest_path.parent
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []
    kinds = {str(item.get("kind") or "") for item in artifacts if isinstance(item, dict)}
    missing_kinds = sorted(set(contract["required_artifact_kinds"]) - kinds)
    if missing_kinds:
        errors.append("manifest missing artifact kinds: " + ", ".join(missing_kinds))
    artifact_checks: list[dict[str, Any]] = []
    for index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, dict) or not artifact.get("kind") or not artifact.get("path"):
            errors.append(f"artifacts[{index}] requires kind and path")
            continue
        kind = str(artifact["kind"])
        try:
            path = resolve_under(str(artifact["path"]), pack_root)
            check = verify_artifact(path)
            claim_errors = text_claim_errors(path)
        except ValueError as exc:
            check = {"path": str(artifact.get("path") or ""), "open_verified": False, "render_verified": False, "parse_verified": False, "errors": [str(exc)]}
            claim_errors = []
        check["kind"] = kind
        artifact_checks.append(check)
        errors.extend(f"{kind}: {item}" for item in check.get("errors", []))
        errors.extend(f"{kind}: {item}" for item in claim_errors)
    try:
        missing_items_check = verify_artifact(resolve_under(str(manifest.get("missing_items_path") or ""), pack_root))
    except ValueError as exc:
        missing_items_check = {"errors": [str(exc)]}
    errors.extend(f"missing_items: {item}" for item in missing_items_check.get("errors", []))
    try:
        plugin_check = verify_plugin_receipt(resolve_project(str(manifest.get("plugin_receipt_path") or "")), case_id=case_id)
    except ValueError as exc:
        plugin_check = {"errors": [str(exc)], "valid": False}
    errors.extend(f"plugin_receipt: {item}" for item in plugin_check.get("errors", []))
    try:
        packet_check = verify_artifact(resolve_project(str(manifest.get("codex_task_packet_path") or "")))
    except ValueError as exc:
        packet_check = {"errors": [str(exc)]}
    errors.extend(f"codex_task_packet: {item}" for item in packet_check.get("errors", []))
    try:
        readiness_path = resolve_project(str(manifest.get("commercial_readiness_path") or ""))
        readiness_errors = commercial_readiness_errors(readiness_path, case_id=case_id)
    except ValueError as exc:
        readiness_errors = [str(exc)]
    errors.extend(f"commercial_readiness: {item}" for item in readiness_errors)
    stable = {
        "case_id": case_id, "manifest_sha256": manifest_sha256, "artifact_checks": artifact_checks,
        "missing_items_check": missing_items_check, "plugin_receipt_check": plugin_check,
        "packet_check": packet_check, "commercial_readiness_errors": readiness_errors, "errors": sorted(errors),
    }
    return {
        "schema_version": "export_quote_pack_verification.v1", "case_id": case_id, "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_sha256, "verified_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS" if not errors else "FAIL", "artifact_checks": artifact_checks, "missing_items_check": missing_items_check,
        "plugin_receipt_check": plugin_check, "codex_task_packet_check": packet_check, "commercial_readiness_errors": readiness_errors,
        "errors": sorted(errors), "verification_sha256": hashlib.sha256(json.dumps(stable, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
        "external_actions_executed": False,
    }


def verify_recorded_verification_receipt(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "valid": False, "errors": []}
    if not path.is_file():
        result["errors"].append("verification receipt missing")
        return result
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result["errors"].append(f"verification receipt invalid JSON: {exc}")
        return result
    if not isinstance(value, dict):
        result["errors"].append("verification receipt must be a JSON object")
        return result
    for field, expected in (("schema_version", "export_quote_pack_verification.v1"), ("case_id", report.get("case_id")), ("status", "PASS"), ("manifest_sha256", report.get("manifest_sha256")), ("verification_sha256", report.get("verification_sha256"))):
        if value.get(field) != expected:
            result["errors"].append(f"verification receipt {field} is stale or invalid")
    if value.get("external_actions_executed") is not False:
        result["errors"].append("verification receipt external_actions_executed must be false")
    result["valid"] = not result["errors"]
    return result


def verify_export_quote_pack_approval_ready(manifest_path: Path, receipt_path: Path, *, expected_case_id: str = "") -> dict[str, Any]:
    report = verify_export_quote_pack(manifest_path, expected_case_id=expected_case_id)
    receipt = verify_recorded_verification_receipt(receipt_path, report)
    errors = list(report.get("errors") or []) + [f"verification_receipt: {item}" for item in receipt["errors"]]
    report["verification_receipt_check"] = receipt
    report["errors"] = sorted(set(errors))
    report["status"] = "PASS" if not report["errors"] else "FAIL"
    return report


def write_verification_receipt(report: dict[str, Any], *, output_path: Path, events_path: Path = DEFAULT_EVENTS_PATH, actor: str = "codex_task_runner") -> dict[str, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    from scripts.event_ledger import append_event
    event = append_event(
        "artifact.export_quote_pack_verified", actor, case_id=report.get("case_id", ""), object_type="artifact",
        object_id=f"{report.get('case_id', '')}:export_quote_pack", source="codex_export_quote_pack_contract",
        payload={"report_path": str(output_path), "status": report["status"], "verification_sha256": report["verification_sha256"]},
        citations=[str(output_path), str(report.get("manifest_path") or "")],
        idempotency_key=f"export-quote-pack-verification:{report.get('case_id', '')}:{report['verification_sha256']}", events_file=events_path,
    )
    return {"receipt_path": str(output_path), "event_id": str(event["event_id"])}
