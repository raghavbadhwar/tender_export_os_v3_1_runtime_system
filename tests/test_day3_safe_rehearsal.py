from scripts.run_day3_safe_rehearsal import SAFE_REHEARSAL_COMMANDS, command_is_safe


def test_day3_rehearsal_commands_are_dry_run_or_read_only() -> None:
    assert SAFE_REHEARSAL_COMMANDS
    for command in SAFE_REHEARSAL_COMMANDS:
        assert command_is_safe(command), command


def test_day3_rehearsal_includes_core_hardening_checks() -> None:
    joined = [" ".join(command) for command in SAFE_REHEARSAL_COMMANDS]
    assert any("check_chatgpt_return_loop.py" in command for command in joined)
    assert any("kanban_blocked_task_drain.py" in command for command in joined)
    assert any("sync_to_drive.py --mode public-template --dry-run" in command for command in joined)
    assert any("sync_to_drive.py --mode private-runtime --dry-run" in command for command in joined)
    assert any("run_full_safe_regression.py --include-pytest" in command for command in joined)
