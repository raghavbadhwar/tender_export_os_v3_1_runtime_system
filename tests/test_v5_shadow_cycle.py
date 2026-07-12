import subprocess

from scripts.run_v5_shadow_cycle import run_cycle


def test_v5_shadow_cycle_stops_and_propagates_failure() -> None:
    calls: list[list[str]] = []

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 9 if len(calls) == 2 else 0, stdout="", stderr="failed")

    report = run_cycle(runner=runner)

    assert report["status"] == "FAIL"
    assert report["exit_code"] == 9
    assert len(calls) == 2
    assert report["external_business_actions"] is False
