from scripts.source_runtime.document_parser import parse_document


def test_corrupt_pdf_returns_structured_failure(tmp_path) -> None:
    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"not a pdf")
    result = parse_document(path)
    assert result.parse_status in {"FAILED", "SCANNED_OR_UNREADABLE_PDF"}
    assert result.confidence == "FAILED"
    assert result.notes
