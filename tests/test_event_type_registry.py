import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_event_type_registry_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_event_type_registry.py"],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "validation passed" in result.stdout
