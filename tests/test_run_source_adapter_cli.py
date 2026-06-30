import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, *args],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=merged,
    )


def test_run_source_adapter_cli_mock_scan_records_event(tmp_path) -> None:
    output = tmp_path / "scan.json"
    events = tmp_path / "events.jsonl"
    result = run_cmd(
        "scripts/run_source_adapter.py",
        "--adapter",
        "mock",
        "--mode",
        "scan",
        "--output",
        str(output),
        "--record-event",
        env={"TENDER_OS_EVENTS_FILE": str(events)},
    )
    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(output.read_text())
    assert data["create_cases"] is False
    assert data["external_side_effects"] is False
    assert "source_adapter.scan_completed" in events.read_text()


def test_run_source_adapter_cli_gem_structured_blocker(tmp_path) -> None:
    output = tmp_path / "gem_scan.json"
    result = run_cmd(
        "scripts/run_source_adapter.py",
        "--adapter",
        "gem",
        "--mode",
        "scan",
        "--keyword",
        "water purifier",
        "--limit",
        "1",
        "--output",
        str(output),
        env={"DEEP_SOURCE_DISABLE_BROWSER": "1", "TENDER_OS_EVENTS_FILE": str(tmp_path / "events.jsonl")},
    )
    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(output.read_text())
    opportunity = data["results"][0]["opportunities"][0]
    assert opportunity["blocker_status"] == "BROWSER_DISABLED_BY_ENV"


def test_deep_report_generates_from_mock_deep_run(tmp_path) -> None:
    source_run = tmp_path / "deep_results.json"
    result = run_cmd(
        "scripts/run_source_adapter.py",
        "--adapter",
        "mock",
        "--mode",
        "deep",
        "--limit",
        "1",
        "--output",
        str(source_run),
        env={"TENDER_OS_EVENTS_FILE": str(tmp_path / "events.jsonl")},
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report = run_cmd("scripts/generate_deep_source_report.py", "--input", str(source_run))
    assert report.returncode == 0, report.stderr or report.stdout
    assert "Wrote deep source report" in report.stdout
