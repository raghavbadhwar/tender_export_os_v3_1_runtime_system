import subprocess
from pathlib import Path

from scripts.check_no_private_runtime_data import is_tracked_private_runtime_path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def tracked_case_private_paths() -> list[str]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "cases/*/evidence/**",
            "cases/**/evidence/**",
            "cases/**/case.md",
            "cases/**/HERMES.md",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return sorted(
        path
        for path in result.stdout.splitlines()
        if path and not path.startswith("cases/examples/")
    )


def test_case_evidence_and_live_case_markdown_are_not_tracked() -> None:
    assert tracked_case_private_paths() == []


def test_case_private_path_policy_allows_only_examples() -> None:
    assert is_tracked_private_runtime_path("cases/GOV-20260630-001/evidence/source.html")
    assert is_tracked_private_runtime_path("cases/GOV-20260630-001/case.md")
    assert is_tracked_private_runtime_path("cases/GOV-20260630-001/HERMES.md")
    assert not is_tracked_private_runtime_path("cases/examples/case.md")
    assert not is_tracked_private_runtime_path("cases/examples/evidence/source.html")
