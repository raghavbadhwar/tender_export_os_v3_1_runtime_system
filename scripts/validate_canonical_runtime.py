#!/usr/bin/env python3
"""Validate the repository's canonical, read-only runtime identity.

The manifest is intentionally small and checked against live local Git metadata.  This
command never writes files, changes Git state, contacts a remote, or enables runtime
routing.  ``--public-template`` additionally requires a sanitized manifest and redacts
local filesystem details from its JSON output.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "config" / "canonical_runtime.json"
SCHEMA_VERSION = "canonical_runtime.v1"
VALIDATION_SCHEMA_VERSION = "canonical_runtime_validation.v1"
_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_RUNTIME_TOP_LEVELS = {".local", ".pytest_cache", "data", "outputs", "receipts"}
_REQUIRED_FIELDS = (
    "schema_version",
    "hermes_workdir",
    "repository_remote",
    "branch",
    "commit",
    "public_template",
    "mode",
)


class GitCommandError(RuntimeError):
    """Raised only when a read-only Git query cannot be completed."""

    def __init__(self, args: Sequence[str], detail: str = "") -> None:
        self.args = tuple(args)
        self.detail = detail
        super().__init__(detail or "git command failed")


def _run_git(repo_root: Path, args: Sequence[str]) -> str:
    """Run one read-only Git query and return stdout.

    Keeping this in one function makes the no-mutation boundary explicit and allows
    deterministic tests to replace the query layer without touching the filesystem.
    """

    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise GitCommandError(args, completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip()


def _is_absolute(value: object) -> bool:
    if not isinstance(value, str):
        return False
    # PureWindowsPath catches drive-letter paths even when this runs on POSIX.
    text = value.strip()
    return (
        Path(text).is_absolute()
        or PurePosixPath(text).is_absolute()
        or PureWindowsPath(text).is_absolute()
        or text.startswith(("file://", "file:"))
    )


def _relative_path(value: str) -> str:
    """Return a stable relative display value for Git status output."""

    value = value.strip()
    if " -> " in value:  # rename/copy status: keep both relative names
        return " -> ".join(_relative_path(part) for part in value.split(" -> "))
    value = value.removeprefix('"').removesuffix('"')
    return value.replace("\\", "/")


def _runtime_path(value: str) -> bool:
    normalized = _relative_path(value)
    while normalized.startswith("./"):
        normalized = normalized[2:]
    first = normalized.split("/", 1)[0]
    return first in _RUNTIME_TOP_LEVELS


def _parse_status(output: str) -> dict[str, list[str]]:
    tracked: list[str] = []
    ignored_runtime: list[str] = []
    ignored_other: list[str] = []
    untracked: list[str] = []
    for line in output.splitlines():
        if not line:
            continue
        status = line[:2]
        value = _relative_path(line[3:] if len(line) > 3 else "")
        if status == "!!":
            (ignored_runtime if _runtime_path(value) else ignored_other).append(value)
        elif status == "??":
            untracked.append(value)
        elif status.strip():
            tracked.append(value)
    return {
        "tracked": sorted(set(item for item in tracked if item)),
        "ignored_runtime": sorted(set(item for item in ignored_runtime if item)),
        "ignored_other": sorted(set(item for item in ignored_other if item)),
        "untracked": sorted(set(item for item in untracked if item)),
    }


def _load_manifest(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.is_file():
        return None, ["MANIFEST_MISSING"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, ["MANIFEST_INVALID"]
    if not isinstance(value, dict):
        return None, ["MANIFEST_INVALID"]
    return value, []


def _validate_manifest_shape(manifest: Mapping[str, Any], *, public_template: bool) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("SCHEMA_VERSION_MISMATCH")
    for field in _REQUIRED_FIELDS:
        if field not in manifest:
            errors.append(f"MANIFEST_FIELD_MISSING:{field}")
    workdir = manifest.get("hermes_workdir")
    if not isinstance(workdir, str) or not workdir.strip():
        errors.append("HERMES_WORKDIR_INVALID")
    elif public_template and _is_absolute(workdir):
        errors.append("PRIVATE_PATH_IN_PUBLIC_MANIFEST")
    remote = manifest.get("repository_remote")
    if not isinstance(remote, str) or not remote.strip():
        errors.append("REPOSITORY_REMOTE_INVALID")
    elif public_template and _is_absolute(remote):
        errors.append("PRIVATE_PATH_IN_PUBLIC_MANIFEST")
    branch = manifest.get("branch")
    if not isinstance(branch, str) or not branch.strip():
        errors.append("BRANCH_INVALID")
    commit = manifest.get("commit")
    if not isinstance(commit, str) or not _COMMIT_RE.fullmatch(commit.strip()):
        errors.append("COMMIT_INVALID")
    if not isinstance(manifest.get("public_template"), bool):
        errors.append("PUBLIC_TEMPLATE_INVALID")
    elif public_template and manifest.get("public_template") is not True:
        errors.append("PUBLIC_TEMPLATE_MISMATCH")
    mode = manifest.get("mode")
    if not isinstance(mode, str) or not mode.strip():
        errors.append("MODE_INVALID")
    elif isinstance(manifest.get("public_template"), bool):
        coherent = (mode == "public-template") == manifest.get("public_template")
        if not coherent:
            errors.append("MANIFEST_MODE_INCOHERENT")
    if public_template and mode != "public-template":
        errors.append("PUBLIC_TEMPLATE_MODE_MISMATCH")
    return errors


def _identity(repo_root: Path) -> tuple[dict[str, str], dict[str, list[str]], list[str]]:
    """Read Git identity and status, returning values, status buckets, and errors."""

    identity: dict[str, str] = {}
    status = {"tracked": [], "ignored_runtime": [], "ignored_other": [], "untracked": []}
    errors: list[str] = []
    queries: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("repository_root", ("rev-parse", "--show-toplevel")),
        ("repository_remote", ("remote", "get-url", "origin")),
        ("branch", ("symbolic-ref", "--quiet", "--short", "HEAD")),
        ("commit", ("rev-parse", "HEAD")),
    )
    for field, args in queries:
        try:
            value = _run_git(repo_root, args)
        except GitCommandError:
            errors.append({
                "repository_root": "REPOSITORY_MISSING",
                "repository_remote": "REPOSITORY_REMOTE_MISSING",
                "branch": "BRANCH_MISSING_OR_DETACHED",
                "commit": "COMMIT_MISSING",
            }[field])
            continue
        if value:
            identity[field] = value
        else:
            errors.append({
                "repository_root": "REPOSITORY_MISSING",
                "repository_remote": "REPOSITORY_REMOTE_MISSING",
                "branch": "BRANCH_MISSING_OR_DETACHED",
                "commit": "COMMIT_MISSING",
            }[field])
    try:
        status_output = _run_git(repo_root, ("status", "--porcelain=v1", "--ignored", "--untracked-files=all"))
        status = _parse_status(status_output)
    except GitCommandError:
        errors.append("GIT_STATUS_UNAVAILABLE")
    return identity, status, errors


def _safe_display(value: object, *, repo_root: Path, manifest_path: Path | None = None) -> object:
    """Redact local absolute paths before they can reach public JSON output."""

    if not isinstance(value, str):
        return value
    text = value
    root = str(repo_root.resolve())
    if text == root or text.startswith(root + os.sep):
        return "<repo>" + text[len(root):].replace(os.sep, "/")
    home = str(Path.home())
    if text == home or text.startswith(home + os.sep):
        return "<home>" + text[len(home):].replace(os.sep, "/")
    if _is_absolute(text):
        return "<redacted-absolute-path>"
    # A Git error or remote can contain an absolute path embedded in a larger value.
    if root in text:
        return text.replace(root, "<repo>")
    if home in text:
        return text.replace(home, "<home>")
    return text


def _safe_map(value: Any, *, repo_root: Path, manifest_path: Path | None = None) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _safe_map(v, repo_root=repo_root, manifest_path=manifest_path) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_map(v, repo_root=repo_root, manifest_path=manifest_path) for v in value]
    return _safe_display(value, repo_root=repo_root, manifest_path=manifest_path)


def validate_canonical_runtime(
    manifest: Mapping[str, Any] | None = None,
    *,
    repo_root: Path = PROJECT_ROOT,
    public_template: bool = False,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    """Return a machine-readable validation report without mutating local state."""

    root = Path(repo_root).expanduser().resolve()
    path = Path(manifest_path).expanduser()
    errors: list[str] = []
    if manifest is None:
        loaded, load_errors = _load_manifest(path)
        manifest = loaded
        errors.extend(load_errors)
    if manifest is None:
        manifest = {}
    if not isinstance(manifest, Mapping):
        manifest = {}
        errors.append("MANIFEST_INVALID")
    errors.extend(_validate_manifest_shape(manifest, public_template=public_template))

    identity, status, identity_errors = _identity(root)
    errors.extend(identity_errors)

    expected_workdir = manifest.get("hermes_workdir")
    actual_root = identity.get("repository_root")
    if isinstance(expected_workdir, str) and expected_workdir.strip() and actual_root:
        configured = (root / expected_workdir).resolve()
        if configured != Path(actual_root).resolve():
            errors.append("HERMES_WORKDIR_MISMATCH")
    elif "HERMES_WORKDIR_INVALID" not in errors:
        errors.append("HERMES_WORKDIR_UNAVAILABLE")

    for field, mismatch_code in (
        ("repository_remote", "REMOTE_MISMATCH"),
        ("branch", "BRANCH_MISMATCH"),
        ("commit", "COMMIT_MISMATCH"),
    ):
        expected = manifest.get(field)
        observed = identity.get(field)
        if isinstance(expected, str) and expected.strip() and observed:
            if expected.strip() != observed.strip():
                errors.append(mismatch_code)
        elif f"{field.upper()}_INVALID" not in errors:
            errors.append(f"{mismatch_code}")

    if status["tracked"]:
        errors.append("TRACKED_SOURCE_DIRTY")

    # Duplicate findings from malformed/missing data are unhelpful and can make a
    # receipt unstable. Preserve first-seen order while de-duplicating codes.
    errors = list(dict.fromkeys(errors))
    clean_manifest = _safe_map(dict(manifest), repo_root=root, manifest_path=path)
    clean_identity = _safe_map(
        {
            "repository_root": "<repo>" if identity.get("repository_root") else None,
            "repository_remote": identity.get("repository_remote"),
            "branch": identity.get("branch"),
            "commit": identity.get("commit"),
        },
        repo_root=root,
        manifest_path=path,
    )
    report: dict[str, Any] = {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "status": "PASS" if not errors else "FAIL",
        "manifest": "config/canonical_runtime.json" if path == DEFAULT_MANIFEST else path.name,
        "mode": "public-template" if public_template else clean_manifest.get("mode", "canonical"),
        "expected": clean_manifest,
        "observed": clean_identity,
        "tracked_source_dirty": bool(status["tracked"]),
        "tracked_changes": status["tracked"],
        "ignored_runtime_data": status["ignored_runtime"],
        "ignored_other_count": len(status["ignored_other"]),
        "untracked_count": len(status["untracked"]),
        "errors": errors,
        "external_actions_executed": False,
        "mutation_performed": False,
    }
    return _safe_map(report, repo_root=root, manifest_path=path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--repo-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--public-template", action="store_true", help="Require sanitized public-template identity")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)
    report = validate_canonical_runtime(
        repo_root=args.repo_root,
        public_template=args.public_template,
        manifest_path=args.manifest,
    )
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Canonical runtime validation {report['status']}")
        if report["errors"]:
            print("Errors: " + ", ".join(report["errors"]))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
