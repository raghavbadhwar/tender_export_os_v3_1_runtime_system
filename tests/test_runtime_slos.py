from __future__ import annotations

import json
from pathlib import Path

import subprocess

from scripts.check_runtime_slos import build_exception_cards, check_age, pass_fail, run_checks


def test_check_age_fails_when_no_matching_artifact() -> None:
    result = check_age("missing", "outputs/no-such-file-*.json", 1)

    assert result["status"] == "FAIL"
    assert result["path"] == ""
    assert result["age_hours"] is None


def test_exception_cards_are_written_only_for_failures(tmp_path: Path) -> None:
    checks = [
        pass_fail("good", True, {"detail": 1}),
        pass_fail("bad", False, {"detail": 2}),
    ]

    paths = build_exception_cards(checks, tmp_path)

    assert len(paths) == 1
    card = json.loads(Path(paths[0]).read_text(encoding="utf-8"))
    assert card["check"] == "bad"
    assert card["kanban_mutated"] is False
    assert "recommended_owner_action" in card


def test_runtime_slo_includes_production_readiness_gate_freshness(tmp_path: Path) -> None:
    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[:2] == ["hermes", "gateway"]:
            return subprocess.CompletedProcess(command, 0, stdout="gateway running", stderr="")
        if command[:2] == ["hermes", "kanban"]:
            return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    report = run_checks(
        config={
            "thresholds": {"production_readiness_gate_max_age_hours": 24},
            "exception_routing": {"output_dir": str(tmp_path / "exception_cards")},
        },
        runner=runner,
    )

    names = {check["name"] for check in report["checks"]}
    readiness = next(check for check in report["checks"] if check["name"] == "production_readiness_gate_freshness")
    assert "production_readiness_gate_freshness" in names
    assert readiness["max_age_hours"] == 24.0
