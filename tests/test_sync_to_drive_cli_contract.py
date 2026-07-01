import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_sync_to_drive_accepts_public_template_schema_group(tmp_path: Path) -> None:
    output = tmp_path / "drive_manifest.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/sync_to_drive.py",
            "--mode",
            "public-template",
            "--dry-run",
            "--group",
            "00_Schemas",
            "--output",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["mode"] == "dry_run"
    assert manifest["projection_mode"] == "public-template"
    assert manifest["groups"][0]["files"]


def test_sync_to_drive_rejects_schema_group_in_private_runtime_mode(tmp_path: Path) -> None:
    output = tmp_path / "drive_manifest.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/sync_to_drive.py",
            "--mode",
            "private-runtime",
            "--dry-run",
            "--group",
            "00_Schemas",
            "--output",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode != 0
    assert "not found for mode 'private-runtime'" in result.stdout
