#!/usr/bin/env python3
"""Validate ChatGPT boardroom returns before staging."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SECTIONS = [
    "executive_summary",
    "cited_findings",
    "recommended_strategy",
    "risks_and_assumptions",
    "suggested_hermes_codex_follow_up_tasks",
    "evidence_gaps",
    "do_not_execute_without_approval",
]

REQUIRED_METADATA = [
    "return_id",
    "related_case_ids",
    "sources_used",
    "confidence_level",
    "open_questions",
    "recommended_next_actions",
    "approval_boundary_statement",
]

MUTATION_PATTERNS = [
    re.compile(r"\b(?:update|write|edit|append|overwrite)\s+(?:data/)?(?:master_cases|supplier_master|quote_master|buyer_master|events)\b", re.I),
    re.compile(r"\bmutate\s+(?:the\s+)?(?:register|ledger|csv)\b", re.I),
    re.compile(r"\brebuild\s+projections\s+and\s+write\s+back\b", re.I),
]

FORBIDDEN_WITHOUT_APPROVAL_PATTERNS = [
    re.compile(r"\b(?:send|submit|upload|pay|sign|use\s+dsc|commit|certify|claim)\b.{0,80}\bwithout\s+approval\b", re.I | re.S),
    re.compile(r"\b(?:immediately|automatically|auto)\s+(?:send|submit|upload|pay|sign|commit|certify)\b", re.I),
    re.compile(r"\b(?:final\s+price|country\s+of\s+origin|hsn|itc-hs)\b.{0,80}\b(?:confirmed|final|certified)\b", re.I | re.S),
]

EXTERNAL_FACT_RE = re.compile(r"https?://|www\.|according to|source:|cited", re.I)
CITATION_RE = re.compile(r"https?://|outputs/|data/|receipts/|docs/|source", re.I)


def normalize_heading(value: str) -> str:
    value = value.strip().lower().strip("#").strip()
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value


def load_input(path: Path) -> tuple[str, dict[str, Any] | None]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        try:
            return text, json.loads(text)
        except json.JSONDecodeError:
            return text, None
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            return text, json.loads(stripped)
        except json.JSONDecodeError:
            return text, None
    return text, None


def markdown_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            keys.add(normalize_heading(stripped))
            continue
        if ":" in stripped:
            key = stripped.split(":", 1)[0]
            keys.add(normalize_heading(key))
    return keys


def json_keys(data: dict[str, Any]) -> set[str]:
    return {normalize_heading(str(key)) for key in data.keys()}


def validate_text(text: str, data: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    keys = json_keys(data) if data is not None else markdown_keys(text)

    for section in REQUIRED_SECTIONS:
        if section not in keys:
            errors.append(f"missing required section: {section}")
    for field in REQUIRED_METADATA:
        if field not in keys:
            errors.append(f"missing required metadata: {field}")

    lowered = text.lower()
    for pattern in MUTATION_PATTERNS:
        if pattern.search(text):
            errors.append("return instructs direct register or ledger mutation")
            break
    for pattern in FORBIDDEN_WITHOUT_APPROVAL_PATTERNS:
        if pattern.search(text):
            errors.append("return instructs forbidden external/final action without approval")
            break
    if EXTERNAL_FACT_RE.search(text) and not CITATION_RE.search(text):
        errors.append("external facts appear without citations or sources_used")
    if "approval_boundary_statement" in keys and "approval" not in lowered:
        errors.append("approval_boundary_statement must explicitly mention approval")
    return errors


def validate_file(path: Path | str) -> tuple[bool, list[str]]:
    input_path = Path(path)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    text, data = load_input(input_path)
    errors = validate_text(text, data)
    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a ChatGPT return packet")
    parser.add_argument("--input", default="", help="Markdown or JSON return file")
    parser.add_argument("--fixture", default="", help="Alias for --input")
    args = parser.parse_args()
    value = args.input or args.fixture
    if not value:
        parser.error("--input or --fixture is required")
    ok, errors = validate_file(value)
    if not ok:
        print("ChatGPT return validation failed:")
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("ChatGPT return validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
