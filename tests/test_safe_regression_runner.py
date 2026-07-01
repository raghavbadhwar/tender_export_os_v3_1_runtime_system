from scripts.run_full_safe_regression import SAFE_COMMANDS


def test_safe_regression_runner_contains_required_public_checks() -> None:
    joined = [" ".join(command) for command in SAFE_COMMANDS]
    assert any("check_no_private_runtime_data.py --public-template" in command for command in joined)
    assert any("system_health_check.py --public-template" in command for command in joined)
    assert any("low_competition_order_radar.py --dry-run" in command for command in joined)
    assert any("retender_corrigenda_watch.py --dry-run" in command for command in joined)
    assert any("buyer_repeat_purchase_analyzer.py --dry-run" in command for command in joined)
    assert any("supplier_ready_category_matcher.py --dry-run" in command for command in joined)
    assert any("stage_deep_research_leads.py --input tests/fixtures/deep_research_leads/good_leads.json --dry-run" in command for command in joined)
    assert any("check_chatgpt_return_loop.py" in command for command in joined)
    assert any("kanban_blocked_task_drain.py" in command for command in joined)
    assert any("setup_drive_folders.py --dry-run" in command for command in joined)
