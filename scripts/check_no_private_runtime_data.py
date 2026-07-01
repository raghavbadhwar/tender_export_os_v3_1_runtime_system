#!/usr/bin/env python3
"""Scan public-template files for private runtime data and secret-like values."""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = PROJECT_ROOT / "config" / "public_scan_allowlist.yaml"

PRIVATE_PATH_PATTERNS = [
    ".git/**",
    ".gitignore",
    ".local/**",
    ".pytest_cache/**",
    ".mypy_cache/**",
    ".ruff_cache/**",
    ".venv/**",
    "venv/**",
    "__pycache__/**",
    "CODEX_PLUGINS_REFERENCE.md",
    "outputs/**",
    "receipts/**",
    "data/*.csv",
    "data/*.jsonl",
    "data/*.xlsx",
    "data/*.bak",
    "data/*.test",
    "data/chatgpt_snapshot.md",
    "data/live/**",
    "cases/*/evidence/**",
    "artifacts/private/**",
]

PUBLIC_EXCEPTIONS = [
    "outputs/examples/**",
    "receipts/examples/**",
    "data/examples/**",
]

# Public-template scans should cover only the sanitized/public surface that can
# be shared as a template or manual. They must not walk the whole repository and
# then try to subtract private runtime paths, because new private folders such as
# cases/, .hermes/plans/, or ad-hoc audit outputs can otherwise leak into the
# public scan before an exclusion rule is added.
PUBLIC_TEMPLATE_INCLUDE_PATTERNS = [
    "AGENTS.md",
    "HERMES.md",
    "README.md",
    "SOUL.md",
    "docs/**/*.md",
    "config/*.yaml",
    "config/schemas/*.json",
    "config/schemas/*.yaml",
    "data/examples/**/*",
    "outputs/examples/**/*",
    "receipts/examples/**/*",
    "templates/**/*",
    "scripts/check_no_private_runtime_data.py",
    "scripts/system_health_check.py",
    "scripts/validate_register_schemas.py",
    "tests/fixtures/**/*",
]

TRACKED_PRIVATE_PATH_PATTERNS = [
    "data/**",
    "outputs/**",
    "receipts/**",
]

TRACKED_PUBLIC_EXCEPTIONS = [
    "data/examples/**",
    "outputs/examples/**",
    "receipts/examples/**",
]

TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".csv",
    ".html",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+91[-\s]?)?[6-9]\d{9}(?!\d)")
GSTIN_RE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")
IEC_CONTEXT_RE = re.compile(r"\bIEC(?:\s*(?:number|code))?\s*[:=]\s*([A-Z0-9]{8,10})\b", re.I)
LOCAL_PATH_RE = re.compile(r"/Users/[^`'\"\s,)]+")
SECRET_PATTERNS = [
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{16,}", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:password|passwd|token|cookie|session|secret|api[_-]?key)\s*[:=]\s*[^\s,'\"]{6,}", re.I),
    re.compile(r"\b(?:uploaded_file_id|message_id)\s*[:=]\s*[A-Za-z0-9._-]{8,}", re.I),
    re.compile(r"\b(?:id_rsa|id_ed25519|\.pem|\.p12|\.pfx)\b", re.I),
]

ALLOWED_EMAIL_DOMAINS = {"example.com", "example.test", "test.example", "test.invalid", "localhost"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def parse_allowlist(path: Path) -> tuple[list[str], list[str]]:
    if not path.exists():
        return [], []
    allowed_paths: list[str] = []
    allowed_literals: list[str] = []
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(":"):
            current = line[:-1]
            continue
        if line.startswith("- ") and current:
            value = line[2:].strip().strip('"').strip("'")
            if current == "allowed_paths":
                allowed_paths.append(value)
            elif current == "allowed_literal_patterns":
                allowed_literals.append(value)
    return allowed_paths, allowed_literals


def is_private_runtime_path(path: Path) -> bool:
    relative = rel(path)
    if matches(relative, PUBLIC_EXCEPTIONS):
        return False
    return matches(relative, PRIVATE_PATH_PATTERNS)


def is_tracked_private_runtime_path(path: str) -> bool:
    if matches(path, TRACKED_PUBLIC_EXCEPTIONS):
        return False
    return matches(path, TRACKED_PRIVATE_PATH_PATTERNS)


def git_tracked_private_runtime_paths() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "data", "outputs", "receipts"],
            cwd=PROJECT_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    return sorted(path for path in result.stdout.splitlines() if is_tracked_private_runtime_path(path))


def iter_public_template_scan_files() -> Iterable[Path]:
    seen: set[Path] = set()
    for pattern in PUBLIC_TEMPLATE_INCLUDE_PATTERNS:
        for path in PROJECT_ROOT.glob(pattern):
            if not path.is_file():
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path


def iter_scan_files(public_template: bool) -> Iterable[Path]:
    if public_template:
        yield from iter_public_template_scan_files()
        return
    for root, dirs, files in os.walk(PROJECT_ROOT):
        root_path = Path(root)
        dirs[:] = [
            d
            for d in dirs
            if not is_private_runtime_path(root_path / d / "placeholder")
        ]
        for name in files:
            path = root_path / name
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            yield path


def scrub_allowed(line: str, allowed_literals: list[str]) -> str:
    scrubbed = line
    for literal in allowed_literals:
        scrubbed = scrubbed.replace(literal, "")
    return scrubbed


def scan_line(path: Path, line_number: int, line: str, allowed_literals: list[str]) -> list[str]:
    findings: list[str] = []
    text = scrub_allowed(line, allowed_literals)
    for match in EMAIL_RE.finditer(text):
        domain = match.group(1).lower()
        if domain not in ALLOWED_EMAIL_DOMAINS:
            findings.append(f"email:{match.group(0)}")
    if PHONE_RE.search(text):
        findings.append("phone-like-number")
    if GSTIN_RE.search(text):
        findings.append("gstin-like-id")
    iec = IEC_CONTEXT_RE.search(text)
    if iec and "YOUR" not in text.upper() and "EXAMPLE" not in text.upper():
        findings.append("iec-like-id")
    if LOCAL_PATH_RE.search(text):
        findings.append("local-user-path")
    for pattern in SECRET_PATTERNS:
        if "re.compile(" in text:
            continue
        if pattern.search(text):
            findings.append("secret-like-value")
            break
    return [f"{rel(path)}:{line_number}: {finding}" for finding in findings]


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan public-template files for private runtime data")
    parser.add_argument("--public-template", action="store_true", help="Skip declared private runtime paths")
    parser.add_argument("--allowlist", default=str(ALLOWLIST), help="Allowlist YAML path")
    args = parser.parse_args()

    allowed_paths, allowed_literals = parse_allowlist(Path(args.allowlist))
    findings: list[str] = []
    tracked_private_paths = git_tracked_private_runtime_paths()
    if not args.public_template:
        findings.extend(f"git-tracked-private-runtime-path:{path}" for path in tracked_private_paths)
    for path in iter_scan_files(args.public_template):
        relative = rel(path)
        allowed_by_path = matches(relative, allowed_paths)
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError as exc:
            findings.append(f"{relative}: read-error:{exc}")
            continue
        for index, line in enumerate(lines, start=1):
            line_findings = scan_line(path, index, line, allowed_literals)
            if allowed_by_path:
                line_findings = [
                    finding
                    for finding in line_findings
                    if not finding.endswith(" local-user-path")
                ]
            findings.extend(line_findings)

    if findings:
        print("Private runtime scan failed:")
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1
    print("Private runtime scan passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
