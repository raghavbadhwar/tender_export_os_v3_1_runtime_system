from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from scripts.validate_specialist_profiles import validate_profiles


WORKSPACE = "/workspace/tender-os"


def registry_fixture() -> dict:
    base = {
        "title": "Worker",
        "description": "Role-specific worker.",
        "identity": "Worker identity.",
        "provision": "create",
        "allowed_toolsets": ["file", "todo"],
        "mcp_tools": ["get_case"],
        "forbidden_toolsets": ["web", "browser", "terminal"],
        "skill_bundle": ["teos-evidence-verifier"],
    }
    return {
        "workspace": WORKSPACE,
        "owner_profile": "owner",
        "specialist_profiles": ["worker-one", "worker-two"],
        "profiles": {
            "worker-one": base | {"title": "Worker One", "description": "First role-specific worker."},
            "worker-two": base | {"title": "Worker Two", "description": "Second role-specific worker."},
        },
    }


def seed_profile(root: Path, name: str, description: str, soul: str) -> Path:
    profile = root / name
    (profile / "skills" / "teos-evidence-verifier").mkdir(parents=True)
    (profile / "skills" / "teos-evidence-verifier" / "SKILL.md").write_text("# evidence\n", encoding="utf-8")
    (profile / "cron").mkdir()
    (profile / "memories").mkdir()
    (profile / "profile.yaml").write_text(
        yaml.safe_dump({"description": description, "description_auto": False}),
        encoding="utf-8",
    )
    (profile / "SOUL.md").write_text(soul, encoding="utf-8")
    (profile / ".env").write_text("# empty profile env\n", encoding="utf-8")
    (profile / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "mcp_discovery_timeout": 20,
                "terminal": {"cwd": WORKSPACE},
                "kanban": {"dispatch_in_gateway": False},
                "platform_toolsets": {"cli": ["file", "todo"]},
                "mcp_servers": {"tender_os": {"tools": {"include": ["get_case"]}}},
            }
        ),
        encoding="utf-8",
    )
    return profile


def auth_runner(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
    if command[-3:] == ["auth", "status", "openai-codex"]:
        return subprocess.CompletedProcess(command, 0, "logged in", "")
    if command[:3] == ["hermes", "profile", "show"]:
        return subprocess.CompletedProcess(command, 0, "Gateway: stopped", "")
    raise AssertionError(command)


def test_validate_profiles_passes_exact_isolated_profiles(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    seed_profile(root, "worker-one", "First role-specific worker.", "# worker-one unique soul\n")
    seed_profile(root, "worker-two", "Second role-specific worker.", "# worker-two unique soul\n")

    report = validate_profiles(registry_fixture(), profiles_root=root, runner=auth_runner)

    assert report["status"] == "PASS"
    assert report["failed_checks"] == 0
    assert report["duplicate_soul_hashes"] == []
    assert all(row["auth_status"] == "PASS" for row in report["profiles"])
    assert all(row["forbidden_tools_present"] == [] for row in report["profiles"])


def test_validate_profiles_detects_authority_state_and_isolation_failures(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    first = seed_profile(root, "worker-one", "Same description.", "duplicate soul\n")
    second = seed_profile(root, "worker-two", "Same description.", "duplicate soul\n")
    config = yaml.safe_load((first / "config.yaml").read_text(encoding="utf-8"))
    config["platform_toolsets"]["cli"].append("web")
    (first / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    (first / "cron" / "jobs.json").write_text("{}", encoding="utf-8")
    (second / "gateway.pid").write_text("123", encoding="utf-8")

    report = validate_profiles(registry_fixture(), profiles_root=root, runner=auth_runner)

    assert report["status"] == "FAIL"
    assert report["duplicate_soul_hashes"]
    assert report["duplicate_descriptions"]
    by_name = {row["profile"]: row for row in report["profiles"]}
    assert "web" in by_name["worker-one"]["forbidden_tools_present"]
    assert by_name["worker-one"]["profile_local_cron"] is True
    assert by_name["worker-two"]["separate_gateway"] is True


def test_validate_profiles_rejects_copied_owner_auth_and_memory(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    owner = root / "owner"
    (owner / "memories").mkdir(parents=True)
    (owner / "auth.json").write_text("same-auth", encoding="utf-8")
    (owner / "memories" / "MEMORY.md").write_text("same-memory", encoding="utf-8")
    for name, description in (
        ("worker-one", "First role-specific worker."),
        ("worker-two", "Second role-specific worker."),
    ):
        profile = seed_profile(root, name, description, f"# {name}\n")
        (profile / "auth.json").write_text("same-auth", encoding="utf-8")
        (profile / "memories" / "MEMORY.md").write_text("same-memory", encoding="utf-8")

    report = validate_profiles(registry_fixture(), profiles_root=root, runner=auth_runner)

    assert report["status"] == "FAIL"
    assert all(row["copied_auth_material"] for row in report["profiles"])
    assert all(row["copied_memory_material"] for row in report["profiles"])
