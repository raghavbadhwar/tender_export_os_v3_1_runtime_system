from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.provision_hermes_specialist_profiles import (
    build_create_commands,
    install_role_skills,
    provision,
    write_profile_overlay,
)


def registry_fixture() -> dict:
    return {
        "owner_profile": "tender-export-os",
        "specialist_profiles": ["worker-one"],
        "profiles": {
            "tender-export-os": {
                "provision": "existing",
                "description": "Owner profile.",
                "skill_bundle": ["owner-skill"],
            },
            "worker-one": {
                "provision": "create",
                "description": "Isolated worker profile.",
                "skill_bundle": ["worker-skill"],
            },
        },
    }


def test_provision_script_is_directly_executable() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/provision_hermes_specialist_profiles.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "--apply" in completed.stdout


def test_build_create_commands_only_targets_missing_create_profiles(tmp_path: Path) -> None:
    profiles_root = tmp_path / "profiles"
    (profiles_root / "tender-export-os").mkdir(parents=True)

    commands = build_create_commands(registry_fixture(), profiles_root)

    assert commands == [
        [
            "hermes",
            "profile",
            "create",
            "worker-one",
            "--no-skills",
            "--description",
            "Isolated worker profile.",
        ]
    ]
    assert all("--clone" not in part and "--clone-all" not in part for command in commands for part in command)


def test_write_profile_overlay_deep_merges_without_secret_material(tmp_path: Path) -> None:
    profile_dir = tmp_path / "worker-one"
    profile_dir.mkdir()
    (profile_dir / "config.yaml").write_text(
        yaml.safe_dump({"agent": {"verbose": False}, "display": {"compact": True}}),
        encoding="utf-8",
    )
    overlay = tmp_path / "worker-one.yaml"
    overlay.write_text(
        yaml.safe_dump(
            {
                "model": {"default": "gpt-test", "provider": "openai-codex"},
                "agent": {"max_turns": 9},
                "platform_toolsets": {"cli": ["file", "todo"]},
            }
        ),
        encoding="utf-8",
    )

    result = write_profile_overlay(profile_dir, overlay)
    stored = yaml.safe_load((profile_dir / "config.yaml").read_text(encoding="utf-8"))

    assert result["written"] is True
    assert stored["agent"] == {"verbose": False, "max_turns": 9}
    assert stored["display"] == {"compact": True}
    assert stored["model"]["provider"] == "openai-codex"
    assert not (profile_dir / "auth.json").exists()
    assert not (profile_dir / "memories" / "MEMORY.md").exists()


def test_write_profile_overlay_rejects_secret_or_runtime_state_keys(tmp_path: Path) -> None:
    profile_dir = tmp_path / "worker-one"
    profile_dir.mkdir()
    overlay = tmp_path / "unsafe.yaml"
    overlay.write_text(yaml.safe_dump({"auth.json": {"token": "secret"}}), encoding="utf-8")

    with pytest.raises(ValueError, match="forbidden"):
        write_profile_overlay(profile_dir, overlay)


def test_install_role_skills_copies_only_registered_skill_directories(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    for name in ("worker-skill", "unlisted-skill"):
        skill = source / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    (source / "auth.json").write_text("secret", encoding="utf-8")
    (source / "memories").mkdir()
    (source / "memories" / "MEMORY.md").write_text("private", encoding="utf-8")
    target.mkdir()

    result = install_role_skills(source, target, ["worker-skill"])

    assert result["installed"] == ["worker-skill"]
    assert (target / "skills" / "worker-skill" / "SKILL.md").exists()
    assert not (target / "skills" / "unlisted-skill").exists()
    assert not (target / "auth.json").exists()
    assert not (target / "memories").exists()


def test_provision_dry_run_creates_no_profiles_and_records_no_secrets(tmp_path: Path) -> None:
    profiles_root = tmp_path / "profiles"
    owner = profiles_root / "tender-export-os"
    (owner / "skills" / "owner-skill").mkdir(parents=True)
    (owner / "skills" / "worker-skill").mkdir(parents=True)
    (owner / "skills" / "worker-skill" / "SKILL.md").write_text("# worker\n", encoding="utf-8")
    overlays = tmp_path / "overlays"
    overlays.mkdir()
    (overlays / "worker-one.yaml").write_text(
        yaml.safe_dump({"model": {"default": "gpt-test", "provider": "openai-codex"}}),
        encoding="utf-8",
    )

    report = provision(
        registry_fixture(),
        profiles_root=profiles_root,
        overlays_root=overlays,
        source_profile_dir=owner,
        apply=False,
    )

    assert report["mode"] == "dry_run"
    assert report["status"] == "DRY_RUN"
    assert not (profiles_root / "worker-one").exists()
    assert report["credentials_copied"] is False
    assert report["memory_copied"] is False
    assert "secret" not in json.dumps(report).lower()


def test_provision_apply_stops_with_auth_required_without_copying_auth(tmp_path: Path) -> None:
    profiles_root = tmp_path / "profiles"
    owner = profiles_root / "tender-export-os"
    skill = owner / "skills" / "worker-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# worker\n", encoding="utf-8")
    (owner / "auth.json").write_text("must-not-copy", encoding="utf-8")
    overlays = tmp_path / "overlays"
    overlays.mkdir()
    (overlays / "worker-one.yaml").write_text(
        yaml.safe_dump({"model": {"default": "gpt-test", "provider": "openai-codex"}}),
        encoding="utf-8",
    )

    def fake_runner(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        if command[:3] == ["hermes", "profile", "create"]:
            profile = profiles_root / command[3]
            profile.mkdir(parents=True)
            (profile / "config.yaml").write_text("{}\n", encoding="utf-8")
            (profile / ".env").write_text("# empty\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "created", "")
        if command[-3:] == ["auth", "status", "openai-codex"]:
            return subprocess.CompletedProcess(command, 1, "not logged in", "")
        if command[-2:] == ["config", "check"]:
            return subprocess.CompletedProcess(command, 0, "ok", "")
        raise AssertionError(command)

    report = provision(
        registry_fixture(),
        profiles_root=profiles_root,
        overlays_root=overlays,
        source_profile_dir=owner,
        apply=True,
        runner=fake_runner,
    )

    worker = profiles_root / "worker-one"
    assert report["status"] == "AUTH_REQUIRED"
    assert report["profiles"][0]["auth_status"] == "AUTH_REQUIRED"
    assert (worker / "skills" / "worker-skill" / "SKILL.md").exists()
    assert not (worker / "auth.json").exists()
    assert not (worker / "memories" / "MEMORY.md").exists()
    assert (worker / ".env").read_text(encoding="utf-8") == "# empty\n"
