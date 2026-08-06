from pathlib import Path

from scripts.run_full_safe_regression import SAFE_COMMANDS


PUBLIC_MASTER_CASES_FIXTURE = Path("tests/fixtures/safe_regression/master_cases.csv")


def test_safe_regression_runner_contains_required_public_checks() -> None:
    joined = [" ".join(command) for command in SAFE_COMMANDS]
    assert any("check_no_private_runtime_data.py --public-template" in command for command in joined)
    assert any("system_health_check.py --public-template" in command for command in joined)
    assert any("validate_business_state_consistency.py --public-template" in command for command in joined)
    assert any("low_competition_order_radar.py --dry-run" in command for command in joined)
    assert any("retender_corrigenda_watch.py --dry-run" in command for command in joined)
    assert any("capture_historical_gov_intelligence.py --dry-run --json" in command for command in joined)
    assert any("gov_historical_intelligence.py --case-id GOV-20260630-001 --json" in command for command in joined)
    assert any("gov_supplier_532_gate.py --case-id GOV-20260630-001 --allow-blocked --json" in command for command in joined)
    assert PUBLIC_MASTER_CASES_FIXTURE.is_file()
    assert sum("--master-cases tests/fixtures/safe_regression/master_cases.csv" in command for command in joined) == 2
    assert any("buyer_repeat_purchase_analyzer.py --dry-run" in command for command in joined)
    assert any("supplier_ready_category_matcher.py --dry-run" in command for command in joined)
    assert any("stage_deep_research_leads.py --input tests/fixtures/deep_research_leads/good_leads.json --dry-run" in command for command in joined)
    assert any("check_chatgpt_return_loop.py" in command for command in joined)
    assert any("research_route.py --validate-configs" in command for command in joined)
    assert any("evaluate_browser_boundaries.py --validate-only" in command for command in joined)
    assert any("kanban_blocked_task_drain.py" in command for command in joined)
    assert any("setup_drive_folders.py --dry-run" in command for command in joined)
