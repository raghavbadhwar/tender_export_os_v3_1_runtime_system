import json
from pathlib import Path

import yaml

from scripts.apply_specialist_profile_souls import (
    PROFILE_SPECS,
    REGISTRY_PATH,
    apply_specialist_souls,
    load_profile_specs,
    render_soul,
)


EXPECTED_PROFILES = {
    "tender-export-os",
    "teos-orchestrator",
    "gov-tender-intelligence",
    "export-buyer-intelligence",
    "supplier-commercial",
    "pricing-risk",
    "compliance-due-diligence",
    "relationship-ops",
    "learning-evaluation",
}


def seed_profile(root: Path, name: str, body: str = "cloned") -> None:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "SOUL.md").write_text(body, encoding="utf-8")


def test_rendered_specialist_souls_are_unique_and_role_specific() -> None:
    rendered = {name: render_soul(name, spec) for name, spec in PROFILE_SPECS.items()}
    assert len(set(rendered.values())) == len(rendered)
    assert "public tender" in rendered["gov-tender-intelligence"].lower()
    assert "supplier 5-3-2" in rendered["supplier-commercial"].lower()
    assert "final price" in rendered["pricing-risk"].lower()
    assert "final legal" in rendered["compliance-due-diligence"].lower()


def test_profile_specs_are_loaded_from_canonical_registry() -> None:
    loaded = load_profile_specs(REGISTRY_PATH)

    assert set(loaded) == EXPECTED_PROFILES
    assert loaded == PROFILE_SPECS
    assert all(profile["description"] for profile in loaded.values())
    assert all(profile["allowed_toolsets"] for profile in loaded.values())
    assert all("mcp_tools" in profile for profile in loaded.values())
    assert all(profile["skill_bundle"] for profile in loaded.values())
    assert all(profile["memory_scope"] for profile in loaded.values())
    assert all(profile["max_turns"] > 0 for profile in loaded.values())
    assert all(profile["task_timeout_seconds"] > 0 for profile in loaded.values())
    assert all("max_delegates" in profile["delegate_limits"] for profile in loaded.values())
    assert all(profile["stop_conditions"] for profile in loaded.values())
    assert all(profile["output_contract"]["required_fields"] for profile in loaded.values())
    assert all(profile["evaluation_scenarios"] for profile in loaded.values())


def test_load_profile_specs_reads_the_supplied_registry_not_a_hardcoded_map(tmp_path: Path) -> None:
    registry = {
        "version": 1,
        "profiles": {
            "custom-worker": {
                "title": "Custom Worker",
                "description": "Custom test profile.",
                "identity": "A custom test worker.",
                "owns": ["fixture work"],
                "inputs": ["fixture"],
                "outputs": ["fixture result"],
                "never": ["external action"],
            }
        },
    }
    path = tmp_path / "profiles.yaml"
    path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    loaded = load_profile_specs(path)

    assert list(loaded) == ["custom-worker"]
    assert loaded["custom-worker"]["title"] == "Custom Worker"


def test_apply_specialist_souls_dry_run_does_not_mutate_profiles(tmp_path: Path) -> None:
    profiles_root = tmp_path / "profiles"
    for name in PROFILE_SPECS:
        seed_profile(profiles_root, name, "CLONED SOUL")

    report = apply_specialist_souls(profiles_root, tmp_path / "out", apply=False)

    assert report["mode"] == "dry_run"
    assert report["profiles_mutated"] is False
    assert all((profiles_root / name / "SOUL.md").read_text(encoding="utf-8") == "CLONED SOUL" for name in PROFILE_SPECS)
    assert all(item["would_change"] for item in report["profiles"])


def test_apply_specialist_souls_apply_writes_unique_prompts_and_backups(tmp_path: Path) -> None:
    profiles_root = tmp_path / "profiles"
    for name in PROFILE_SPECS:
        seed_profile(profiles_root, name, "CLONED SOUL")

    report = apply_specialist_souls(profiles_root, tmp_path / "out", apply=True)

    assert report["mode"] == "apply"
    assert report["profiles_mutated"] is True
    bodies = [(profiles_root / name / "SOUL.md").read_text(encoding="utf-8") for name in PROFILE_SPECS]
    assert len(set(bodies)) == len(bodies)
    assert report["unique_new_hash_count"] == len(PROFILE_SPECS)
    for item in report["profiles"]:
        assert item["backup_path"]
        assert Path(item["backup_path"]).exists()
        assert item["canary_pass"] is True


def test_apply_specialist_souls_can_limit_live_mutation_to_new_workers(tmp_path: Path) -> None:
    profiles_root = tmp_path / "profiles"
    for name in PROFILE_SPECS:
        seed_profile(profiles_root, name, "ORIGINAL SOUL")

    report = apply_specialist_souls(
        profiles_root,
        tmp_path / "out",
        apply=True,
        selected_profiles={"teos-orchestrator", "pricing-risk"},
    )

    assert report["profile_count"] == 2
    assert {item["profile"] for item in report["profiles"]} == {"teos-orchestrator", "pricing-risk"}
    assert (profiles_root / "tender-export-os" / "SOUL.md").read_text(encoding="utf-8") == "ORIGINAL SOUL"
    assert (profiles_root / "teos-orchestrator" / "SOUL.md").read_text(encoding="utf-8") != "ORIGINAL SOUL"
