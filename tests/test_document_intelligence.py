import json
from pathlib import Path

import pytest

from scripts.source_runtime.document_intelligence import run_document_intelligence_bundle
from scripts.validate_document_intelligence_output import validate_bundle


def _make_text_pdf(path: Path, text: str) -> None:
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_document_intelligence_bundle_extracts_and_archives_pdf_csv_html(tmp_path: Path) -> None:
    pdf_path = tmp_path / "tender_notice.pdf"
    _make_text_pdf(
        pdf_path,
        "GOV Tender Notice for spice supply. Deadline 31/07/2026. EMD INR 12,34,567.",
    )
    csv_path = tmp_path / "boq.csv"
    csv_path.write_text("item,qty,unit_price\nTurmeric,10,120\nCumin,5,180\n", encoding="utf-8")
    html_path = tmp_path / "corrigendum.html"
    html_path.write_text(
        "<html><body><h1>Corrigendum</h1><p>Bid date extended to 05 Aug 2026.</p></body></html>",
        encoding="utf-8",
    )

    bundle = run_document_intelligence_bundle(
        [pdf_path, csv_path, html_path],
        output_dir=tmp_path / "bundle",
        run_id="docintel_test_run",
        workflow="GOV",
        case_id="GOV-TEST-001",
        archive_inputs=True,
    )

    assert bundle["external_side_effects"] is False
    assert bundle["cases_created"] == 0
    assert bundle["run_id"] == "docintel_test_run"
    assert len(bundle["documents"]) == 3
    assert bundle["summary"]["documents_parsed"] == 3
    assert bundle["summary"]["total_tables"] >= 1
    assert bundle["summary"]["blocker_count"] == 0

    pdf_record = next(doc for doc in bundle["documents"] if doc["source_filename"] == "tender_notice.pdf")
    assert pdf_record["parse_status"] == "PARSED"
    assert pdf_record["confidence"] in {"MEDIUM", "HIGH"}
    assert pdf_record["page_count"] == 1
    assert any("INR" in value for value in pdf_record["money_amounts"])
    assert Path(pdf_record["markdown_path"]).exists()
    assert "spice supply" in Path(pdf_record["markdown_path"]).read_text(encoding="utf-8")

    csv_record = next(doc for doc in bundle["documents"] if doc["source_filename"] == "boq.csv")
    assert csv_record["table_count"] == 1
    assert csv_record["table_csv_paths"]
    assert Path(csv_record["table_csv_paths"][0]).exists()

    archive_metadata = Path(pdf_record["archive_metadata_path"])
    assert archive_metadata.exists()
    metadata = json.loads(archive_metadata.read_text(encoding="utf-8"))
    assert metadata["sha256"] == pdf_record["sha256"]
    assert Path(metadata["archived_path"]).exists()

    assert Path(bundle["manifest_path"]).exists()
    assert Path(bundle["report_path"]).exists()
    assert not validate_bundle(Path(bundle["output_dir"]))


def test_document_intelligence_validator_catches_missing_archived_source(tmp_path: Path) -> None:
    source = tmp_path / "notice.txt"
    source.write_text("Tender text with deadline 01/08/2026", encoding="utf-8")

    bundle = run_document_intelligence_bundle(
        [source],
        output_dir=tmp_path / "bundle",
        run_id="docintel_broken_archive",
        workflow="EXPORT",
        archive_inputs=True,
    )
    doc = bundle["documents"][0]
    Path(doc["archived_source_path"]).unlink()

    errors = validate_bundle(Path(bundle["output_dir"]))

    assert any("archived_source_path" in error for error in errors)
