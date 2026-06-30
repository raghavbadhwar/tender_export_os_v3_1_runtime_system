import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_validate_good_chatgpt_return() -> None:
    result = run_cmd("scripts/validate_chatgpt_return.py", "--input", "tests/fixtures/chatgpt_returns/good_return.md")
    assert result.returncode == 0, result.stderr or result.stdout


def test_validate_bad_chatgpt_returns_fail() -> None:
    missing = run_cmd("scripts/validate_chatgpt_return.py", "--input", "tests/fixtures/chatgpt_returns/bad_missing_sections.md")
    external = run_cmd("scripts/validate_chatgpt_return.py", "--input", "tests/fixtures/chatgpt_returns/bad_external_action.md")
    assert missing.returncode != 0
    assert external.returncode != 0


def test_stage_rejects_invalid_return(tmp_path) -> None:
    inbox = tmp_path / "inbox"
    result = run_cmd(
        "scripts/stage_chatgpt_return.py",
        "--input",
        "tests/fixtures/chatgpt_returns/bad_external_action.md",
        "--inbox",
        str(inbox),
    )
    assert result.returncode == 1
    assert not inbox.exists()


def test_stage_accepts_valid_return(tmp_path) -> None:
    inbox = tmp_path / "inbox"
    result = run_cmd(
        "scripts/stage_chatgpt_return.py",
        "--input",
        "tests/fixtures/chatgpt_returns/good_return.md",
        "--inbox",
        str(inbox),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert list(inbox.iterdir())
