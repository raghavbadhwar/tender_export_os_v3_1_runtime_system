from __future__ import annotations

import json
from pathlib import Path

from scripts.evaluate_artifact_champions import evaluate_cases, load_config, write_report


FIXTURE = Path("tests/fixtures/artifact_evaluations/champion_current_pass.json")


def load_fixture() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_artifact_champion_fixture_passes_all_dimensions() -> None:
    report = evaluate_cases(load_fixture(), config=load_config())

    assert report["status"] == "PASS"
    assert report["evaluated_count"] == 4
    assert report["external_actions_executed"] is False
    assert {row["dimension"] for row in report["results"]} == set(load_config()["dimensions"])


def test_artifact_champion_evaluation_detects_regression() -> None:
    cases = load_fixture()
    cases[0]["current_metrics"]["numeric_accuracy"] = 0.5

    report = evaluate_cases(cases, config=load_config())

    assert report["status"] == "FAIL"
    assert any("numeric_accuracy regressed below champion" in error for error in report["errors"])


def test_artifact_champion_evaluation_requires_all_dimensions() -> None:
    report = evaluate_cases(load_fixture()[:-1], config=load_config())

    assert report["status"] == "FAIL"
    assert any("missing evaluation dimension: approval_card_readability" == error for error in report["errors"])


def test_artifact_champion_report_writes_under_output_path(tmp_path: Path) -> None:
    report = evaluate_cases(load_fixture(), config=load_config())
    output = write_report(report, output_path=tmp_path / "artifact_evaluations" / "report.json")

    assert output.is_file()
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["status"] == "PASS"

