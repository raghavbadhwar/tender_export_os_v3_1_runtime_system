#!/usr/bin/env python3
"""Import role-specific external plugin skill payloads into TEOS Hermes worker profiles.

This script implements config/worker_plugin_policy.yaml.

Safety defaults:
- Dry-run unless --write is passed.
- Imports SKILL.md payloads as profile-local Hermes skills.
- Does not enable Hermes-native plugins.
- Does not configure MCP servers.
- Does not modify source plugin directories.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    print(f"ERROR: PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config" / "worker_plugin_policy.yaml"
REPORT_DIR = ROOT / "outputs" / "audits"


@dataclass
class ImportItem:
    profile: str
    kind: str
    source_label: str
    source_dir: Path
    target_name: str
    target_dir: Path
    status: str
    error: str | None = None


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "skill"


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Policy must be a YAML mapping: {path}")
    return data


def configured_root(value: Any) -> Path | None:
    """Return an explicit absolute runtime root, or ``None`` when unset.

    Public-template policy values intentionally use environment-variable
    placeholders.  Leaving one unresolved must never turn it into a relative
    path that an import operation could accidentally use.
    """
    raw = str(value or "").strip()
    expanded = os.path.expandvars(raw)
    if not raw or "$" in expanded:
        return None
    candidate = Path(expanded).expanduser()
    return candidate if candidate.is_absolute() else None


def configured_roots(policy: dict[str, Any]) -> tuple[Path, Path, Path]:
    """Resolve all roots required for a worker-skill import.

    Imports are an opt-in private-deployment action.  The public repository
    deliberately has no bundled external skill library, so a missing root is
    treated as unconfigured rather than as a source to probe or create.
    """
    roots = policy.get("source_roots") or {}
    accio_root = configured_root(roots.get("accio"))
    claude_root = configured_root(roots.get("claude"))
    profiles_root = configured_root(policy.get("profiles_root"))
    if not all((accio_root, claude_root, profiles_root)):
        raise ValueError(
            "Worker skill imports are unconfigured. Set "
            "TEOS_ACCIO_SKILLS_ROOT, TEOS_CLAUDE_SKILLS_ROOT, and "
            "TEOS_HERMES_PROFILES_ROOT to explicit absolute paths."
        )
    return accio_root, claude_root, profiles_root


def extract_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return simple frontmatter key/value strings and markdown body."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[text.find("\n", end + 1) + 1 :]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line or line.lstrip() != line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip().strip("'\"")
        if key:
            meta[key] = val
    return meta, body


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return json.dumps(str(value), ensure_ascii=False)


def make_claude_target_name(rel_path: str) -> str:
    parts = Path(rel_path).parts
    # Common curated export: directory_plugins/by_name/<family>/skills/<skill>
    if len(parts) >= 5 and parts[0] == "directory_plugins" and parts[1] == "by_name" and parts[3] == "skills":
        family = parts[2]
        skill = parts[4]
        return f"teos-claude-{slugify(family)}-{slugify(skill)}"
    # Marketplace source: marketplace_sources/<plugin>/<bundle>/skills/<skill>
    if len(parts) >= 5 and parts[0] == "marketplace_sources" and "skills" in parts:
        idx = parts.index("skills")
        prefix = "-".join(slugify(p) for p in parts[1:idx])
        skill = parts[idx + 1] if idx + 1 < len(parts) else parts[-1]
        return f"teos-claude-{prefix}-{slugify(skill)}"
    # Official/other source: try to include plugin folder before skills.
    if "skills" in parts:
        idx = parts.index("skills")
        prefix_parts = [p for p in parts[max(0, idx - 3) : idx] if p not in {"plugins", "marketplaces"}]
        prefix = "-".join(slugify(p) for p in prefix_parts) or "plugin"
        skill = parts[idx + 1] if idx + 1 < len(parts) else parts[-1]
        return f"teos-claude-{prefix}-{slugify(skill)}"
    return f"teos-claude-{slugify(rel_path)}"


def patch_skill_text(
    original_text: str,
    *,
    target_name: str,
    profile: str,
    kind: str,
    source_label: str,
    source_dir: Path,
    imported_at: str,
) -> str:
    meta, body = extract_frontmatter(original_text)
    original_name = meta.get("name") or source_dir.name
    original_description = meta.get("description") or f"Imported {kind} skill payload from {source_label}."
    description = (
        f"Tender Export OS profile-local plugin skill for {profile}; imported from {kind}:{source_label}. "
        f"Original: {original_description}"
    )
    if len(description) > 420:
        description = description[:417] + "..."

    frontmatter = {
        "name": target_name,
        "description": description,
        "teos_import_profile": profile,
        "teos_source_kind": kind,
        "teos_source_label": source_label,
        "teos_source_path": str(source_dir),
        "teos_original_skill_name": original_name,
        "teos_imported_at": imported_at,
        "teos_external_actions_allowed": False,
        "created_by": "teos_worker_plugin_importer",
    }
    fm_lines = ["---"]
    for key, value in frontmatter.items():
        fm_lines.append(f"{key}: {yaml_scalar(value)}")
    fm_lines.append("---")

    overlay = f"""

