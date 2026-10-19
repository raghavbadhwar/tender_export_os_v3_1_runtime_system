# Document Intelligence + Evidence Archive Lane

This lane converts local tender/RFQ/supplier documents into deterministic, local-only TEOS evidence bundles.

It is the first implementation from `docs/TOOLING_DEEP_RESEARCH_RECOMMENDATIONS.md`.

## Safety contract

The lane is internal evidence processing only. It does **not**:

- create cases,
- send buyer/supplier messages,
- log into portals,
- upload documents,
- submit bids,
- commit price, origin, HSN/ITC-HS, delivery, or payment terms,
- bypass approval gates.

Each manifest sets:

```json
"external_side_effects": false,
"cases_created": 0,
"approval_required_before_external_action": true
```

## Command

```bash
cd /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system

.venv/bin/python scripts/run_document_intelligence.py \
  /path/to/tender.pdf \
  /path/to/boq.xlsx \
  /path/to/corrigendum.html \
  --workflow GOV \
  --case-id GOV-EXAMPLE-001
```

Optional OCR fallback, only if `ocrmypdf` is installed:

```bash
.venv/bin/python scripts/run_document_intelligence.py scanned.pdf --enable-ocr
```

## Output shape

```text
outputs/document_intelligence/<run_id>/
  manifest.json
  extraction_report.md
  source_files/
  ocr_pdf/
  markdown/
  tables_csv/
  tables_xlsx/
  evidence_archive/
```

## Validation

```bash
.venv/bin/python scripts/validate_document_intelligence_output.py \
  outputs/document_intelligence/<run_id>
```

The validator checks:

- manifest exists and is valid JSON,
- safety fields remain false/zero,
- source copies exist,
- archive copies exist,
- SHA256 values match copied files,
- markdown/table artifacts exist.

## Current local capability baseline

The current no-key lane uses installed local tooling:

- PyMuPDF / `fitz` for PDF text and pages,
- `pdfplumber` for PDF text/tables,
- pandas/openpyxl for Excel and XLSX table output,
- built-in CSV parsing,
- python-docx for DOCX,
- existing TEOS HTML parser for HTML,
- local copy + SHA256 metadata for evidence archiving.

Optional tools not required for the first local lane:

- `ocrmypdf` for scanned-PDF OCR fallback,
- `archivebox` for fuller web/evidence archiving,
- Docling/Marker/Unstructured for heavier layout/document intelligence.

## Promotion rule

This lane produces evidence bundles only. A parsed document can support Deep Read, supplier proof, pricing, compliance, or case creation only after TEOS proof gates and owner approval rules are satisfied.
