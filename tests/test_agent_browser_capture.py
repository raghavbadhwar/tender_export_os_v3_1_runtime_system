from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.agent_browser_capture import READ_ONLY_COMMANDS, capture, command, public_hostname


def test_public_hostname_rejects_credentials_and_private_targets() -> None:
    with pytest.raises(ValueError):
        public_hostname("https://user:pass@example.com", resolve_dns=False)
    with pytest.raises(ValueError):
        public_hostname("https://127.0.0.1", resolve_dns=False)
    with pytest.raises(ValueError):
        public_hostname("http://example.com", resolve_dns=False)


def test_command_rejects_non_read_only_action() -> None:
    assert READ_ONLY_COMMANDS == {"open", "snapshot", "get", "screenshot", "close"}
    with pytest.raises(ValueError):
        command(["agent-browser"], "click", "@e1")


def test_capture_uses_only_read_only_commands_and_writes_receipt(tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def fake_runner(args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
        seen.append(args)
        action = next(item for item in args if item in READ_ONLY_COMMANDS)
        if action == "screenshot":
            path = Path(args[args.index("screenshot") + 1])
            path.write_bytes(b"fake-png")
        stdout = '{"success":true,"data":"Public handicraft catalogue"}'
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=stdout, stderr="")

    receipt, receipt_path = capture(
        url="https://example.com/catalogue",
        source_name="Example Retailer",
        output_root=tmp_path,
        resolve_dns=False,
        runner=fake_runner,
    )

    actions = [next(item for item in args if item in READ_ONLY_COMMANDS) for args in seen]
    assert actions == ["open", "snapshot", "get", "screenshot", "close"]
    assert receipt["status"] == "COMPLETED"
    assert receipt["external_business_actions"] is False
    assert receipt_path.is_file()
    assert "click" not in actions
