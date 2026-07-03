#!/usr/bin/env python3
"""Validate TEOS worker role-specific plugin skill imports.

Reads config/worker_plugin_policy.yaml and checks that every selected external
skill payload has a profile-local imported Hermes skill with matching frontmatter
and source provenance.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    print(f"ERROR: PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config" / "worker_plugin_policy.yaml"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "skill"


def make_claude_target_name(rel_path: str) -> str:
    parts = Path(rel_path).parts
    if len(parts) >= 5 and parts[0] == "directory_plugins" and parts[1] == "by_name" and parts[3] == "skills":
        return f"teos-claude-{slugify(parts[2])}-{slugify(parts[4])}"
    if len(parts) >= 5 and parts[0] == "marketplace_sources" and "skills" in parts:
        idx = parts.index("skills")
        prefix = "-".join(slugify(p) for p in parts[1:idx])
        skill = parts[idx + 1] if idx + 1 < len(parts) else parts[-1]
        return f"teos-claude-{prefix}-{slugify(skill)}"
    if "skills" in parts:
        idx = parts.index("skills")
        prefix_parts = [p for p in parts[max(0, idx - 3) : idx] if p not in {"plugins", "marketplaces"}]
        prefix = "-".join(slugify(p) for p in prefix_parts) or "plugin"
        skill = parts[idx + 1] if idx + 1 < len(parts) else parts[-1]
        return f"teos-claude-{prefix}-{slugify(skill)}"
    return f"teos-claude-{slugify(rel_path)}"


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Policy must be a YAML mapping: {path}")
    return data


def first_frontmatter_block(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 4)
    if end == -1:
        return ""
    return text[4:end]


def frontmatter_value(block: str, key: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.+)$", re.M)
    match = pattern.search(block)
    if not match:
        return None
    return match.group(1).strip().strip('"\'')


def expected_items(policy: dict[str, Any], profiles: set[str] | None) -> list[dict[str, str]]:
    profiles_root = Path(policy.get("profiles_root", ""))
    category = policy.get("import_category_path", "tender-export-os/plugin-imports")
    imports = policy.get("profile_imports") or {}
    items: list[dict[str, str]] = []
    for profile, cfg in imports.items():
        if profiles and profile not in profiles:
            continue
        base = profiles_root / profile / "skills" / category
        for skill in cfg.get("accio") or []:
            target_name = f"teos-accio-{slugify(skill)}"
            items.append({
                "profile": profile,
                "kind": "accio",
                "source_label": skill,
                "target_name": target_name,
                "target_path": str(base / target_name / "SKILL.md"),
            })
        for rel in cfg.get("claude") or []:
            target_name = make_claude_target_name(rel)
            items.append({
                "profile": profile,
                "kind": "claude",
                "source_label": rel,
                "target_name": target_name,
                "target_path": str(base / target_name / "SKILL.md"),
            })
    return items


def validate_item(item: dict[str, str]) -> dict[str, Any]:
    path = Path(item["target_path"])
    errors: list[str] = []
    if not path.exists():
        errors.append("missing target SKILL.md")
        return item | {"ok": False, "errors": errors}
    text = path.read_text(encoding="utf-8", errors="ignore")
    block = first_frontmatter_block(text)
    if not block:
        errors.append("missing YAML frontmatter")
    name = frontmatter_value(block, "name")
    if name != item["target_name"]:
        errors.append(f"frontmatter name mismatch: {name!r} != {item['target_name']!r}")
    profile = frontmatter_value(block, "teos_import_profile")
    if profile != item["profile"]:
        errors.append(f"profile provenance mismatch: {profile!r} != {item['profile']!r}")
    kind = frontmatter_value(block, "teos_source_kind")
    if kind != item["kind"]:
        errors.append(f"source kind mismatch: {kind!r} != {item['kind']!r}")
    if "Tender Export OS Safety Overlay" not in text:
        errors.append("missing TEOS safety overlay")
    if "teos_external_actions_allowed: false" not in block:
        errors.append("external action flag missing or not false")
    return item | {"ok": not errors, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--profile", action="append")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    policy = read_yaml(Path(args.policy).expanduser().resolve())
    selected = set(args.profile or []) or None
    results = [validate_item(i) for i in expected_items(policy, selected)]
    failures = [r for r in results if not r["ok"]]
    summary = {
        "policy": str(Path(args.policy).expanduser().resolve()),
        "items": len(results),
        "ok": len(results) - len(failures),
        "failed": len(failures),
        "profiles": sorted({r["profile"] for r in results}),
        "failures": failures,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        if failures:
            print(f"TEOS worker plugin import validation FAILED: {len(failures)} failure(s) / {len(results)} item(s)")
            for failure in failures:
                print(f"- {failure['profile']} {failure['target_name']}: {', '.join(failure['errors'])}")
        else:
            print(f"TEOS worker plugin import validation passed: {len(results)} imported skill(s) across {len(summary['profiles'])} profile(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
