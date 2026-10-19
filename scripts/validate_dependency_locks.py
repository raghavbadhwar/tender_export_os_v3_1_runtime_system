#!/usr/bin/env python3
"""Validate dependency-lock coverage without resolving or installing packages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_LOCK_PAIRS = (("requirements.txt", "requirements.lock.txt"), ("requirements-mcp.txt", "requirements-mcp.lock.txt"))
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")
EXACT_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;]+)")


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).casefold()


def parse_requirement_lines(text: str, *, lock: bool, source: str) -> tuple[dict[str, str], list[str], list[str]]:
    values: dict[str, str] = {}
    warnings: list[str] = []
    errors: list[str] = []
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        if line.startswith(("http://", "https://", "git+", "file:", "-e ")):
            errors.append(f"{source}:{line_number}: URL/editable requirement is not lock-covered")
            continue
        match = EXACT_RE.match(line)
        if match:
            name, version = match.groups()
            key = normalize_name(name)
            if key in values and values[key] != version:
                errors.append(f"{source}:{line_number}: conflicting duplicate for {name}")
            elif key in values:
                errors.append(f"{source}:{line_number}: duplicate requirement for {name}")
            values[key] = version
            continue
        name_match = NAME_RE.match(line)
        if not name_match:
            errors.append(f"{source}:{line_number}: unsupported requirement syntax")
            continue
        name = name_match.group(0)
        key = normalize_name(name)
        if lock:
            errors.append(f"{source}:{line_number}: lock entry for {name} is not exact-pinned")
        else:
            warnings.append(f"{source}:{line_number}: direct requirement {name} is not exact-pinned; lock coverage is required")
        if key in values:
            errors.append(f"{source}:{line_number}: duplicate requirement for {name}")
        values[key] = ""
    return values, warnings, errors


def validate_dependency_files(project_root: Path = PROJECT_ROOT, *, ci_text: str | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    coverage: list[dict[str, Any]] = []
    lock_maps: dict[str, dict[str, str]] = {}
    for source_name, lock_name in SOURCE_LOCK_PAIRS:
        source_path = project_root / source_name
        lock_path = project_root / lock_name
        if not source_path.is_file() or not lock_path.is_file():
            errors.append(f"missing requirement source or lock: {source_name}, {lock_name}")
            continue
        source_values, source_warnings, source_errors = parse_requirement_lines(source_path.read_text(encoding="utf-8"), lock=False, source=source_name)
        lock_values, lock_warnings, lock_errors = parse_requirement_lines(lock_path.read_text(encoding="utf-8"), lock=True, source=lock_name)
        warnings.extend(source_warnings); warnings.extend(lock_warnings); errors.extend(source_errors); errors.extend(lock_errors)
        missing = sorted(name for name in source_values if name not in lock_values)
        if missing:
            errors.append(f"{source_name}: direct requirements missing from {lock_name}: {', '.join(missing)}")
        for name, requested_version in source_values.items():
            locked_version = lock_values.get(name)
            if requested_version and locked_version and requested_version != locked_version:
                errors.append(f"{source_name}: exact requirement {name}=={requested_version} conflicts with {lock_name}=={locked_version}")
        lock_maps[lock_name] = lock_values
        coverage.append({"source": source_name, "lock": lock_name, "direct_count": len(source_values), "lock_count": len(lock_values), "missing": missing})
    workflow = ci_text if ci_text is not None else (project_root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    if "validate_dependency_locks.py --json" not in workflow:
        errors.append("CI does not run validate_dependency_locks.py --json")
    for _source_name, lock_name in SOURCE_LOCK_PAIRS:
        if f"-r {lock_name}" not in workflow:
            errors.append(f"CI does not install exact lock {lock_name}")
    if "-r requirements.txt" in workflow:
        errors.append("CI installs unpinned requirements.txt instead of its exact lock")
    return {"schema_version":"dependency_lock_validation.v1","status":"PASS" if not errors else "BLOCKED","errors":list(dict.fromkeys(errors)),"warnings":warnings,"coverage":coverage,"network_accessed":False,"installation_performed":False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try: report = validate_dependency_files()
    except (OSError, UnicodeError) as exc: report = {"schema_version":"dependency_lock_validation.v1","status":"BLOCKED","errors":[str(exc)],"warnings":[],"coverage":[],"network_accessed":False,"installation_performed":False}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
