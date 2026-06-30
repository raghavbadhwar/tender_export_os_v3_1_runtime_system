from pathlib import Path

from scripts.check_no_private_runtime_data import scan_line


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
