from __future__ import annotations

from pathlib import Path

from scripts.run_disaster_recovery_drill import export_profiles, isolated_restore_check, profile_names


def test_profile_names_include_owner_and_specialists_once() -> None:
    registry = {
        "owner_profile": "tender-export-os",
        "specialist_profiles": ["teos-orchestrator", "tender-export-os"],
    }

    assert profile_names(registry) == ["tender-export-os", "teos-orchestrator"]


def test_export_profiles_copies_recovery_files(tmp_path: Path) -> None:
    profiles_root = tmp_path / "profiles"
    profile_dir = profiles_root / "tender-export-os"
    profile_dir.mkdir(parents=True)
    for name in ("config.yaml", "profile.yaml", "SOUL.md", "state.db"):
        (profile_dir / name).write_text(name, encoding="utf-8")

    exported = export_profiles(["tender-export-os"], tmp_path / "exports", profiles_root=profiles_root)

    assert exported[0]["source_exists"] is True
    assert set(exported[0]["files"]) == {"config.yaml", "profile.yaml", "SOUL.md", "state.db"}
    assert (tmp_path / "exports/tender-export-os/state.db").read_text(encoding="utf-8") == "state.db"


def test_isolated_restore_check_requires_core_files(tmp_path: Path) -> None:
    source = tmp_path / "exports" / "tender-export-os"
    source.mkdir(parents=True)
    for name in ("config.yaml", "SOUL.md", "state.db"):
        (source / name).write_text(name, encoding="utf-8")

    result = isolated_restore_check("tender-export-os", tmp_path / "exports", tmp_path / "restore")

    assert result["ok"] is True
    assert result["missing"] == []
    assert Path(result["restore_path"]).is_dir()
