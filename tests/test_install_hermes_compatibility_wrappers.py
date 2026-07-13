from __future__ import annotations

from pathlib import Path

from scripts.install_hermes_compatibility_wrappers import install_wrappers, render_wrapper


def test_render_wrapper_prints_target_and_expiring_deprecation_notice() -> None:
    text = render_wrapper("old-agent", "new-agent", "2026-08-11", "/opt/hermes")

    assert "DEPRECATED" in text
    assert "old-agent" in text
    assert "new-agent" in text
    assert "2026-08-11" in text
    assert 'exec /opt/hermes -p new-agent "$@"' in text
    assert text.count(" -p ") == 1


def test_install_wrappers_is_dry_run_by_default(tmp_path: Path) -> None:
    wrapper_dir = tmp_path / "bin"
    report = install_wrappers(
        {"old-agent": "new-agent"},
        wrapper_dir=wrapper_dir,
        profiles_root=tmp_path / "profiles",
        expires_on="2026-08-11",
        hermes_binary="/opt/hermes",
        apply=False,
        backup_dir=tmp_path / "backup",
    )

    assert report["mode"] == "dry_run"
    assert report["wrappers_mutated"] is False
    assert not wrapper_dir.exists()


def test_install_wrappers_apply_backs_up_and_targets_existing_profiles(tmp_path: Path) -> None:
    wrapper_dir = tmp_path / "bin"
    wrapper_dir.mkdir()
    old = wrapper_dir / "old-agent"
    old.write_text("original\n", encoding="utf-8")
    profiles_root = tmp_path / "profiles"
    (profiles_root / "new-agent").mkdir(parents=True)
    backup = tmp_path / "backup"

    report = install_wrappers(
        {"old-agent": "new-agent"},
        wrapper_dir=wrapper_dir,
        profiles_root=profiles_root,
        expires_on="2026-08-11",
        hermes_binary="/opt/hermes",
        apply=True,
        backup_dir=backup,
    )

    assert report["status"] == "PASS"
    assert report["wrappers_mutated"] is True
    assert (backup / "old-agent.before").read_text(encoding="utf-8") == "original\n"
    assert "new-agent" in old.read_text(encoding="utf-8")
    assert old.stat().st_mode & 0o111
