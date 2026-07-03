from pathlib import Path

from scripts import run_operating_firm_test_matrix as matrix


def ok_runner(command: list[str]) -> dict[str, object]:
    return {
        "command": " ".join(command),
        "returncode": 0,
        "ok": True,
        "stdout_tail": "ok",
        "stderr_tail": "",
        "timed_out": False,
    }


def test_operating_firm_matrix_separates_codex_need(tmp_path: Path) -> None:
    report = matrix.build_matrix(stamp="20260702090000", runner=ok_runner, project_root=tmp_path)

    assert report["status"] == "PASS"
    assert report["lanes"]["no_codex_core"]["status"] == "PASS"
    assert report["lanes"]["codex_hermes_runtime"]["status"] == "PASS"
    assert report["codex_need"]["required_for_core"] is False
    assert report["codex_need"]["required_for_artifacts"] is True
    no_codex_commands = [result["command"] for result in report["lanes"]["no_codex_core"]["results"]]
    codex_commands = [result["command"] for result in report["lanes"]["codex_hermes_runtime"]["results"]]
    assert any("validate_agent_loops.py" in command for command in no_codex_commands)
    assert any("-m pytest" in command for command in no_codex_commands)
    assert any("check_codex_runtime_readiness.py" in command for command in codex_commands)
    assert any("system_health_check.py --runtime" in command for command in codex_commands)


def test_operating_firm_matrix_core_can_pass_when_codex_fails(tmp_path: Path) -> None:
    def runner(command: list[str]) -> dict[str, object]:
        joined = " ".join(command)
        ok = "check_codex_runtime_readiness.py" not in joined and "system_health_check.py --runtime" not in joined
        return {
            "command": joined,
            "returncode": 0 if ok else 1,
            "ok": ok,
            "stdout_tail": "",
            "stderr_tail": "codex unavailable" if not ok else "",
            "timed_out": False,
        }

    report = matrix.build_matrix(stamp="20260702090001", runner=runner, project_root=tmp_path)

    assert report["status"] == "FAIL"
    assert report["lanes"]["no_codex_core"]["status"] == "PASS"
    assert report["lanes"]["codex_hermes_runtime"]["status"] == "FAIL"
    assert report["codex_need"]["required_for_core"] is False
    assert report["codex_need"]["required_for_artifacts"] is False
    assert report["codex_need"]["core_passed_without_codex"] is True
