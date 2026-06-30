import sys
from pathlib import Path
from types import SimpleNamespace

from scripts.source_runtime.document_parser import parse_document


class FakePage:
    def extract_text(self) -> str:
        return "Bid End Date: 31-01-2099\nEMD: INR 5000"

    def extract_tables(self):
        return [[["Item", "Description", "Quantity"], ["1", "RO water purifier", "10"]]]


class FakePdf:
    pages = [FakePage()]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None


def test_pdf_table_extraction_records_page_metadata(tmp_path, monkeypatch) -> None:
    path = tmp_path / "fixture.pdf"
    path.write_bytes(b"not a real pdf; pdfplumber is faked")
    monkeypatch.setitem(sys.modules, "pdfplumber", SimpleNamespace(open=lambda _path: FakePdf()))
    result = parse_document(path)
    assert result.parse_status == "PARSED"
    assert result.tables[0]["page"] == 1
    assert result.tables[0]["table_index"] == 1
    assert result.tables[0]["table_type"] == "BOQ"
