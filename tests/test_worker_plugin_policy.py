from __future__ import annotations

from pathlib import Path

import pytest

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


def test_public_template_requires_explicit_runtime_skill_roots(monkeypatch: pytest.MonkeyPatch) -> None:
    policy = read_yaml(POLICY)

    assert policy["source_roots"] == {
        "accio": "${TEOS_ACCIO_SKILLS_ROOT}",
        "claude": "${TEOS_CLAUDE_SKILLS_ROOT}",
    }
    assert policy["profiles_root"] == "${TEOS_HERMES_PROFILES_ROOT}"
    for variable in ("TEOS_ACCIO_SKILLS_ROOT", "TEOS_CLAUDE_SKILLS_ROOT", "TEOS_HERMES_PROFILES_ROOT"):
        monkeypatch.delenv(variable, raising=False)

    with pytest.raises(ValueError, match="TEOS_ACCIO_SKILLS_ROOT"):
        load_items(policy)


def test_load_items_uses_explicit_runtime_skill_roots(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    policy = read_yaml(POLICY)
    accio_root = tmp_path / "accio"
    claude_root = tmp_path / "claude"
    profiles_root = tmp_path / "profiles"
    monkeypatch.setenv("TEOS_ACCIO_SKILLS_ROOT", str(accio_root))
    monkeypatch.setenv("TEOS_CLAUDE_SKILLS_ROOT", str(claude_root))
    monkeypatch.setenv("TEOS_HERMES_PROFILES_ROOT", str(profiles_root))

    items = load_items(policy)
    assert items
    assert {item.profile for item in items} == EXPECTED
    assert all(item.target_dir.is_relative_to(profiles_root) for item in items)
    assert all(
        item.source_dir.is_relative_to(accio_root if item.kind == "accio" else claude_root)
        for item in items
    )
