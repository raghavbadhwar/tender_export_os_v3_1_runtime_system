from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_compliance_matrix_markdown_template_has_required_columns() -> None:
    text = (PROJECT_ROOT / "templates" / "compliance_matrix_template.md").read_text(encoding="utf-8")
    required = [
        "clause_id",
        "requirement_text",
        "requirement_type",
        "our_position",
        "evidence_source",
        "evidence_page_or_cell",
        "gap_status",
        "owner_decision_needed",
        "notes",
    ]
    for column in required:
        assert column in text
    assert "Owner review required" in text


def test_compliance_matrix_xlsx_template_exists_with_required_headers() -> None:
    from openpyxl import load_workbook

    path = PROJECT_ROOT / "templates" / "compliance_matrix_template.xlsx"
    assert path.exists()
    workbook = load_workbook(path)
    sheet = workbook.active
    headers = [cell.value for cell in sheet[1]]
    assert headers == [
        "clause_id",
        "requirement_text",
        "requirement_type",
        "our_position",
        "evidence_source",
        "evidence_page_or_cell",
        "gap_status",
        "owner_decision_needed",
        "notes",
    ]
