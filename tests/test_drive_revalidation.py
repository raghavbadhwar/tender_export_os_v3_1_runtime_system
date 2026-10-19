from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.revalidate_drive_knowledge_bus_sync import build_revalidation


def runner_factory(*, auth_returncode: int = 1, dry_run_returncode: int = 0):
    def runner(command, cwd, capture_output, text, timeout, check):
        if "--check-auth" in command:
            return subprocess.CompletedProcess(command, auth_returncode, stdout="", stderr="auth unavailable")
        if "--output" in command:
            output = Path(command[command.index("--output") + 1])
            if dry_run_returncode == 0:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps({"groups": [], "mode": "dry_run"}), encoding="utf-8")
            return subprocess.CompletedProcess(command, dry_run_returncode, stdout="dry run", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    return runner


def test_drive_revalidation_records_dry_run_pass_live_auth_blocked(tmp_path: Path) -> None:
    receipt = build_revalidation(
        runner=runner_factory(auth_returncode=1, dry_run_returncode=0),
        stamp="20990101T000000Z",
        output_dir=tmp_path / "outputs",
        receipt_dir=tmp_path / "receipts",
    )

    assert receipt["status"] == "DRY_RUN_PASS_LIVE_AUTH_BLOCKED"
    assert receipt["live_upload_attempted"] is False
    assert receipt["external_actions_executed"] is False
    assert not str(receipt["receipt_path"]).startswith("/")
    assert any("gws auth login" in step for step in receipt["remediation_steps"])


def test_drive_revalidation_passes_when_auth_and_dry_run_pass(tmp_path: Path) -> None:
    receipt = build_revalidation(
        runner=runner_factory(auth_returncode=0, dry_run_returncode=0),
        stamp="20990101T000000Z",
        output_dir=tmp_path / "outputs",
        receipt_dir=tmp_path / "receipts",
    )

    assert receipt["status"] == "PASS"
    assert not str(receipt["dry_run_manifest"]).startswith("/")
    assert receipt["remediation_steps"] == []


def test_drive_revalidation_fails_when_dry_run_fails(tmp_path: Path) -> None:
    receipt = build_revalidation(
        runner=runner_factory(auth_returncode=0, dry_run_returncode=1),
        stamp="20990101T000000Z",
        output_dir=tmp_path / "outputs",
        receipt_dir=tmp_path / "receipts",
    )

    assert receipt["status"] == "FAIL"
    assert receipt["remediation_steps"]


def test_drive_revalidation_receipt_is_scrubbed_for_public_sync(tmp_path: Path) -> None:
    receipt = build_revalidation(
        runner=runner_factory(auth_returncode=1, dry_run_returncode=0),
        stamp="20990101T000000Z",
        output_dir=tmp_path / "outputs",
        receipt_dir=tmp_path / "receipts",
    )

    serialized = json.dumps(receipt)
    assert "/Users/" not in serialized
    assert str(Path.cwd()) not in serialized
