from pathlib import Path

from scripts.check_chatgpt_return_loop import build_chatgpt_return_loop_report


def test_chatgpt_return_loop_report_creates_required_folders_and_keeps_dry_run(tmp_path: Path) -> None:
    report = build_chatgpt_return_loop_report(tmp_path, fixture_return=Path("tests/fixtures/chatgpt_returns/good_return.md"))

    assert report["mode"] == "dry_run_only"
    assert report["external_actions_executed"] is False
    assert report["repo_registers_mutated"] is False
    assert report["required_folders_ok"] is True
    assert report["fixture_validation_ok"] is True
    assert report["staging_probe_ok"] is True
    for rel in ["outputs/chatgpt_bridge/to_chatgpt", "outputs/chatgpt_bridge/from_chatgpt", "outputs/chatgpt_bridge/reviewed"]:
        assert (tmp_path / rel).exists()
