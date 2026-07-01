import json
from pathlib import Path

from scripts.apply_specialist_profile_souls import PROFILE_SPECS, apply_specialist_souls, render_soul


def seed_profile(root: Path, name: str, body: str = "cloned") -> None:
    profile = root / name
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "SOUL.md").write_text(body, encoding="utf-8")


def test_rendered_specialist_souls_are_unique_and_role_specific() -> None:
    rendered = {name: render_soul(name, spec) for name, spec in PROFILE_SPECS.items()}
    assert len(set(rendered.values())) == len(rendered)
    assert "public tender discovery" in rendered["gov-tender-radar"].lower()
    assert "supplier 5-3-2" in rendered["supplier-sourcing"].lower()
    assert "final price" in rendered["pricing-compliance"].lower()
    assert "never" in rendered["codex-artifact-factory"].lower()


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
