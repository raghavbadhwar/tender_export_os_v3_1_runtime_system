#!/usr/bin/env python3
"""
validate_loop_schedule.py

Validates the Tender + Export OS loop schedule registry against the loop registry.

Usage:
    python scripts/validate_loop_schedule.py
    python scripts/validate_loop_schedule.py --schedule config/loop_schedule.json --loops config/agent_loops.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEDULE = PROJECT_ROOT / "config" / "loop_schedule.json"
DEFAULT_LOOPS = PROJECT_ROOT / "config" / "agent_loops.json"

REQUIRED_TOP_LEVEL_KEYS = {
    "spec_version",
    "date",
    "agent_name",
    "timezone",
    "sources_used",
    "global_rules",
    "schedules",
}

REQUIRED_GLOBAL_RULES = {
    "autonomy_level",
    "case_key",
    "run_log",
    "approval_policy",
    "external_effects_allowed_without_approval",
    "credentials_allowed_in_outputs",
    "default_failure_handoff",
    "schedule_change_rule",
}

REQUIRED_SCHEDULE_KEYS = {
    "schedule_id",
    "status",
    "cadence",
    "purpose",
    "max_total_runtime_minutes",
    "entries",
}

REQUIRED_ENTRY_KEYS = {
    "slot",
    "loop_name",
    "phase",
    "mode",
    "input_scope",
    "max_runtime_minutes",
    "depends_on",
    "approval_behavior",
    "outputs",
}

FORBIDDEN_APPROVAL_BEHAVIOR = {
    "execute without approval",
    "auto approve",
    "send without approval",
    "submit without approval",
    "use dsc",
}

SLOT_PATTERN = re.compile(r"^([0-2][0-9]:[0-5][0-9])(,[0-2][0-9]:[0-5][0-9])*$|^on_[a-z0-9_]+$")


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def non_empty(value):
    if value is None:
        return False
    if isinstance(value, (str, list, dict)):
        return len(value) > 0
    return True


def require_keys(errors, location, obj, keys, allow_empty_keys=None):
    allow_empty_keys = allow_empty_keys or set()
    missing = sorted(keys - set(obj.keys()))
    for key in missing:
        errors.append(f"{location}: missing required key '{key}'")
    for key in sorted(keys & set(obj.keys())):
        if key in allow_empty_keys:
            continue
        if not non_empty(obj[key]) and obj[key] is not False:
            errors.append(f"{location}: key '{key}' must not be empty")


def validate_entry(errors, entry, location, loop_names):
    require_keys(errors, location, entry, REQUIRED_ENTRY_KEYS, allow_empty_keys={"depends_on"})

    loop_name = entry.get("loop_name")
    if loop_name and loop_name not in loop_names:
        errors.append(f"{location}.loop_name: unknown loop '{loop_name}'")

    slot = entry.get("slot", "")
    if slot and not SLOT_PATTERN.match(slot):
        errors.append(f"{location}.slot: must be HH:MM, comma-separated HH:MM, or on_event_name")

    max_runtime = entry.get("max_runtime_minutes")
    if not isinstance(max_runtime, int) or max_runtime < 1:
        errors.append(f"{location}.max_runtime_minutes: must be a positive integer")

    if not isinstance(entry.get("depends_on", []), list):
        errors.append(f"{location}.depends_on: must be a list")

    if not isinstance(entry.get("outputs", []), list):
        errors.append(f"{location}.outputs: must be a list")

    approval_behavior = str(entry.get("approval_behavior", "")).lower()
    for forbidden in FORBIDDEN_APPROVAL_BEHAVIOR:
        if forbidden in approval_behavior:
            errors.append(f"{location}.approval_behavior: unsafe behavior '{forbidden}'")


def validate_schedule(errors, schedule, index, loop_names):
    location = f"schedules[{index}]"
    require_keys(errors, location, schedule, REQUIRED_SCHEDULE_KEYS)

    if schedule.get("status") not in {"ACTIVE", "PAUSED"}:
        errors.append(f"{location}.status: must be ACTIVE or PAUSED")

    max_total = schedule.get("max_total_runtime_minutes")
    if not isinstance(max_total, int) or max_total < 1:
        errors.append(f"{location}.max_total_runtime_minutes: must be a positive integer")

    entries = schedule.get("entries", [])
    if not isinstance(entries, list) or not entries:
        errors.append(f"{location}.entries: must contain at least one entry")
        return

    phase_names = set()
    total_runtime = 0
    for entry_index, entry in enumerate(entries):
        entry_location = f"{location}.entries[{entry_index}]"
        if not isinstance(entry, dict):
            errors.append(f"{entry_location}: must be an object")
            continue
        phase = entry.get("phase")
        if phase in phase_names:
            errors.append(f"{entry_location}.phase: duplicate phase '{phase}' in schedule")
        phase_names.add(phase)
        total_runtime += entry.get("max_runtime_minutes", 0) if isinstance(entry.get("max_runtime_minutes"), int) else 0
        validate_entry(errors, entry, entry_location, loop_names)

    if isinstance(max_total, int) and total_runtime > max_total:
        errors.append(f"{location}: entry runtimes total {total_runtime}, above max_total_runtime_minutes {max_total}")


def validate(schedule, loop_registry):
    errors = []
    require_keys(errors, "schedule_registry", schedule, REQUIRED_TOP_LEVEL_KEYS)

    global_rules = schedule.get("global_rules", {})
    if isinstance(global_rules, dict):
        require_keys(errors, "global_rules", global_rules, REQUIRED_GLOBAL_RULES)
        if global_rules.get("external_effects_allowed_without_approval") is not False:
            errors.append("global_rules.external_effects_allowed_without_approval: must be false")
        if global_rules.get("credentials_allowed_in_outputs") is not False:
            errors.append("global_rules.credentials_allowed_in_outputs: must be false")
        if global_rules.get("approval_policy") != "config/approval_policy.yaml":
            errors.append("global_rules.approval_policy: must be config/approval_policy.yaml")
    else:
        errors.append("global_rules: must be an object")

    loop_names = {loop.get("loop_name") for loop in loop_registry.get("loops", []) if isinstance(loop, dict)}
    if not loop_names:
        errors.append("loop registry: no loop names found")

    schedules = schedule.get("schedules", [])
    if not isinstance(schedules, list) or not schedules:
        errors.append("schedules: must contain at least one schedule")
    else:
        ids = []
        referenced_loops = set()
        for index, item in enumerate(schedules):
            if not isinstance(item, dict):
                errors.append(f"schedules[{index}]: must be an object")
                continue
            ids.append(item.get("schedule_id"))
            for entry in item.get("entries", []):
                if isinstance(entry, dict) and entry.get("loop_name"):
                    referenced_loops.add(entry["loop_name"])
            validate_schedule(errors, item, index, loop_names)
        for schedule_id in sorted({item for item in ids if ids.count(item) > 1}):
            errors.append(f"schedules: duplicate schedule_id '{schedule_id}'")

        unreferenced = sorted(loop_names - referenced_loops)
        for loop_name in unreferenced:
            errors.append(f"schedules: loop '{loop_name}' is not scheduled or event-triggered")

    app_targets = schedule.get("app_automation_targets", [])
    if app_targets:
        schedule_ids = {item.get("schedule_id") for item in schedules if isinstance(item, dict)}
        for index, target in enumerate(app_targets):
            location = f"app_automation_targets[{index}]"
            if target.get("schedule_id") not in schedule_ids:
                errors.append(f"{location}.schedule_id: must reference a configured schedule")
            prompt_file = target.get("prompt_file")
            if prompt_file and not (PROJECT_ROOT / prompt_file).exists():
                errors.append(f"{location}.prompt_file: file does not exist: {prompt_file}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate Tender + Export OS loop schedule registry")
    parser.add_argument("--schedule", default=str(DEFAULT_SCHEDULE), help="Path to loop_schedule.json")
    parser.add_argument("--loops", default=str(DEFAULT_LOOPS), help="Path to agent_loops.json")
    args = parser.parse_args()

    schedule_path = Path(args.schedule)
    loops_path = Path(args.loops)
    if not schedule_path.is_absolute():
        schedule_path = PROJECT_ROOT / schedule_path
    if not loops_path.is_absolute():
        loops_path = PROJECT_ROOT / loops_path

    try:
        schedule = load_json(schedule_path)
        loop_registry = load_json(loops_path)
    except FileNotFoundError as exc:
        print(f"FAIL: file not found: {exc.filename}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return 1

    errors = validate(schedule, loop_registry)
    if errors:
        print("FAIL: loop schedule registry has validation errors")
        for error in errors:
            print(f"- {error}")
        return 1

    schedules = schedule.get("schedules", [])
    entries = sum(len(item.get("entries", [])) for item in schedules)
    print(f"PASS: {schedule_path}")
    print(f"Schedules validated: {len(schedules)}")
    print(f"Entries validated: {entries}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
