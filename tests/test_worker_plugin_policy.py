from __future__ import annotations

from pathlib import Path

from scripts.import_external_worker_skills import load_items, read_yaml


POLICY = Path("config/worker_plugin_policy.yaml")
EXPECTED = {
    "teos-orchestrator",
    "gov-tender-intelligence",
    "export-buyer-intelligence",
    "supplier-commercial",
    "pricing-risk",
    "compliance-due-diligence",
    "relationship-ops",
    "learning-evaluation",
}
LEGACY = {
    "hermes-chief-operator",
    "gov-tender-radar",
    "export-rfq-radar",
    "supplier-sourcing",
    "pricing-compliance",
    "sales-followup",
    "learning-review",
    "source-health",
    "codex-artifact-factory",
    "chatgpt-boardroom-handoff",
}


def test_worker_plugin_policy_targets_only_real_specialist_profiles() -> None:
    policy = read_yaml(POLICY)

    assert set(policy["profile_imports"]) == EXPECTED
    assert not (set(policy["profile_imports"]) & LEGACY)
    assert policy["policy"]["teos_external_actions_allowed"] is False
    assert policy["policy"]["hermes_native_plugins_auto_enabled"] is False
    assert policy["policy"]["mcp_servers_auto_enabled"] is False


def test_pricing_and_compliance_imports_are_split() -> None:
    imports = read_yaml(POLICY)["profile_imports"]

    assert imports["pricing-risk"]["maps_runtime_agents"] == ["pricing_agent"]
    assert imports["compliance-due-diligence"]["maps_runtime_agents"] == ["compliance_agent"]
    assert "cost-optimization" in imports["pricing-risk"]["accio"]
    assert "claims" in imports["compliance-due-diligence"]["accio"]


def test_every_selected_skill_source_exists() -> None:
    policy = read_yaml(POLICY)
    items = load_items(policy)

    assert items
    assert {item.profile for item in items} == EXPECTED
    assert all((item.source_dir / "SKILL.md").is_file() for item in items)
