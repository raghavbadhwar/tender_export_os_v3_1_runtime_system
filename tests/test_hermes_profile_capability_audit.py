from pathlib import Path

from scripts.audit_hermes_profile_capabilities import capability_utilization_snapshot, evaluate_profile


def _manifest(tmp_path: Path) -> dict:
    return {
        "profile": "tender-export-os",
        "workspace": str(tmp_path / "repo"),
        "runtime": {"gateway_supervision_required": "launchd"},
        "reasoning_and_context": {"reasoning_effort": "high", "max_turns": 80, "verify_on_stop": True},
        "governed_learning": {"memory_write_approval": True, "skill_write_approval": True, "guard_agent_created_skills": True},
        "local_skills": {"bundle": "teos-ops", "members": ["teos-chief-operator"]},
        "local_capabilities": {
            "model_resilience": {
                "fallback_chain": [{"provider": "openai-codex", "model": "gpt-5.5"}]
            },
            "filesystem_checkpoints": {
                "enabled": True,
                "max_snapshots": 12,
                "max_total_size_mb": 300,
                "max_file_size_mb": 10,
                "auto_prune": True,
                "retention_days": 7,
                "delete_orphans": True,
                "min_interval_hours": 24,
            },
            "deterministic_security": {
                "website_blocklist_enabled": True,
                "website_blocklist_domains": ["mail.google.com", "gmail.com"],
                "terminal_deny_globs": ["gws *"],
            },
            "behavioral_evaluation": {
                "spec": str(tmp_path / "eval.yaml"),
                "runner": str(tmp_path / "eval.py"),
                "latest_report_glob": str(tmp_path / "eval-report.json"),
                "required_status": "PASS",
                "max_age_hours": 168,
            },
        },
        "gateway_hooks": [
            {
                "name": "teos-event-bridge",
                "evidence_event_type": "hermes.gateway_started",
                "evidence_event_source": "hermes_gateway_hook",
                "evidence_event_file": str(tmp_path / "events.jsonl"),
            }
        ],
        "scheduled_jobs": [{"name": "Morning Brief"}],
    }


def test_capability_audit_passes_complete_profile(tmp_path: Path) -> None:
    profile_home = tmp_path / "profile"
    (profile_home / "skills" / "teos-chief-operator").mkdir(parents=True)
    (profile_home / "skills" / "teos-chief-operator" / "SKILL.md").write_text("ok", encoding="utf-8")
    (profile_home / "skill-bundles").mkdir()
    (profile_home / "skill-bundles" / "teos-ops.yaml").write_text("skills: []", encoding="utf-8")
    (profile_home / "hooks" / "teos-event-bridge").mkdir(parents=True)
    (profile_home / "hooks" / "teos-event-bridge" / "HOOK.yaml").write_text("events: []", encoding="utf-8")
    (tmp_path / "eval.yaml").write_text("version: 1\n", encoding="utf-8")
    (tmp_path / "eval.py").write_text("pass\n", encoding="utf-8")
    (tmp_path / "eval-report.json").write_text('{"status":"PASS"}\n', encoding="utf-8")
    (tmp_path / "events.jsonl").write_text(
        '{"event_type":"hermes.gateway_started","source":"hermes_gateway_hook"}\n',
        encoding="utf-8",
    )
    config = {
        "terminal": {"cwd": str(tmp_path / "repo")},
        "memory": {"write_approval": True},
        "skills": {"write_approval": True, "guard_agent_created": True},
        "agent": {"reasoning_effort": "high", "max_turns": 80, "verify_on_stop": True},
        "checkpoints": {
            "enabled": True,
            "max_snapshots": 12,
            "max_total_size_mb": 300,
            "max_file_size_mb": 10,
            "auto_prune": True,
            "retention_days": 7,
            "delete_orphans": True,
            "min_interval_hours": 24,
        },
        "fallback_providers": [{"provider": "openai-codex", "model": "gpt-5.5"}],
        "security": {
            "website_blocklist": {
                "enabled": True,
                "domains": ["mail.google.com", "gmail.com"],
            }
        },
        "approvals": {"deny": ["gws *"]},
    }

    report = evaluate_profile(
        _manifest(tmp_path),
        config,
        profile_home,
        cron_output="Name: Morning Brief",
        gateway_output="Gateway is supervised by launchd",
    )

    assert report["status"] == "PASS"
    assert report["findings"] == []


