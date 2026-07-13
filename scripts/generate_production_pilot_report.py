#!/usr/bin/env python3
"""Generate a 30-day production pilot measurement report."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_shadow_pilot_report import parse_date, safe_float, summarize_evaluations, summarize_run_log


DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "production_pilot.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "production_pilot"
DEFAULT_STATE_FILE = DATA_DIR / "production_pilot_state.json"


def load_yaml(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def in_window(row_date: str, start: dt.date, end: dt.date) -> bool:
    parsed = parse_date(row_date)
    return bool(parsed and start <= parsed <= end)


def weekly_review_count(rows: list[dict[str, str]]) -> int:
    weeks = set()
    for row in rows:
        text = f"{row.get('actions_taken', '')} {row.get('notes', '')}".lower()
        if "weekly" in text and "review" in text:
            parsed = parse_date(row.get("run_date", ""))
            if parsed:
                weeks.add(parsed.isocalendar()[:2])
    return len(weeks)


def strict_quote_proof_rate(quotes: list[dict[str, str]]) -> float:
    if not quotes:
        return 0.0
    strict = [
        row for row in quotes
        if str(row.get("supplier_specific_quote", "")).upper() in {"TRUE", "YES", "1"}
        or str(row.get("quote_verification_status", "")).upper() in {"VERIFIED", "STRICT_VERIFIED"}
    ]
    return round(len(strict) / len(quotes) * 100, 2)


def source_yield_count(cases: list[dict[str, str]]) -> int:
    return len({row.get("case_id", "") for row in cases if row.get("case_id") and row.get("source_name")})


def resolve_state_file(config: dict[str, Any]) -> Path:
    configured = str(config.get("state_file") or DEFAULT_STATE_FILE)
    path = Path(configured).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def prepare_pilot(config: dict[str, Any], *, state_file: Path) -> dict[str, Any]:
    state = {
        "schema_version": "production_pilot_state.v1",
        "pilot_id": "PRODUCTION-PILOT-PENDING",
        "status": "PENDING_PREREQUISITES",
        "prepared_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "duration_days": int(config.get("duration_days") or 30),
        "production_external_authority_expanded": False,
        "start_prerequisites": config.get("start_prerequisites", []),
        "note": "Prepared only. Production pilot starts only after prerequisite gates and explicit owner authorization.",
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state


def activate_pilot(config: dict[str, Any], *, start_date: dt.date, state_file: Path) -> dict[str, Any]:
    duration_days = int(config.get("duration_days") or 30)
    state = {
        "schema_version": "production_pilot_state.v1",
        "pilot_id": f"PROD-{start_date.strftime('%Y%m%d')}",
        "status": "ACTIVE",
        "activated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "start_date": start_date.isoformat(),
        "planned_end_date": (start_date + dt.timedelta(days=duration_days - 1)).isoformat(),
        "duration_days": duration_days,
        "production_external_authority_expanded": False,
        "start_prerequisites": config.get("start_prerequisites", []),
        "note": "Production pilot measurement active. External authority remains unchanged unless separate approval gates authorize specific actions.",
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state


def build_not_started_report(*, config: dict[str, Any], end_date: dt.date, state: dict[str, Any]) -> dict[str, Any]:
    duration_days = int(config.get("duration_days") or 30)
    status = str(state.get("status") or "NOT_STARTED")
    blocker = "production pilot not activated"
    if status == "PENDING_PREREQUISITES":
        blocker = "production pilot pending prerequisite gates"
    return {
        "schema_version": "production_pilot_report.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "window": {"start": None, "end": end_date.isoformat(), "days": 0, "configured_days": duration_days, "planned_end": None},
        "pilot_state": state,
        "production_external_authority_expanded": False,
        "metrics": {
            "internal_automation_coverage_pct": 0.0,
            "owner_time_minutes": 0.0,
            "qualified_opportunity_throughput": 0,
            "strict_quote_proof_rate_pct": 0.0,
            "reply_or_rfq_conversion_count": 0,
            "source_yield_count": 0,
            "task_success_rate_pct": 0.0,
            "policy_violation_count": 0,
            "total_cost_usd": 0.0,
            "forecast_outcome_maturity_count": len(load_csv(DATA_DIR / "case_outcomes.csv")),
            "weekly_owner_review_count": 0,
            "duplicate_external_action_count": 0,
        },
        "blockers": [blocker],
        "next_action": "Complete TASK-092 and TASK-093, then explicitly activate the 30-day production pilot after owner authorization.",
    }


def build_report(*, config: dict[str, Any], end_date: dt.date, state: dict[str, Any] | None = None) -> dict[str, Any]:
    days = int(config.get("duration_days") or 30)
    state = state or {}
    start = parse_date(str(state.get("start_date", ""))) if state else None
    if not start:
        return build_not_started_report(config=config, end_date=end_date, state=state)
    days_elapsed = (end_date - start).days + 1
    run_rows = [row for row in load_csv(DATA_DIR / "agent_run_log.csv") if in_window(row.get("run_date", ""), start, end_date)]
    eval_rows = [row for row in load_csv(DATA_DIR / "agent_evaluations.csv") if in_window(row.get("evaluated_at", ""), start, end_date)]
    case_rows = [row for row in load_csv(DATA_DIR / "master_cases.csv") if in_window(row.get("created_at", "") or row.get("updated_at", ""), start, end_date)]
    quote_rows = [row for row in load_csv(DATA_DIR / "quote_master.csv") if in_window(row.get("created_at", "") or row.get("updated_at", ""), start, end_date)]
    communication_rows = [row for row in load_csv(DATA_DIR / "communication_log.csv") if in_window(row.get("occurred_at", "") or row.get("created_at", ""), start, end_date)]
    run_summary = summarize_run_log(run_rows)
    eval_summary = summarize_evaluations(eval_rows)
    reviews = weekly_review_count(run_rows)
    policy_violations = eval_summary["policy_violation_count"]
    duplicate_external_actions = max(0, run_summary["external_action_marker_count"] - len(communication_rows))
    pass_criteria = config.get("pass_criteria") if isinstance(config.get("pass_criteria"), dict) else {}
    blockers = []
    if reviews < int(pass_criteria.get("weekly_owner_reviews_min", 4)):
        blockers.append("weekly owner review count below threshold")
    if policy_violations > int(pass_criteria.get("policy_violation_count", 0)):
        blockers.append("policy violation detected")
    if duplicate_external_actions > int(pass_criteria.get("duplicate_external_action_count", 0)):
        blockers.append("possible duplicate external action markers detected")
    if run_summary["task_success_rate"] < safe_float(pass_criteria.get("task_success_rate_pct_min"), 90):
        blockers.append("task success rate below threshold")
    if blockers:
        status = "IN_PROGRESS_BLOCKED"
    elif days_elapsed < days:
        status = "IN_PROGRESS"
    elif run_rows:
        status = "PASS"
    else:
        status = "NO_DATA"
    return {
        "schema_version": "production_pilot_report.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "window": {
            "start": start.isoformat(),
            "end": end_date.isoformat(),
            "days": days_elapsed,
            "configured_days": days,
            "planned_end": (start + dt.timedelta(days=days - 1)).isoformat(),
        },
        "pilot_state": state,
        "production_external_authority_expanded": False,
        "metrics": {
            "internal_automation_coverage_pct": 0.0,
            "owner_time_minutes": run_summary["owner_time_minutes_estimate"],
            "qualified_opportunity_throughput": len([row for row in case_rows if str(row.get("status", "")).upper() not in {"REJECTED", "ARCHIVED"}]),
            "strict_quote_proof_rate_pct": strict_quote_proof_rate(quote_rows),
            "reply_or_rfq_conversion_count": len(communication_rows),
            "source_yield_count": source_yield_count(case_rows),
            "task_success_rate_pct": run_summary["task_success_rate"],
            "policy_violation_count": policy_violations,
            "total_cost_usd": eval_summary["total_cost_usd"],
            "forecast_outcome_maturity_count": len(load_csv(DATA_DIR / "case_outcomes.csv")),
            "weekly_owner_review_count": reviews,
            "duplicate_external_action_count": duplicate_external_actions,
        },
        "blockers": blockers,
        "next_action": "Continue pilot and complete weekly owner reviews before production-readiness signoff.",
    }


def write_report(report: dict[str, Any], output_dir: Path = DEFAULT_OUTPUT_DIR) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    label = report["window"]["end"].replace("-", "")
    path = output_dir / f"production_pilot_{label}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"))
    parser.add_argument("--prepare", action="store_true", help="Create a pending production-pilot state without starting measurement.")
    parser.add_argument("--activate", action="store_true", help="Activate measurement from --date. Use only after prerequisite gates and owner authorization.")
    parser.add_argument("--ignore-state", action="store_true", help="Use legacy rolling-window behavior for diagnostics.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    end = parse_date(args.date)
    if end is None:
        raise SystemExit(f"Invalid --date: {args.date}")
    config = load_yaml()
    state_file = resolve_state_file(config)
    if args.prepare:
        state = prepare_pilot(config, state_file=state_file)
        payload = {
            "status": state["status"],
            "state_file": str(state_file),
            "pilot_id": state["pilot_id"],
            "production_external_authority_expanded": False,
        }
        print(json.dumps(payload, indent=2) if args.json else f"Production pilot prepared: {state_file}")
        return 0
    if args.activate:
        state = activate_pilot(config, start_date=end, state_file=state_file)
        payload = {
            "status": "ACTIVATED",
            "state_file": str(state_file),
            "pilot_id": state["pilot_id"],
            "start_date": state["start_date"],
            "planned_end_date": state["planned_end_date"],
            "production_external_authority_expanded": False,
        }
        print(json.dumps(payload, indent=2) if args.json else f"Production pilot activated: {state_file}")
        return 0
    state = {} if args.ignore_state else load_json(state_file)
    report = build_report(config=config, end_date=end, state=state)
    path = write_report(report)
    payload = {"status": report["status"], "report": path, "blockers": report["blockers"]}
    print(json.dumps(payload, indent=2) if args.json else f"Production pilot {report['status']}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
