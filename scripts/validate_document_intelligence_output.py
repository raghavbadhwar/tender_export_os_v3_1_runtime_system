#!/usr/bin/env python3
"""Validate a Document Intelligence + Evidence Archive bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_path(errors: list[str], field: str, value: Any, must_be_file: bool = True) -> Path | None:
    if not value:
        errors.append(f"missing {field}")
        return None
    path = Path(str(value))
    if must_be_file and not path.is_file():
        errors.append(f"{field} does not exist or is not a file: {path}")
    elif not must_be_file and not path.exists():
        errors.append(f"{field} does not exist: {path}")
    return path


def validate_bundle(output_dir: Path | str) -> list[str]:
    output_path = Path(output_dir)
    errors: list[str] = []
    manifest_path = output_path / "manifest.json"
    if not manifest_path.is_file():
        return [f"manifest.json missing: {manifest_path}"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"manifest.json invalid JSON: {exc}"]

    for field in ["run_id", "created_at", "summary", "documents", "tool_statuses"]:
        if field not in manifest:
            errors.append(f"manifest missing field: {field}")
    if manifest.get("external_side_effects") is not False:
        errors.append("external_side_effects must be false")
    if manifest.get("cases_created") != 0:
        errors.append("cases_created must be 0")
    _require_path(errors, "report_path", manifest.get("report_path"))

    documents = manifest.get("documents") or []
    if not isinstance(documents, list):
        errors.append("documents must be a list")
        return errors
    for index, doc in enumerate(documents, start=1):
        prefix = f"documents[{index}]"
        for field in ["source_filename", "sha256", "source_copy_path", "archived_source_path", "archive_metadata_path", "markdown_path"]:
            if not doc.get(field):
                errors.append(f"{prefix} missing {field}")
        source_copy = _require_path(errors, f"{prefix}.source_copy_path", doc.get("source_copy_path"))
        archived = _require_path(errors, f"{prefix}.archived_source_path", doc.get("archived_source_path"))
        _require_path(errors, f"{prefix}.archive_metadata_path", doc.get("archive_metadata_path"))
        _require_path(errors, f"{prefix}.markdown_path", doc.get("markdown_path"))
        if source_copy and source_copy.is_file() and doc.get("sha256") and _sha256(source_copy) != doc["sha256"]:
            errors.append(f"{prefix}.source_copy_path sha256 mismatch")
        if archived and archived.is_file() and doc.get("sha256") and _sha256(archived) != doc["sha256"]:
            errors.append(f"{prefix}.archived_source_path sha256 mismatch")
        for table_path in doc.get("table_csv_paths") or []:
            _require_path(errors, f"{prefix}.table_csv_paths", table_path)
        for table_path in doc.get("table_xlsx_paths") or []:
            _require_path(errors, f"{prefix}.table_xlsx_paths", table_path)

    summary = manifest.get("summary") or {}
    if summary.get("documents_total") is not None and summary.get("documents_total") < len(documents):
        errors.append("summary.documents_total cannot be less than document records")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", help="Directory containing manifest.json")
    parser.add_argument("--json", action="store_true", help="Print JSON validation result")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_bundle(Path(args.bundle_dir))
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2, ensure_ascii=False))
    elif errors:
        print("Document intelligence validation failed:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Document intelligence validation passed")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
