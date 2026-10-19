from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.teos_job_supervisor import execute_job


def test_supervisor_builds_project_isolated_python_environment(tmp_path, monkeypatch) -> None:
    project_root = tmp_path / "project"
    scripts_dir = project_root / "scripts"
    venv_bin = project_root / ".venv" / "bin"
    scripts_dir.mkdir(parents=True)
    venv_bin.mkdir(parents=True)
    (scripts_dir / "probe.py").write_text("print('ok')\n", encoding="utf-8")
    (venv_bin / "python").write_text("", encoding="utf-8")

    foreign_pythonpath = tmp_path / "foreign-pythonpath"
    foreign_pythonhome = tmp_path / "foreign-pythonhome"
    foreign_venv = tmp_path / "foreign-venv"

    monkeypatch.setenv(
        "PYTHONPATH",
        os.pathsep.join(
            (
                str(foreign_pythonpath / "site-packages"),
                str(foreign_pythonpath / "other-site-packages"),
            )
        ),
    )
    monkeypatch.setenv("PYTHONHOME", str(foreign_pythonhome))
    monkeypatch.setenv("VIRTUAL_ENV", str(foreign_venv))

    captured: dict[str, object] = {}

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["env"] = kwargs["env"]
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    receipt = execute_job(
        {"id": "probe", "task_command": "python scripts/probe.py", "max_runtime_minutes": 1},
        project_root=project_root,
        events_file=tmp_path / "events.jsonl",
        run_log_file=tmp_path / "agent_run_log.csv",
        runner=runner,
        revision="test-revision",
        run_id="JOB-TEST-PROBE",
    )

    environment = captured["env"]
    assert isinstance(environment, dict)
    assert "PYTHONPATH" not in environment
    assert "PYTHONHOME" not in environment
    assert environment["VIRTUAL_ENV"] == str(project_root / ".venv")
    assert environment["PYTHONNOUSERSITE"] == "1"
    assert environment["PATH"].split(os.pathsep)[0] == str(venv_bin)
    assert receipt["status"] == "SUCCESS"