def test_capability_audit_blocks_on_config_and_schedule_drift(tmp_path: Path) -> None:
    report = evaluate_profile(
        _manifest(tmp_path),
        {"terminal": {"cwd": "/wrong"}},
        tmp_path / "missing-profile",
        cron_output="No scheduled jobs",
        gateway_output="detached fallback process",
    )

    assert report["status"] == "BLOCKED"
    codes = {item["code"] for item in report["findings"]}
    assert "CONFIG_DRIFT" in codes
    assert "SCHEDULE_MISSING" in codes
    assert "GATEWAY_NOT_SUPERVISED" in codes
    assert "FALLBACK_MISSING" in codes
    assert "CHECKPOINT_CONFIG_DRIFT" in codes or "CONFIG_DRIFT" in codes
    assert "WEBSITE_BLOCKLIST_DRIFT" in codes
    assert "APPROVAL_DENY_MISSING" in codes
    assert "BEHAVIORAL_EVAL_SPEC_MISSING" in codes
    assert "BEHAVIORAL_EVAL_REPORT_MISSING" in codes
    assert "HOOK_EVIDENCE_MISSING" in codes


def test_capability_utilization_distinguishes_configured_and_used(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    events.write_text(
        "{\"event_type\":\"hermes.agent_started\"}\n"
        "{\"event_type\":\"hermes.gateway_started\"}\n"
        "{\"event_type\":\"memory.proposal_staged\"}\n",
        encoding="utf-8",
    )
    manifest = _manifest(tmp_path)
    manifest["scheduled_jobs"] = [{"name": "Morning Brief"}, {"name": "Evening Close"}]
    manifest["specialist_profiles"] = ["worker-one", "worker-two"]
    manifest["local_capabilities"] = {
        "governed_mcp": {"tools": ["get_case", "search_cases"]},
        "filesystem_checkpoints": {"enabled": True},
    }
    snapshot = capability_utilization_snapshot(
        manifest,
        {},
        cron_output="Name: Morning Brief\n",
        insights_output="Sessions:          4            Messages:        12\nTool calls:        9\nLoads:              2\n mcp__tender_os__get_case       3\n kanban_show                         1\n",
        kanban_output='{"by_status":{"done":2}}',
        events_file=events,
    )

    capabilities = snapshot["capabilities"]
    assert capabilities["scheduler"]["status"] == "CONFIGURED_PARTIAL_EVIDENCE"
    assert capabilities["mcp"]["status"] == "CONFIGURED_AND_USED"
    assert capabilities["kanban"]["status"] == "USED"
    assert capabilities["skills_and_memory"]["memory_events"] == 1
    assert capabilities["optional_authority"]["status"] == "INTENTIONALLY_GATED"


def test_evaluate_profile_embeds_utilization_snapshot(tmp_path: Path) -> None:
    report = evaluate_profile(
        _manifest(tmp_path),
        {},
        tmp_path / "profile",
        cron_output="",
        gateway_output="",
        insights_output="Sessions: 1\nTool calls: 2\n",
        kanban_output='{"by_status":{"blocked":1}}',
        events_file=tmp_path / "missing-events.jsonl",
    )

    assert report["capability_utilization"]["schema_version"] == "hermes_capability_utilization.v1"
    assert report["capability_utilization"]["capabilities"]["session_runtime"]["sessions_in_insights_window"] == 1
