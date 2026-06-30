from scripts.run_full_safe_regression import SAFE_COMMANDS


def test_safe_regression_runner_contains_required_public_checks() -> None:
    joined = [" ".join(command) for command in SAFE_COMMANDS]
    assert any("check_no_private_runtime_data.py --public-template" in command for command in joined)
    assert any("system_health_check.py --public-template" in command for command in joined)
    assert any("setup_drive_folders.py --dry-run" in command for command in joined)
