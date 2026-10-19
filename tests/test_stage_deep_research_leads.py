import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "stage_deep_research_leads.py"
FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "deep_research_leads"
MASTER_CASES = PROJECT_ROOT / "data" / "master_cases.csv"


def run_stage(input_name: str, output_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(FIXTURES / input_name),
            "--output-dir",
            str(output_dir),
            *args,
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def load_payload(output_dir: Path) -> dict:
    staged_files = sorted(output_dir.glob("**/staged_leads.json"))
    assert staged_files
    return json.loads(staged_files[-1].read_text(encoding="utf-8"))


def test_stage_script_defaults_to_dry_run(tmp_path: Path) -> None:
    result = run_stage("good_leads.json", tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = load_payload(tmp_path)
    assert payload["mode"] == "dry_run"
    assert payload["external_actions_executed"] is False
    assert payload["master_cases_mutated"] is False


def test_stage_script_does_not_mutate_master_cases_by_default(tmp_path: Path) -> None:
    before = MASTER_CASES.read_text(encoding="utf-8") if MASTER_CASES.exists() else ""
    result = run_stage("good_leads.json", tmp_path, "--dry-run")
    after = MASTER_CASES.read_text(encoding="utf-8") if MASTER_CASES.exists() else ""
    assert result.returncode == 0, result.stdout + result.stderr
    assert after == before


def test_stage_script_rejects_forbidden_actions(tmp_path: Path) -> None:
    result = run_stage("forbidden_action_leads.json", tmp_path, "--dry-run")
    assert result.returncode != 0
    assert "forbidden recommended_repo_action SEND_QUOTE" in result.stdout
    assert not list(tmp_path.glob("**/staged_leads.json"))


def test_public_listing_only_stays_lead_not_bid_ready(tmp_path: Path) -> None:
    result = run_stage("public_listing_only.json", tmp_path, "--dry-run")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = load_payload(tmp_path)
    lead = payload["leads"][0]
    assert lead["evidence_level"] == "PUBLIC_LISTING_ONLY"
    assert lead["recommended_repo_action"] == "MANUAL_SOURCE_CHECK"
    assert lead["case_candidate_allowed"] is False
    assert lead["operational_stage"] == "LEAD_STAGING"
