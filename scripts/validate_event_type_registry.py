#!/usr/bin/env python3
"""Validate event type registry against the event schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import parse_event_type_registry_minimal  # noqa: E402

EVENT_SCHEMA = PROJECT_ROOT / "config" / "schemas" / "event.schema.json"
REGISTRY = PROJECT_ROOT / "config" / "schemas" / "event_types.yaml"
REQUIRED_KEYS = {
    "object_type",
    "actor_allowed",
    "required_payload_fields",
    "allowed_payload_fields",
    "forbidden_payload_keys",
    "citation_required",
    "private_data_allowed",
}
MANDATORY_FORBIDDEN = {"password", "token", "cookie", "session", "dsc"}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ModuleNotFoundError:
        return parse_minimal_yaml(path)


def parse_minimal_yaml(path: Path) -> dict[str, Any]:
    return parse_event_type_registry_minimal(path)


def effective(defaults: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    merged.update(entry or {})
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate event type registry")
    parser.add_argument("--registry", default=str(REGISTRY))
    parser.add_argument("--schema", default=str(EVENT_SCHEMA))
    args = parser.parse_args()

    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    registry = load_yaml(Path(args.registry))
    defaults = registry.get("defaults", {})
    events = registry.get("events", {})
    errors: list[str] = []

    schema_types = set(schema.get("event_types", []))
    registry_types = set(events)
    missing = sorted(schema_types - registry_types)
    extra = sorted(registry_types - schema_types)
    if missing:
        errors.append(f"missing registry entries: {missing}")
    if extra:
        errors.append(f"registry entries not in event schema: {extra}")

    object_types = set(schema.get("object_types", []))
    for event_type in sorted(schema_types & registry_types):
        merged = effective(defaults, events[event_type])
        missing_keys = sorted(REQUIRED_KEYS - set(merged))
        if missing_keys:
            errors.append(f"{event_type}: missing keys after defaults: {missing_keys}")
        if merged.get("object_type") not in object_types:
            errors.append(f"{event_type}: unknown object_type {merged.get('object_type')!r}")
        forbidden = {str(item).lower() for item in merged.get("forbidden_payload_keys", [])}
        if not MANDATORY_FORBIDDEN.issubset(forbidden):
            errors.append(f"{event_type}: forbidden_payload_keys must include {sorted(MANDATORY_FORBIDDEN)}")
        if not isinstance(merged.get("citation_required"), bool):
            errors.append(f"{event_type}: citation_required must be boolean")
        if not isinstance(merged.get("private_data_allowed"), bool):
            errors.append(f"{event_type}: private_data_allowed must be boolean")

    if errors:
        print("Event type registry validation failed:")
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"Event type registry validation passed: {len(schema_types)} event types")
    return 0


if __name__ == "__main__":
    sys.exit(main())
