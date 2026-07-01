from pathlib import Path

from scripts.check_no_private_runtime_data import iter_scan_files, is_tracked_private_runtime_path, scan_line


def test_scan_line_rejects_live_email_and_local_path() -> None:
    findings = scan_line(
        Path("sample.txt"),
        1,
        "Contact owner@example.org and write /Users/example/private.txt",
        [],
    )
    assert any("email:" in item for item in findings)
    assert any("local-user-path" in item for item in findings)


def test_scan_line_allows_example_domain() -> None:
    findings = scan_line(Path("sample.txt"), 1, "Contact buyer@example.com", [])
    assert findings == []


def test_tracked_runtime_path_policy_only_allows_examples() -> None:
    assert is_tracked_private_runtime_path("data/master_cases.csv")
    assert is_tracked_private_runtime_path("outputs/case_reports/live.html")
    assert is_tracked_private_runtime_path("receipts/approvals/live.json")
    assert not is_tracked_private_runtime_path("data/examples/master_cases.example.csv")
    assert not is_tracked_private_runtime_path("outputs/examples/sample.html")
    assert not is_tracked_private_runtime_path("receipts/examples/sample.html")


def test_public_template_scan_uses_declared_public_surface_only() -> None:
    scanned = {str(path.relative_to(Path(__file__).resolve().parents[1])) for path in iter_scan_files(public_template=True)}
    assert "README.md" in scanned
    assert "config/schemas/master_cases.schema.json" in scanned
    assert "data/examples/master_cases.example.csv" in scanned
    assert "cases/EXP-20260630-005/case.md" not in scanned
    assert ".hermes/plans/2026-07-01_142041-tender-export-os-hardening-sprint.md" not in scanned
    assert "data/master_cases.csv" not in scanned
