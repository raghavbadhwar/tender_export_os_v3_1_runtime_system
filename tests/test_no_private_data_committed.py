from pathlib import Path

from scripts.check_no_private_runtime_data import is_tracked_private_runtime_path, scan_line


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
