#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_routed_agent_names(path: Path) -> set[str]:
    names: set[str] = set()
    in_agents = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "agents:":
            in_agents = True
            continue
        if in_agents and line and not line.startswith(" "):
            break
        if not in_agents or not line.startswith("  ") or line.startswith("    "):
            continue
        key = stripped.split(":", 1)[0].strip()
        if key:
            names.add(key)
    return names


def main():
    routed = load_routed_agent_names(PROJECT_ROOT / "config" / "agent_capability_routing.yaml")
    failures = []
    for p in sorted((PROJECT_ROOT / "agents").glob("*.md")):
        text = p.read_text(encoding="utf-8")
        name = p.stem
        for needle in ["Best-in-Class Tuning", "source", "approval"]:
            if needle.lower() not in text.lower():
                failures.append(f"{p.relative_to(PROJECT_ROOT)} missing {needle}")
        if name not in routed:
            failures.append(f"{name} missing from config/agent_capability_routing.yaml")
    if failures:
        print("FAIL: agent prompt audit")
        print("\n".join(failures))
        return 1
    print(f'PASS: audited {len(list((PROJECT_ROOT / "agents").glob("*.md")))} agent prompts and capability routing')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
