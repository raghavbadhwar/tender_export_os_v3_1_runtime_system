from __future__ import annotations

from pathlib import Path

from scripts.validate_dependency_locks import parse_requirement_lines, validate_dependency_files


CI_TEXT = """- run: python scripts/validate_dependency_locks.py --json
- run: python -m pip install -r requirements.lock.txt
- run: python -m pip install -r requirements-mcp.lock.txt
"""


def _write_repo(tmp_path: Path, requirements: str = "foo\n", lock: str = "foo==1.0\n", mcp: str = "bar==2.0\n", mcp_lock: str = "bar==2.0\n", ci: str = CI_TEXT) -> Path:
    (tmp_path / "requirements.txt").write_text(requirements)
    (tmp_path / "requirements.lock.txt").write_text(lock)
    (tmp_path / "requirements-mcp.txt").write_text(mcp)
    (tmp_path / "requirements-mcp.lock.txt").write_text(mcp_lock)
    (tmp_path / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".github/workflows/ci.yml").write_text(ci)
    return tmp_path


def test_current_repository_lock_coverage_passes_without_network() -> None:
    report = validate_dependency_files(Path(__file__).resolve().parents[1])
    assert report["status"] == "PASS", report
    assert report["network_accessed"] is False
    assert report["installation_performed"] is False


def test_unpinned_direct_requirement_is_reported_but_exact_lock_covers_it(tmp_path: Path) -> None:
    report = validate_dependency_files(_write_repo(tmp_path))
    assert report["status"] == "PASS"
    assert any("not exact-pinned" in warning for warning in report["warnings"])


def test_duplicate_conflicting_requirement_fails(tmp_path: Path) -> None:
    report = validate_dependency_files(_write_repo(tmp_path, requirements="foo==1.0\nfoo==2.0\n", lock="foo==2.0\n"))
    assert report["status"] == "BLOCKED"
    assert any("conflicting duplicate" in error for error in report["errors"])


def test_url_and_unpinned_lock_entries_fail(tmp_path: Path) -> None:
    report = validate_dependency_files(_write_repo(tmp_path, requirements="https://example.test/pkg.whl\n", lock="foo==1.0\n"))
    assert report["status"] == "BLOCKED"
    assert any("URL/editable" in error for error in report["errors"])
    report = validate_dependency_files(_write_repo(tmp_path, lock="foo>=1.0\n"))
    assert any("lock entry" in error for error in report["errors"])


def test_markers_are_parsed_without_resolution_or_network(tmp_path: Path) -> None:
    source = "foo>=1; python_version < '3.13'\n"
    values, warnings, errors = parse_requirement_lines(source, lock=False, source="requirements.txt")
    assert values == {"foo": ""}
    assert warnings and not errors
    report = validate_dependency_files(_write_repo(tmp_path, requirements=source))
    assert report["status"] == "PASS"


def test_ci_must_install_both_exact_locks_and_run_validator(tmp_path: Path) -> None:
    ci = "- run: python -m pip install -r requirements.txt\n"
    report = validate_dependency_files(_write_repo(tmp_path, ci=ci))
    assert report["status"] == "BLOCKED"
    assert any("CI" in error for error in report["errors"])