# TEOS Plugin Import: {original_name}

## Tender Export OS Safety Overlay

This is an imported plugin/skill payload for the `{profile}` Hermes worker profile.
It is subordinate to the worker `SOUL.md`, the live Tender Export OS approval policy,
`config/worker_plugin_policy.yaml`, and the `tender-export-operator` skill.

Hard limits:

- Use this skill for internal analysis, drafting, extraction, research, and artifact support only.
- Do not send email/messages, post publicly, upload portal documents, submit bids, use DSC, pay money, place orders, or commit price/delivery/payment/origin/HSN/ITC-HS.
- If the imported skill suggests an external action, convert it into an approval card or draft for owner review.
- Cite sources and leave TEOS run-log/proof artifacts when the task mutates case state.

## Imported Skill Content
"""
    return "\n".join(fm_lines).rstrip() + overlay + "\n" + body.lstrip()


def load_items(policy: dict[str, Any], profiles: set[str] | None = None) -> list[ImportItem]:
    accio_root, claude_root, profiles_root = configured_roots(policy)
    category = policy.get("import_category_path", "tender-export-os/plugin-imports")
    imports = policy.get("profile_imports") or {}

    items: list[ImportItem] = []
    for profile, cfg in imports.items():
        if profiles and profile not in profiles:
            continue
        base_target = profiles_root / profile / "skills" / category
        for skill in cfg.get("accio") or []:
            source_dir = accio_root / skill
            target_name = f"teos-accio-{slugify(skill)}"
            items.append(
                ImportItem(
                    profile=profile,
                    kind="accio",
                    source_label=skill,
                    source_dir=source_dir,
                    target_name=target_name,
                    target_dir=base_target / target_name,
                    status="pending",
                )
            )
        for rel in cfg.get("claude") or []:
            source_dir = claude_root / rel
            target_name = make_claude_target_name(rel)
            items.append(
                ImportItem(
                    profile=profile,
                    kind="claude",
                    source_label=rel,
                    source_dir=source_dir,
                    target_name=target_name,
                    target_dir=base_target / target_name,
                    status="pending",
                )
            )
    return items


def import_item(item: ImportItem, *, write: bool, imported_at: str) -> ImportItem:
    skill_md = item.source_dir / "SKILL.md"
    profile_dir = item.target_dir.parents[2]  # .../<profile>/skills/tender-export-os/plugin-imports/name
    if not profile_dir.exists():
        item.status = "error"
        item.error = f"Profile directory missing: {profile_dir}"
        return item
    if not skill_md.exists():
        item.status = "error"
        item.error = f"Source SKILL.md missing: {skill_md}"
        return item

    original_text = skill_md.read_text(encoding="utf-8", errors="ignore")
    existing = item.target_dir / "SKILL.md"
    effective_imported_at = imported_at
    if existing.exists():
        try:
            existing_meta, _ = extract_frontmatter(existing.read_text(encoding="utf-8", errors="ignore"))
            effective_imported_at = existing_meta.get("teos_imported_at") or imported_at
        except Exception:
            effective_imported_at = imported_at

    patched = patch_skill_text(
        original_text,
        target_name=item.target_name,
        profile=item.profile,
        kind=item.kind,
        source_label=item.source_label,
        source_dir=item.source_dir,
        imported_at=effective_imported_at,
    )

    if existing.exists():
        try:
            if existing.read_text(encoding="utf-8", errors="ignore") == patched:
                item.status = "unchanged"
            else:
                item.status = "would_update" if not write else "updated"
        except Exception:
            item.status = "would_update" if not write else "updated"
    else:
        item.status = "would_create" if not write else "created"

    if not write:
        return item

    item.target_dir.mkdir(parents=True, exist_ok=True)
    # Copy support files/directories. Do not delete existing target files.
    shutil.copytree(item.source_dir, item.target_dir, dirs_exist_ok=True)
    (item.target_dir / "SKILL.md").write_text(patched, encoding="utf-8")
    return item


def report_markdown(items: list[ImportItem], *, write: bool, imported_at: str, policy_path: Path) -> str:
    created = sum(1 for i in items if i.status == "created")
    updated = sum(1 for i in items if i.status == "updated")
    unchanged = sum(1 for i in items if i.status == "unchanged")
    would_create = sum(1 for i in items if i.status == "would_create")
    would_update = sum(1 for i in items if i.status == "would_update")
    errors = [i for i in items if i.status == "error"]
    profiles = sorted({i.profile for i in items})

    lines = [
        "# TEOS Worker Plugin Import Report",
        "",
        f"**Timestamp:** {imported_at}",
        f"**Policy:** `{policy_path}`",
        f"**Mode:** {'WRITE' if write else 'DRY-RUN'}",
        "",
        "## Summary",
        "",
        f"- Profiles covered: {len(profiles)}",
        f"- Import items processed: {len(items)}",
        f"- Created: {created}",
        f"- Updated: {updated}",
        f"- Unchanged: {unchanged}",
        f"- Would create: {would_create}",
        f"- Would update: {would_update}",
        f"- Errors: {len(errors)}",
        "",
        "## Safety Boundaries",
        "",
        "- No Hermes-native runtime plugins were enabled.",
        "- No MCP servers were configured.",
        "- No external source plugin directories were modified.",
        "- Imported skills include a Tender Export OS safety overlay and provenance.",
        "- Imported skills are for internal research/drafting/artifact support only; external sends/uploads/payments/DSC/final commitments remain approval-gated.",
        "",
        "## Profile Imports",
        "",
    ]
    for profile in profiles:
        lines.append(f"### `{profile}`")
        lines.append("")
        for i in [x for x in items if x.profile == profile]:
            err = f" — ERROR: {i.error}" if i.error else ""
            lines.append(f"- `{i.target_name}` ← `{i.kind}:{i.source_label}` — **{i.status}**{err}")
        lines.append("")
    if errors:
        lines.extend(["## Errors", ""])
        for i in errors:
            lines.append(f"- `{i.profile}` `{i.target_name}`: {i.error}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", default=str(DEFAULT_POLICY), help="Path to worker_plugin_policy.yaml")
    parser.add_argument("--profile", action="append", help="Limit to one profile; may repeat")
    parser.add_argument("--write", action="store_true", help="Actually write profile-local imported skills")
    parser.add_argument("--dry-run", action="store_true", help="Explicit dry-run mode (default)")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    parser.add_argument("--report", action="store_true", help="Write markdown report under outputs/audits")
    args = parser.parse_args(argv)

    policy_path = Path(args.policy).expanduser().resolve()
    policy = read_yaml(policy_path)
    selected = set(args.profile or []) or None
    imported_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        items = load_items(policy, selected)
    except ValueError as exc:
        summary = {
            "mode": "write" if args.write else "dry-run",
            "policy": str(policy_path),
            "items": 0,
            "profiles": [],
            "status": "SKIPPED_UNCONFIGURED",
            "reason": str(exc),
            "status_counts": {},
            "errors": [],
            "report_path": None,
        }
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(f"TEOS worker plugin import skipped: {exc}")
        # A dry run is a safe no-op; an explicit write must fail closed.
        return 2 if args.write else 0
    if not items:
        print("No import items selected", file=sys.stderr)
        return 1

    processed = [import_item(i, write=args.write, imported_at=imported_at) for i in items]
    report = report_markdown(processed, write=args.write, imported_at=imported_at, policy_path=policy_path)

    if args.report or args.write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        suffix = "write" if args.write else "dry_run"
        report_path = REPORT_DIR / f"worker_plugin_import_report_{stamp}_{suffix}.md"
        report_path.write_text(report, encoding="utf-8")
    else:
        report_path = None

    summary = {
        "mode": "write" if args.write else "dry-run",
        "policy": str(policy_path),
        "items": len(processed),
        "profiles": sorted({i.profile for i in processed}),
        "status_counts": {},
        "errors": [i.__dict__ | {"source_dir": str(i.source_dir), "target_dir": str(i.target_dir)} for i in processed if i.status == "error"],
        "report_path": str(report_path) if report_path else None,
    }
    for i in processed:
        summary["status_counts"][i.status] = summary["status_counts"].get(i.status, 0) + 1

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(report)
        if report_path:
            print(f"Report saved: {report_path}")

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
