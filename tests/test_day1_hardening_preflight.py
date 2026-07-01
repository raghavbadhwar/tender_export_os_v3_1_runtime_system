import json
from pathlib import Path

from scripts.day1_hardening_preflight import build_cron_cleanup_plan, build_preflight, redact_cron_job


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def seed_project(project: Path) -> None:
    for relative in [
        "README.md",
        "AGENTS.md",
        "HERMES.md",
        "SOUL.md",
        "manifest.json",
        "docs/FINAL_ARCHITECTURE.md",
        "docs/CHATGPT_BOARDROOM.md",
        "docs/WEB_BROWSER_RESEARCH_ROUTING.md",
        "docs/V4_1_2_PHASEWISE_IMPLEMENTATION_PLAN.md",
        "docs/V4_1_2_OPERATIONAL_READINESS_REPORT.md",
        "config/hermes_cron.yaml",
        "config/portal_access_reality.yaml",
        "config/sources.gov.yaml",
        "config/sources.export.yaml",
        "config/sources.supplier.yaml",
        "config/plugin_routing.yaml",
        "config/agent_capability_routing.yaml",
        "data/master_cases.csv",
        "data/events.jsonl",
    ]:
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("sample\n", encoding="utf-8")


def seed_profile(profiles: Path, name: str, enabled: bool = True) -> None:
    profile = profiles / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "SOUL.md").write_text(f"# {name}\n", encoding="utf-8")
    write_json(
        profile / "cron" / "jobs.json",
        {
            "jobs": [
                {
                    "id": f"{name[:3]}-job",
                    "name": "daily-brief",
                    "prompt": "run daily brief without secrets",
                    "schedule_display": "0 9 * * *",
                    "enabled": enabled,
                    "workdir": "/tmp/project",
                    "token": "should-not-be-copied",
                }
            ]
        },
    )


def test_redacted_cron_job_removes_prompt_and_secret_fields() -> None:
    redacted = redact_cron_job({"id": "j1", "prompt": "hello", "api_key": "secret-value"})
    assert "prompt" not in redacted
    assert redacted["prompt_redacted"] is True
    assert redacted["prompt_sha256"]
    assert redacted["api_key"] == "[REDACTED]"


def test_cron_cleanup_plan_keeps_canonical_and_flags_specialist_duplicate() -> None:
    plan = build_cron_cleanup_plan(
        [
            {
                "profile": "tender-export-os",
                "enabled_count": 1,
                "jobs": [{"id": "a", "name": "daily-brief", "schedule_display": "0 9 * * *", "workdir": "/tmp/project", "enabled": True}],
            },
            {
                "profile": "gov-tender-radar",
                "enabled_count": 1,
                "jobs": [{"id": "b", "name": "daily-brief", "schedule_display": "0 9 * * *", "workdir": "/tmp/project", "enabled": True}],
            },
        ]
    )
    actions = {item["action"] for item in plan["recommended_actions"]}
    assert "KEEP_CANONICAL_ACTIVE" in actions
    assert "PAUSE_CANDIDATE_DRY_RUN_ONLY" in actions
    assert plan["cron_mutated"] is False


def test_build_preflight_writes_inventory_backups_and_dry_run_plan(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    profiles = tmp_path / "profiles"
    seed_project(project)
    seed_profile(profiles, "tender-export-os")
    seed_profile(profiles, "gov-tender-radar")

    inventory = build_preflight(project, profiles, project / "outputs" / "day1_hardening", skip_kanban_cli=True)

    inventory_path = project / inventory["inventory_path"]
    cron_plan_path = project / inventory["cron_cleanup_dry_run_plan_path"]
    assert inventory_path.exists()
    assert cron_plan_path.exists()
    assert inventory["safety"]["external_actions_executed"] is False
    assert inventory["safety"]["cron_mutated"] is False
    assert inventory["kanban_snapshot"]["skipped"] is True

    cron_plan = json.loads(cron_plan_path.read_text(encoding="utf-8"))
    assert cron_plan["mode"] == "dry_run_only"
    assert any(item["profile"] == "gov-tender-radar" for item in cron_plan["recommended_actions"])

    redacted_cron_backups = list((project / inventory["run_dir"] / "backups" / "profile_cron_redacted").glob("*.json"))
    assert redacted_cron_backups
    assert "should-not-be-copied" not in redacted_cron_backups[0].read_text(encoding="utf-8")
