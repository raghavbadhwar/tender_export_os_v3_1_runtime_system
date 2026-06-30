import json
import subprocess
import sys


def run_cmd(*args, check=True):
    result = subprocess.run(
        [sys.executable, *args],
        text=True,
        capture_output=True,
        check=check,
    )
    return result


def test_verify_buyer_demand_expected_stages():
    result = run_cmd("scripts/verify_buyer_demand.py", "--all", "--dry-run", "--json")
    rows = {row["case_id"]: row for row in json.loads(result.stdout)}

    assert rows["EXP-20260630-001"]["stage"] == "RAW_LEAD"
    assert rows["EXP-20260630-002"]["stage"] == "RAW_LEAD"
    assert rows["EXP-20260630-003"]["stage"] == "BUYER_VISIBLE"
    assert rows["EXP-20260630-004"]["stage"] == "BUYER_VISIBLE"
    assert rows["EXP-20260630-005"]["stage"] == "RFQ_VERIFIED"
    assert rows["EXP-20260630-006"]["stage"] == "RFQ_VERIFIED"


def test_research_buyer_horizon_includes_source_tiers():
    result = run_cmd("scripts/research_buyer_horizon.py", "--dry-run", "--json")
    rows = json.loads(result.stdout)
    tiers = {row["source_tier"] for row in rows}

    assert "TIER_1_INSTITUTIONAL" in tiers
    assert "TIER_2_SECTOR" in tiers
    assert "TIER_4_MARKETPLACE_RFQ" in tiers
    assert all(row["recommended_next_action"] for row in rows)


def test_case_readiness_blocks_weak_export_cases_after_discovery():
    result = run_cmd(
        "scripts/validate_case_readiness.py",
        "--case-id",
        "EXP-20260630-001",
        "--json",
        "--strict",
        check=False,
    )
    assert result.returncode == 1
    rows = json.loads(result.stdout)
    blockers = " ".join(rows[0]["blockers"])
    assert "RFQ_VERIFIED" in blockers
