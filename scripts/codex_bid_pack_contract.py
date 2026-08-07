#!/usr/bin/env python3
"""Verify an internal GOV bid pack before an approval card can be created."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from xml.etree import ElementTree
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"
SCHEMA_PATH = PROJECT_ROOT / "config" / "schemas" / "bid_pack_manifest.schema.json"


def load_contract(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Bid pack contract must be an object: {path}")
    return value


def resolve_under(path: str, root: Path) -> Path:
    candidate = Path(path).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"artifact path escapes its allowed root: {path}") from exc
    return resolved


def resolve_project(path: str) -> Path:
    candidate = Path(path).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (PROJECT_ROOT / candidate).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {path}") from exc
    return resolved


def render_preview(path: Path) -> tuple[bool, str, str]:
    """Render a local binary artifact to a disposable preview without network access."""
    quicklook = shutil.which("qlmanage")
    if quicklook:
        with tempfile.TemporaryDirectory(prefix="teos-pack-render-") as temporary:
            output_dir = Path(temporary)
            result = subprocess.run(
                [quicklook, "-t", "-s", "1024", "-o", str(output_dir), str(path)],
                capture_output=True,
                text=True,
                timeout=45,
                check=False,
            )
            previews = [item for item in output_dir.rglob("*.png") if item.is_file() and item.stat().st_size > 0]
            if result.returncode == 0 and previews:
                return True, "macOS Quick Look thumbnail", ""
            detail = (result.stderr or result.stdout or "Quick Look produced no preview").strip().replace("\n", " ")
            return False, "macOS Quick Look thumbnail", detail[:300]
    return False, "", "No local binary render verifier is available (requires qlmanage)."


def verify_artifact(path: Path) -> dict[str, Any]:
    result = {
        "path": str(path),
        "exists": path.is_file(),
        "sha256": "",
        "open_verified": False,
        "render_verified": False,
        "parse_verified": False,
        "parse_method": "",
        "render_method": "",
        "errors": [],
    }
    if not path.is_file():
        result["errors"].append("artifact missing")
        return result
    try:
        content = path.read_bytes()
    except OSError as exc:
        result["errors"].append(f"open failed: {exc}")
        return result
    if not content:
        result["errors"].append("artifact is empty")
        return result
    result["open_verified"] = True
    result["sha256"] = hashlib.sha256(content).hexdigest()
    suffix = path.suffix.casefold()
    try:
        if suffix == ".json":
            json.loads(content.decode("utf-8"))
            result["parse_verified"] = True
            result["render_verified"] = True
            result["parse_method"] = "JSON decoder"
            result["render_method"] = "UTF-8 structured text"
        elif suffix in {".md", ".txt", ".html", ".htm", ".csv"}:
            text = content.decode("utf-8")
            result["parse_verified"] = bool(text.strip())
            result["render_verified"] = bool(text.strip())
            result["parse_method"] = "UTF-8 decoder"
            result["render_method"] = "UTF-8 text renderability"
        elif suffix == ".pdf":
            pdftotext = shutil.which("pdftotext")
            if pdftotext:
                parsed = subprocess.run(
                    [pdftotext, str(path), "-"], capture_output=True, text=True, timeout=45, check=False
                )
                result["parse_verified"] = parsed.returncode == 0
                result["parse_method"] = "pdftotext"
                if parsed.returncode != 0:
                    result["errors"].append("PDF text extraction failed")
            else:
                result["errors"].append("PDF parser unavailable (requires pdftotext)")
            result["render_verified"], result["render_method"], render_error = render_preview(path)
            if render_error:
                result["errors"].append(f"PDF render failed: {render_error}")
        elif suffix in {".docx", ".xlsx"}:
            expected_xml = "word/document.xml" if suffix == ".docx" else "xl/workbook.xml"
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path) as archive:
                    if expected_xml in archive.namelist():
                        ElementTree.fromstring(archive.read(expected_xml))
                        result["parse_verified"] = True
                        result["parse_method"] = f"Office ZIP + {expected_xml} XML"
                    else:
                        result["errors"].append(f"Office document missing {expected_xml}")
            else:
                result["errors"].append("Office document is not a valid ZIP container")
            result["render_verified"], result["render_method"], render_error = render_preview(path)
            if render_error:
                result["errors"].append(f"Office render failed: {render_error}")
        else:
            result["errors"].append(f"unsupported artifact type: {suffix or '(none)'}")
    except (ElementTree.ParseError, UnicodeDecodeError, json.JSONDecodeError, OSError, subprocess.TimeoutExpired, zipfile.BadZipFile) as exc:
        result["errors"].append(f"parse/render failed: {exc}")
    if not result["parse_verified"]:
        result["errors"].append("parse verification failed")
    if not result["render_verified"]:
        result["errors"].append("render verification failed")
    return result


def verify_plugin_receipt(path: Path, *, case_id: str) -> dict[str, Any]:
    result = {"path": str(path), "sha256": "", "valid": False, "errors": []}
    if not path.is_file():
        result["errors"].append("plugin receipt missing")
        return result
    try:
        content = path.read_bytes()
        result["sha256"] = hashlib.sha256(content).hexdigest()
        value = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        result["errors"].append(f"plugin receipt invalid JSON: {exc}")
        return result
    if not isinstance(value, dict):
        result["errors"].append("plugin receipt must be a JSON object")
        return result
    for field in ("case_id", "task_id", "runtime", "status", "artifacts", "external_actions_executed"):
        if field not in value:
            result["errors"].append(f"plugin receipt missing {field}")
    if value.get("case_id") != case_id:
        result["errors"].append("plugin receipt case_id mismatch")
    if value.get("status") != "SUCCESS":
        result["errors"].append("plugin receipt status must be SUCCESS")
    if value.get("external_actions_executed") is not False:
        result["errors"].append("plugin receipt external_actions_executed must be false")
    if not isinstance(value.get("artifacts"), list) or not value.get("artifacts"):
        result["errors"].append("plugin receipt artifacts must be a non-empty list")
    result["valid"] = not result["errors"]
    return result


def verify_bid_pack(manifest_path: Path, *, expected_case_id: str = "") -> dict[str, Any]:
    """Perform independent open/render/parse checks without producing a pack."""
    contract = load_contract()
    errors: list[str] = []
    if not manifest_path.is_file():
        return {"status": "FAIL", "errors": [f"artifact manifest missing: {manifest_path}"], "external_actions_executed": False}
    try:
        manifest_content = manifest_path.read_bytes()
        manifest_sha256 = hashlib.sha256(manifest_content).hexdigest()
        manifest = json.loads(manifest_content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": [f"artifact manifest invalid JSON: {exc}"], "external_actions_executed": False}
    if not isinstance(manifest, dict):
        return {"status": "FAIL", "errors": ["artifact manifest must be a JSON object"], "external_actions_executed": False}
    for field in contract["required_top_level"]:
        if field not in manifest or manifest.get(field) in (None, ""):
            errors.append(f"manifest missing {field}")
    if manifest.get("schema_version") != contract["schema_version"]:
        errors.append(f"manifest schema_version must be {contract['schema_version']}")
    if manifest.get("workflow_type") != "GOV":
        errors.append("manifest workflow_type must be GOV")
    if manifest.get("external_actions_executed") is not False:
        errors.append("manifest external_actions_executed must be false")
    case_id = str(manifest.get("case_id") or "")
    if expected_case_id and case_id != expected_case_id:
        errors.append(f"manifest case_id must be {expected_case_id}")
    pack_root = manifest_path.parent
    artifact_checks: list[dict[str, Any]] = []
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []
    kinds = {str(item.get("kind") or "") for item in artifacts if isinstance(item, dict)}
    missing_kinds = sorted(set(contract["required_artifact_kinds"]) - kinds)
    if missing_kinds:
        errors.append("manifest missing artifact kinds: " + ", ".join(missing_kinds))
    for index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, dict):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        kind = str(artifact.get("kind") or "")
        path_text = str(artifact.get("path") or "")
        if not kind or not path_text:
            errors.append(f"artifacts[{index}] requires kind and path")
            continue
        try:
            check = verify_artifact(resolve_under(path_text, pack_root))
        except ValueError as exc:
            check = {"path": path_text, "errors": [str(exc)], "open_verified": False, "render_verified": False, "parse_verified": False}
        check["kind"] = kind
        artifact_checks.append(check)
        errors.extend(f"{kind}: {error}" for error in check.get("errors", []))
    missing_items_path = str(manifest.get("missing_items_path") or "")
    try:
        missing_items_check = verify_artifact(resolve_under(missing_items_path, pack_root))
    except ValueError as exc:
        missing_items_check = {"path": missing_items_path, "errors": [str(exc)], "open_verified": False, "render_verified": False, "parse_verified": False}
    errors.extend(f"missing_items: {error}" for error in missing_items_check.get("errors", []))
    try:
        plugin_check = verify_plugin_receipt(resolve_project(str(manifest.get("plugin_receipt_path") or "")), case_id=case_id)
    except ValueError as exc:
        plugin_check = {"path": str(manifest.get("plugin_receipt_path") or ""), "valid": False, "errors": [str(exc)]}
    errors.extend(f"plugin_receipt: {error}" for error in plugin_check.get("errors", []))
    try:
        task_packet = resolve_project(str(manifest.get("codex_task_packet_path") or ""))
        task_packet_check = verify_artifact(task_packet)
    except ValueError as exc:
        task_packet_check = {"path": str(manifest.get("codex_task_packet_path") or ""), "errors": [str(exc)], "open_verified": False, "render_verified": False, "parse_verified": False}
    errors.extend(f"codex_task_packet: {error}" for error in task_packet_check.get("errors", []))
    stable = {
        "case_id": case_id,
        "manifest_sha256": manifest_sha256,
        "artifact_checks": artifact_checks,
        "missing_items_check": missing_items_check,
        "plugin_receipt_check": plugin_check,
        "codex_task_packet_check": task_packet_check,
        "errors": sorted(errors),
    }
    return {
        "schema_version": "bid_pack_verification.v1",
        "case_id": case_id,
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_sha256,
        "verified_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS" if not errors else "FAIL",
        "artifact_checks": artifact_checks,
        "missing_items_check": missing_items_check,
        "plugin_receipt_check": plugin_check,
        "codex_task_packet_check": task_packet_check,
        "errors": sorted(errors),
        "verification_sha256": hashlib.sha256(json.dumps(stable, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
        "external_actions_executed": False,
    }


def verify_recorded_verification_receipt(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    """Confirm that a persisted PASS receipt proves the current manifest check."""
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
    if value.get("schema_version") != "bid_pack_verification.v1":
        result["errors"].append("verification receipt schema_version is invalid")
    if value.get("case_id") != report.get("case_id"):
        result["errors"].append("verification receipt case_id mismatch")
    if value.get("status") != "PASS":
        result["errors"].append("verification receipt status must be PASS")
    if value.get("external_actions_executed") is not False:
        result["errors"].append("verification receipt external_actions_executed must be false")
    if value.get("manifest_sha256") != report.get("manifest_sha256"):
        result["errors"].append("verification receipt manifest hash is stale")
    if value.get("verification_sha256") != report.get("verification_sha256"):
        result["errors"].append("verification receipt is stale for the current manifest")
    result["valid"] = not result["errors"]
    return result


def verify_bid_pack_approval_ready(
    manifest_path: Path,
    verification_receipt_path: Path,
    *,
    expected_case_id: str = "",
) -> dict[str, Any]:
    """Validate a GOV pack plus the recorded, current PASS verification receipt."""
    report = verify_bid_pack(manifest_path, expected_case_id=expected_case_id)
    receipt_check = verify_recorded_verification_receipt(verification_receipt_path, report)
    errors = list(report.get("errors") or [])
    errors.extend(f"verification_receipt: {item}" for item in receipt_check["errors"])
    report["verification_receipt_check"] = receipt_check
    report["errors"] = sorted(set(errors))
    report["status"] = "PASS" if not report["errors"] else "FAIL"
    return report


def write_verification_receipt(report: dict[str, Any], *, output_path: Path, events_path: Path = DEFAULT_EVENTS_PATH, actor: str = "codex_task_runner") -> dict[str, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    from scripts.event_ledger import append_event

    event = append_event(
        "artifact.bid_pack_verified",
        actor,
        case_id=report.get("case_id", ""),
        object_type="artifact",
        object_id=f"{report.get('case_id', '')}:bid_pack",
        source="codex_bid_pack_contract",
        payload={"report_path": str(output_path), "status": report["status"], "verification_sha256": report["verification_sha256"]},
        citations=[str(output_path), str(report.get("manifest_path") or "")],
        idempotency_key=f"bid-pack-verification:{report.get('case_id', '')}:{report['verification_sha256']}",
        events_file=events_path,
    )
    return {"receipt_path": str(output_path), "event_id": str(event["event_id"])}
