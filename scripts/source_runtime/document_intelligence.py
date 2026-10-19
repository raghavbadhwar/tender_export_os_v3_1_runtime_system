"""Document Intelligence + Evidence Archive lane for Tender Export OS.

This module is intentionally deterministic and local-only. It converts local
source documents into a bounded evidence bundle for human/repo review; it does
not create cases, send messages, log into portals, upload documents, or make
external commitments.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import mimetypes
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .document_parser import ParseResult, parse_document
from .evidence_store import PROJECT_ROOT, safe_name

DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "document_intelligence"
SUPPORTED_TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".json", ".xml", ".yaml", ".yml"}


def now_utc_compact() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _module_available(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def tool_statuses() -> dict[str, Any]:
    return {
        "pymupdf": "available" if _module_available("fitz") else "missing",
        "pdfplumber": "available" if _module_available("pdfplumber") else "missing",
        "pandas": "available" if _module_available("pandas") else "missing",
        "openpyxl": "available" if _module_available("openpyxl") else "missing",
        "ocrmypdf": "available" if shutil.which("ocrmypdf") else "missing_optional",
        "archivebox": "available" if shutil.which("archivebox") else "missing_optional",
        "archive_mode": "local_copy_hash_manifest",
    }


def _copy_source(path: Path, target_dir: Path, sha256: str) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{path.stem}_{sha256[:10]}{path.suffix.lower()}"
    shutil.copy2(path, target)
    return target


def _parse_plain_text(path: Path) -> ParseResult:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return ParseResult(
        source_path=str(path),
        parse_status="PARSED" if text.strip() else "FAILED",
        confidence="HIGH" if text.strip() else "FAILED",
        text=text,
        tables=[],
        notes="plain_text_parser",
    )


def _parse_source(path: Path) -> ParseResult:
    if path.suffix.lower() in SUPPORTED_TEXT_SUFFIXES:
        return _parse_plain_text(path)
    return parse_document(path)


def _maybe_ocr_pdf(path: Path, output_dir: Path, enable_ocr: bool) -> tuple[Path | None, str, str]:
    """Return OCR PDF path, OCR status, note."""
    if path.suffix.lower() != ".pdf":
        return None, "NOT_APPLICABLE", ""
    if not enable_ocr:
        return None, "SKIPPED_DISABLED", "OCR fallback disabled"
    if not shutil.which("ocrmypdf"):
        return None, "MISSING_TOOL", "ocrmypdf command not installed"
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{path.stem}_ocr.pdf"
    proc = subprocess.run(
        ["ocrmypdf", "--skip-text", str(path), str(target)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=240,
    )
    if proc.returncode == 0 and target.exists():
        return target, "OCR_APPLIED", (proc.stdout + "\n" + proc.stderr).strip()[:1000]
    return None, "FAILED", (proc.stdout + "\n" + proc.stderr).strip()[:1000]


def _table_rows(table: Any) -> list[list[str]]:
    if isinstance(table, dict):
        rows = table.get("rows") or []
    else:
        rows = table or []
    normalized: list[list[str]] = []
    for row in rows:
        if isinstance(row, (list, tuple)):
            normalized.append(["" if cell is None else str(cell) for cell in row])
        else:
            normalized.append([str(row)])
    return normalized


def _write_markdown(path: Path, result: ParseResult, out_dir: Path, record: dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{safe_name(path.stem)}.md"
    text = result.text or ""
    lines = [
        f"# Extracted document — {path.name}",
        "",
        f"- Source SHA256: `{record['sha256']}`",
        f"- Parse status: `{result.parse_status}`",
        f"- Confidence: `{result.confidence}`",
        f"- Page count: `{result.page_count if result.page_count is not None else ''}`",
        f"- Table count: `{len(result.tables)}`",
        f"- OCR status: `{record.get('ocr_status', '')}`",
        "",
        "## Extracted text",
        "",
        text.strip() or "_No extractable text found._",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def _write_tables(path: Path, tables: list[Any], csv_dir: Path, xlsx_dir: Path) -> tuple[list[str], list[str]]:
    csv_dir.mkdir(parents=True, exist_ok=True)
    xlsx_dir.mkdir(parents=True, exist_ok=True)
    csv_paths: list[str] = []
    xlsx_paths: list[str] = []
    workbook_frames: list[tuple[str, list[list[str]]]] = []
    for index, table in enumerate(tables, start=1):
        rows = _table_rows(table)
        if not rows:
            continue
        csv_path = csv_dir / f"{safe_name(path.stem)}_table_{index}.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)
        csv_paths.append(str(csv_path.resolve()))
        workbook_frames.append((f"table_{index}", rows))

    if workbook_frames:
        try:
            import pandas as pd

            xlsx_path = xlsx_dir / f"{safe_name(path.stem)}_tables.xlsx"
            with pd.ExcelWriter(xlsx_path) as writer:
                for sheet, rows in workbook_frames:
                    frame = pd.DataFrame(rows)
                    frame.to_excel(writer, index=False, header=False, sheet_name=sheet[:31])
            xlsx_paths.append(str(xlsx_path.resolve()))
        except Exception:
            # CSV output is the canonical deterministic table artifact. XLSX is nice-to-have.
            pass
    return csv_paths, xlsx_paths


def _write_archive_metadata(path: Path, archived_path: Path, archive_dir: Path, record: dict[str, Any]) -> Path:
    archive_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = archive_dir / f"{safe_name(path.stem)}_{record['sha256'][:10]}_archive.json"
    payload = {
        "source_path": str(path.resolve()),
        "archived_path": str(archived_path.resolve()),
        "source_filename": path.name,
        "sha256": record["sha256"],
        "size_bytes": record["size_bytes"],
        "mime_type": record["mime_type"],
        "captured_at": now_iso(),
        "archive_method": "local_copy_with_sha256_manifest",
        "external_side_effects": False,
    }
    metadata_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return metadata_path


def _document_record(
    path: Path,
    source_copy: Path,
    archived_source: Path,
    archive_metadata: Path,
    result: ParseResult,
    markdown_path: Path,
    table_csv_paths: list[str],
    table_xlsx_paths: list[str],
    sha256: str,
    ocr_status: str,
    ocr_pdf_path: Path | None,
    ocr_note: str,
) -> dict[str, Any]:
    return {
        "source_path": str(path.resolve()),
        "source_filename": path.name,
        "source_copy_path": str(source_copy.resolve()),
        "archived_source_path": str(archived_source.resolve()),
        "archive_metadata_path": str(archive_metadata.resolve()),
        "sha256": sha256,
        "size_bytes": path.stat().st_size,
        "suffix": path.suffix.lower(),
        "mime_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "parse_status": result.parse_status,
        "confidence": result.confidence,
        "page_count": result.page_count,
        "text_length": len(result.text or ""),
        "table_count": len(result.tables),
        "dates": result.dates,
        "money_amounts": result.money_amounts,
        "notes": result.notes,
        "markdown_path": str(markdown_path.resolve()),
        "table_csv_paths": table_csv_paths,
        "table_xlsx_paths": table_xlsx_paths,
        "ocr_status": ocr_status,
        "ocr_pdf_path": str(ocr_pdf_path.resolve()) if ocr_pdf_path else "",
        "ocr_note": ocr_note,
        "requires_manual_review": result.parse_status != "PARSED" or result.confidence in {"LOW", "FAILED"},
    }


def _write_report(bundle: dict[str, Any], report_path: Path) -> None:
    lines = [
        f"# Document Intelligence + Evidence Archive Report — {bundle['run_id']}",
        "",
        f"- Workflow: `{bundle.get('workflow', '')}`",
        f"- Case ID: `{bundle.get('case_id', '')}`",
        f"- Created: `{bundle['created_at']}`",
        f"- External side effects: `{bundle['external_side_effects']}`",
        f"- Cases created: `{bundle['cases_created']}`",
        f"- Documents parsed: `{bundle['summary']['documents_parsed']}/{bundle['summary']['documents_total']}`",
        f"- Total tables: `{bundle['summary']['total_tables']}`",
        f"- Blockers: `{bundle['summary']['blocker_count']}`",
        "",
        "## Documents",
        "",
        "| File | Status | Confidence | Pages | Text chars | Tables | OCR | Manual review |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for doc in bundle["documents"]:
        lines.append(
            f"| {doc['source_filename']} | {doc['parse_status']} | {doc['confidence']} | "
            f"{doc.get('page_count') or ''} | {doc['text_length']} | {doc['table_count']} | "
            f"{doc['ocr_status']} | {doc['requires_manual_review']} |"
        )
    if bundle.get("blockers"):
        lines += ["", "## Blockers", ""]
        for blocker in bundle["blockers"]:
            lines.append(f"- **{blocker['source_filename']}**: {blocker['reason']} — {blocker.get('detail', '')}")
    lines += [
        "",
        "## Safety contract",
        "",
        "This bundle is internal evidence only. It does not create cases, submit bids, send buyer/supplier messages, commit price/terms/origin/classification, or bypass approval gates.",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_document_intelligence_bundle(
    source_paths: list[str | Path],
    output_dir: str | Path | None = None,
    run_id: str | None = None,
    workflow: str = "GENERAL",
    case_id: str = "",
    archive_inputs: bool = True,
    enable_ocr: bool = False,
) -> dict[str, Any]:
    run_id = run_id or f"docintel_{now_utc_compact()}"
    base_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_ROOT / run_id
    base_dir.mkdir(parents=True, exist_ok=True)

    dirs = {
        "source_files": base_dir / "source_files",
        "ocr_pdf": base_dir / "ocr_pdf",
        "markdown": base_dir / "markdown",
        "tables_csv": base_dir / "tables_csv",
        "tables_xlsx": base_dir / "tables_xlsx",
        "evidence_archive": base_dir / "evidence_archive",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    blockers: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    for raw_path in source_paths:
        source = Path(raw_path).expanduser().resolve()
        if not source.exists() or not source.is_file():
            blockers.append({"source_filename": str(raw_path), "reason": "SOURCE_MISSING", "detail": "File does not exist"})
            continue
        sha = sha256_file(source)
        source_copy = _copy_source(source, dirs["source_files"], sha)
        archived_source = _copy_source(source, dirs["evidence_archive"], sha) if archive_inputs else source_copy

        result = _parse_source(source)
        ocr_pdf_path: Path | None = None
        ocr_status = "NOT_NEEDED"
        ocr_note = ""
        if source.suffix.lower() == ".pdf" and result.parse_status != "PARSED":
            ocr_pdf_path, ocr_status, ocr_note = _maybe_ocr_pdf(source, dirs["ocr_pdf"], enable_ocr)
            if ocr_pdf_path:
                retry = _parse_source(ocr_pdf_path)
                if retry.parse_status == "PARSED":
                    result = retry
            else:
                blockers.append({"source_filename": source.name, "reason": "OCR_NOT_AVAILABLE", "detail": ocr_note})
        elif source.suffix.lower() == ".pdf":
            ocr_status = "SKIPPED_TEXT_PRESENT"

        partial_record = {
            "sha256": sha,
            "size_bytes": source.stat().st_size,
            "mime_type": mimetypes.guess_type(source.name)[0] or "application/octet-stream",
        }
        archive_metadata = _write_archive_metadata(source, archived_source, dirs["evidence_archive"], partial_record)
        markdown_path = _write_markdown(source, result, dirs["markdown"], {**partial_record, "ocr_status": ocr_status})
        table_csv_paths, table_xlsx_paths = _write_tables(source, result.tables, dirs["tables_csv"], dirs["tables_xlsx"])
        record = _document_record(
            source,
            source_copy,
            archived_source,
            archive_metadata,
            result,
            markdown_path,
            table_csv_paths,
            table_xlsx_paths,
            sha,
            ocr_status,
            ocr_pdf_path,
            ocr_note,
        )
        if record["requires_manual_review"]:
            blockers.append({"source_filename": source.name, "reason": "LOW_CONFIDENCE_OR_FAILED_PARSE", "detail": record["notes"]})
        documents.append(record)

    summary = {
        "documents_total": len(source_paths),
        "documents_parsed": sum(1 for doc in documents if doc["parse_status"] == "PARSED"),
        "documents_manual_review": sum(1 for doc in documents if doc["requires_manual_review"]),
        "total_tables": sum(doc["table_count"] for doc in documents),
        "blocker_count": len(blockers),
    }
    manifest_path = base_dir / "manifest.json"
    report_path = base_dir / "extraction_report.md"
    bundle = {
        "run_id": run_id,
        "created_at": now_iso(),
        "workflow": workflow,
        "case_id": case_id,
        "output_dir": str(base_dir.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "report_path": str(report_path.resolve()),
        "tool_statuses": tool_statuses(),
        "external_side_effects": False,
        "cases_created": 0,
        "approval_required_before_external_action": True,
        "archive_inputs": archive_inputs,
        "summary": summary,
        "documents": documents,
        "blockers": blockers,
        "directories": {key: str(path.resolve()) for key, path in dirs.items()},
    }
    manifest_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_report(bundle, report_path)
    # Re-write manifest with final report path guaranteed present.
    manifest_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    return bundle
