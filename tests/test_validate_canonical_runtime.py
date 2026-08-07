from __future__ import annotations

import json
from pathlib import Path

import scripts.validate_canonical_runtime as validator


REMOTE = "git@github.com:example/tender-export-os.git"
BRANCH = "main"
COMMIT = "a" * 40


def _manifest(**overrides):
    value = {
        "schema_version": "canonical_runtime.v1",
        "mode": "public-template",
        "hermes_workdir": ".",
        "repository_remote": REMOTE,
        "branch": BRANCH,
        "commit": COMMIT,
        "public_template": True,
    }
    value.update(overrides)
    return value


def _fake_git(monkeypatch, root: Path, *, status: str = ""):
    values = {
        ("rev-parse", "--show-toplevel"): str(root),
        ("remote", "get-url", "origin"): REMOTE,
        ("symbolic-ref", "--quiet", "--short", "HEAD"): BRANCH,
        ("rev-parse", "HEAD"): COMMIT,
        ("status", "--porcelain=v1", "--ignored", "--untracked-files=all"): status,
    }

    def fake_run(_root, args):
        return values[tuple(args)]

    monkeypatch.setattr(validator, "_run_git", fake_run)


def test_matching_identity_passes_without_exposing_repository_path(monkeypatch, tmp_path):
    _fake_git(monkeypatch, tmp_path, status="!! outputs/runtime.json\n?? local-note.txt\n")

    report = validator.validate_canonical_runtime(
        _manifest(),
        repo_root=tmp_path,
        manifest_path=tmp_path / "config" / "canonical_runtime.json",
        public_template=True,
    )

    assert report["status"] == "PASS"
    assert report["errors"] == []
    assert report["tracked_source_dirty"] is False
    assert report["ignored_runtime_data"] == ["outputs/runtime.json"]
    assert report["untracked_count"] == 1
    assert "<repo>" in json.dumps(report)
    assert str(tmp_path) not in json.dumps(report)
    assert report["external_actions_executed"] is False
    assert report["mutation_performed"] is False


def test_commit_mismatch_fails_closed(monkeypatch, tmp_path):
    _fake_git(monkeypatch, tmp_path)

    report = validator.validate_canonical_runtime(
        _manifest(commit="b" * 40),
        repo_root=tmp_path,
        manifest_path=tmp_path / "canonical_runtime.json",
        public_template=True,
    )

    assert report["status"] == "FAIL"
    assert "COMMIT_MISMATCH" in report["errors"]


def test_dirty_tracked_source_fails_but_ignored_runtime_is_reported(monkeypatch, tmp_path):
    _fake_git(
        monkeypatch,
        tmp_path,
        status=" M scripts/changed.py\n!! outputs/run.json\n!! .venv/bin/python\n",
    )

    report = validator.validate_canonical_runtime(
        _manifest(),
        repo_root=tmp_path,
        manifest_path=tmp_path / "canonical_runtime.json",
        public_template=True,
    )

    assert report["status"] == "FAIL"
    assert "TRACKED_SOURCE_DIRTY" in report["errors"]
    assert report["tracked_changes"] == ["scripts/changed.py"]
    assert report["ignored_runtime_data"] == ["outputs/run.json"]
    assert report["ignored_other_count"] == 1


def test_public_template_rejects_private_workdir_and_redacts_it(monkeypatch, tmp_path):
    _fake_git(monkeypatch, tmp_path)
    private_workdir = str(tmp_path / "private-hermes-workdir")

    report = validator.validate_canonical_runtime(
        _manifest(hermes_workdir=private_workdir),
        repo_root=tmp_path,
        manifest_path=tmp_path / "canonical_runtime.json",
        public_template=True,
    )

    assert report["status"] == "FAIL"
    assert "PRIVATE_PATH_IN_PUBLIC_MANIFEST" in report["errors"]
    assert str(tmp_path) not in json.dumps(report)
    assert "<repo>/private-hermes-workdir" in json.dumps(report)


def test_public_template_mode_is_required(monkeypatch, tmp_path):
    _fake_git(monkeypatch, tmp_path)

    report = validator.validate_canonical_runtime(
        _manifest(mode="private-runtime", public_template=False),
        repo_root=tmp_path,
        manifest_path=tmp_path / "canonical_runtime.json",
        public_template=True,
    )

    assert report["status"] == "FAIL"
    assert "PUBLIC_TEMPLATE_MISMATCH" in report["errors"]
    assert "PUBLIC_TEMPLATE_MODE_MISMATCH" in report["errors"]
