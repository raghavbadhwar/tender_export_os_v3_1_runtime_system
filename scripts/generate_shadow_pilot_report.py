#!/usr/bin/env python3
"""Generate a 14-day shadow pilot measurement report without external actions."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import statistics
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "shadow_pilot.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "shadow_pilot"
DEFAULT_STATE_FILE = DATA_DIR / "shadow_pilot_state.json"
EXTERNAL_ACTION_MARKERS = {
    "send",
    "sent",
    "submit",
    "submitted",
    "upload",
    "uploaded",
    "payment",
    "pay",
    "dsc",
    "esign",
    "purchase order",
    "po ",
    "final price",
    "delivery commitment",
}
SUCCESS_STATUSES = {"SUCCESS", "SUCCESS_WITH_WARNINGS", "PASS", "COMPLETED"}
EXTERNAL_ACTION_PATTERNS = [
    re.compile(rf"(?<![\w-]){re.escape(marker.strip())}(?![\w-])")
    for marker in EXTERNAL_ACTION_MARKERS
    if marker.strip()
]
NEGATED_ACTION_CLAUSE = re.compile(r"\bno\b[^.;\n]*\baction\b")


def parse_date(value: str) -> dt.date | None:
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(value[:10] if fmt == "%Y-%m-%d" else value[:8], fmt).date()
        except ValueError:
            continue
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def iso_date(value: dt.date) -> str:
    return value.isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
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


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def in_window(value: str, start: dt.date, end: dt.date) -> bool:
    parsed = parse_date(value)
    return bool(parsed and start <= parsed <= end)


def has_external_marker(row: dict[str, str]) -> bool:
    text = " ".join(str(row.get(key, "")) for key in ("actions_taken", "notes", "actual_result")).lower()
    text = NEGATED_ACTION_CLAUSE.sub(" ", text)
    return any(pattern.search(text) for pattern in EXTERNAL_ACTION_PATTERNS)


def summarize_run_log(rows: list[dict[str, str]]) -> dict[str, Any]:
    total = len(rows)
    successes = sum(1 for row in rows if str(row.get("status", "")).upper() in SUCCESS_STATUSES)
    runtimes = [safe_float(row.get("runtime_seconds")) for row in rows if str(row.get("runtime_seconds", "")).strip()]
    external_markers = [row for row in rows if has_external_marker(row)]
    owner_time_minutes = sum(
        safe_float(row.get("runtime_seconds")) / 60.0
        for row in rows
        if "owner" in str(row.get("agent_name", "")).lower()
        or "approval" in str(row.get("actions_taken", "")).lower()
    )
    return {
        "run_count": total,
        "success_count": successes,
        "task_success_rate": round((successes / total) * 100, 2) if total else 0.0,
        "cases_processed": int(sum(safe_float(row.get("cases_processed")) for row in rows)),
        "cases_created": int(sum(safe_float(row.get("cases_created")) for row in rows)),
        "cases_updated": int(sum(safe_float(row.get("cases_updated")) for row in rows)),
        "errors": int(sum(safe_float(row.get("errors")) for row in rows)),
        "warnings": int(sum(safe_float(row.get("warnings")) for row in rows)),
        "median_task_latency_seconds": round(statistics.median(runtimes), 2) if runtimes else 0.0,
        "total_runtime_seconds": round(sum(runtimes), 2),
        "owner_time_minutes_estimate": round(owner_time_minutes, 2),
        "external_action_marker_count": len(external_markers),
        "external_action_marker_run_ids": [row.get("run_id", "") for row in external_markers if row.get("run_id")],
    }


def summarize_evaluations(rows: list[dict[str, str]]) -> dict[str, Any]:
    total = len(rows)
    passed = sum(1 for row in rows if str(row.get("status", "")).upper() == "PASS")
    evidence = [safe_float(row.get("evidence_completeness_pct")) for row in rows if str(row.get("evidence_completeness_pct", "")).strip()]
    latency = [safe_float(row.get("latency_ms")) for row in rows if str(row.get("latency_ms", "")).strip()]
    policy_failures = [row for row in rows if str(row.get("policy_compliance", "")).upper() == "FAIL"]
    return {
        "evaluation_count": total,
        "pass_count": passed,
        "evaluation_pass_rate": round((passed / total) * 100, 2) if total else 0.0,
        "average_evidence_completeness_pct": round(sum(evidence) / len(evidence), 2) if evidence else 0.0,
        "policy_violation_count": len(policy_failures),
        "policy_violation_ids": [row.get("evaluation_id", "") for row in policy_failures if row.get("evaluation_id")],
        "total_cost_usd": round(sum(safe_float(row.get("cost_usd")) for row in rows), 6),
        "median_model_latency_ms": round(statistics.median(latency), 2) if latency else 0.0,
    }


def summarize_cases(rows: list[dict[str, str]]) -> dict[str, Any]:
    qualified_statuses = {
        "WATCHLIST",
        "DEEP_READ",
        "SUPPLIER_SEARCH",
        "PRICING_READY",
        "ARTIFACT_PRODUCTION",
        "APPROVAL_REQUIRED",
    }
    qualified = [row for row in rows if str(row.get("status", "")).upper() in qualified_statuses]
    return {
        "case_count": len(rows),
        "qualified_opportunity_count": len(qualified),
        "qualified_case_ids": [row.get("case_id", "") for row in qualified if row.get("case_id")],
    }


def profile_names_from_registry(registry: dict[str, Any]) -> list[str]:
    owner = str(registry.get("owner_profile") or "").strip()
    specialists = [str(value).strip() for value in registry.get("specialist_profiles") or [] if str(value).strip()]
    return list(dict.fromkeys(([owner] if owner else []) + specialists))


def expected_daily_profiles(config: dict[str, Any]) -> list[str]:
    telemetry = config.get("daily_profile_telemetry") if isinstance(config.get("daily_profile_telemetry"), dict) else {}
    if telemetry.get("required") is not True:
        return []
    configured = telemetry.get("expected_profiles")
    if isinstance(configured, list):
        return list(dict.fromkeys(str(value).strip() for value in configured if str(value).strip()))
    source = Path(str(config.get("profiles_source") or "config/hermes_specialist_profiles.yaml"))
    source = source if source.is_absolute() else PROJECT_ROOT / source
    try:
        return profile_names_from_registry(load_yaml(source))
    except (OSError, ValueError, yaml.YAMLError):
        return []


def summarize_daily_profile_telemetry(
    *,
    config: dict[str, Any],
    run_rows: list[dict[str, str]],
    evaluation_rows: list[dict[str, str]],
    start: dt.date,
    end: dt.date,
) -> dict[str, Any]:
    telemetry = config.get("daily_profile_telemetry") if isinstance(config.get("daily_profile_telemetry"), dict) else {}
    expected_profiles = expected_daily_profiles(config)
    if not expected_profiles:
        return {
            "required": telemetry.get("required") is True,
            "status": "NOT_CONFIGURED",
            "expected_profiles": [],
            "observed_day_count": 0,
            "complete_day_count": 0,
            "missing_by_day": {},
        }

    probe_trigger = str(telemetry.get("probe_trigger_type") or "shadow_profile_probe")
    evaluation_scenario = str(telemetry.get("evaluation_scenario_id") or "shadow_profile_probe")
    expected_set = set(expected_profiles)
    days = [start + dt.timedelta(days=offset) for offset in range((end - start).days + 1)]
    probes_by_day: dict[str, set[str]] = {iso_date(day): set() for day in days}
    evaluations_by_day: dict[str, set[str]] = {iso_date(day): set() for day in days}
    for row in run_rows:
        date = parse_date(row.get("run_date", ""))
        if date is None or not (start <= date <= end):
            continue
        if str(row.get("trigger_type") or "").strip() != probe_trigger:
            continue
        profile = str(row.get("agent_name") or "").strip()
        if profile in expected_set:
            probes_by_day[iso_date(date)].add(profile)
    for row in evaluation_rows:
        date = parse_date(row.get("evaluated_at", ""))
        if date is None or not (start <= date <= end):
            continue
        if str(row.get("scenario_id") or "").strip() != evaluation_scenario:
            continue
        profile = str(row.get("profile") or "").strip()
        if profile in expected_set:
            evaluations_by_day[iso_date(date)].add(profile)

    missing_by_day: dict[str, dict[str, list[str]]] = {}
    complete_day_count = 0
    for day in days:
        label = iso_date(day)
        missing_probes = sorted(expected_set - probes_by_day[label])
        missing_evaluations = sorted(expected_set - evaluations_by_day[label])
        if not missing_probes and not missing_evaluations:
            complete_day_count += 1
        else:
            missing_by_day[label] = {"probes": missing_probes, "evaluations": missing_evaluations}
    return {
        "required": True,
        "status": "PASS" if not missing_by_day else "INCOMPLETE",
        "expected_profiles": expected_profiles,
        "probe_trigger_type": probe_trigger,
        "evaluation_scenario_id": evaluation_scenario,
        "observed_day_count": len(days),
        "complete_day_count": complete_day_count,
        "missing_by_day": missing_by_day,
    }
def compare(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    keys = sorted(set(current) & set(baseline))
    comparison: dict[str, Any] = {}
    for key in keys:
        if isinstance(current.get(key), (int, float)) and isinstance(baseline.get(key), (int, float)):
            comparison[key] = {
                "current": current[key],
                "baseline": baseline[key],
                "delta": round(float(current[key]) - float(baseline[key]), 4),
            }
    return comparison


def build_report(
    *,
    config: dict[str, Any],
    run_log: list[dict[str, str]],
    evaluations: list[dict[str, str]],
    cases: list[dict[str, str]],
    end_date: dt.date,
    days: int,
    start_date: dt.date | None = None,
    pilot_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    configured_days = int(config.get("duration_days") or 14)
    if start_date is not None:
        start = start_date
        days = (end_date - start).days + 1
    else:
        start = end_date - dt.timedelta(days=days - 1)
    baseline_end = start - dt.timedelta(days=1)
    baseline_start = baseline_end - dt.timedelta(days=int(config.get("baseline_days") or days) + -1)

    current_runs = [row for row in run_log if in_window(row.get("run_date", ""), start, end_date)]
    baseline_runs = [row for row in run_log if in_window(row.get("run_date", ""), baseline_start, baseline_end)]
    current_evals = [row for row in evaluations if in_window(row.get("evaluated_at", ""), start, end_date)]
    baseline_evals = [row for row in evaluations if in_window(row.get("evaluated_at", ""), baseline_start, baseline_end)]
    current_cases = [row for row in cases if in_window(row.get("created_at", "") or row.get("updated_at", ""), start, end_date)]
    baseline_cases = [row for row in cases if in_window(row.get("created_at", "") or row.get("updated_at", ""), baseline_start, baseline_end)]

    run_summary = summarize_run_log(current_runs)
    eval_summary = summarize_evaluations(current_evals)
    case_summary = summarize_cases(current_cases)
    baseline_run_summary = summarize_run_log(baseline_runs)
    baseline_eval_summary = summarize_evaluations(baseline_evals)
    baseline_case_summary = summarize_cases(baseline_cases)

    telemetry_end = min(end_date, start + dt.timedelta(days=configured_days - 1))
    daily_profile_telemetry = summarize_daily_profile_telemetry(
        config=config,
        run_rows=current_runs,
        evaluation_rows=current_evals,
        start=start,
        end=telemetry_end,
    ) if start_date is not None else {"required": False, "status": "NOT_ACTIVE"}

    blockers: list[str] = []
    warnings: list[str] = []
    if start_date is None and days < configured_days:
        blockers.append("pilot window is shorter than configured duration")
    if run_summary["external_action_marker_count"]:
        blockers.append("run log contains external-action markers inside the shadow window")
    if eval_summary["policy_violation_count"]:
        blockers.append("agent evaluations contain policy violations inside the shadow window")
    success_metrics = config.get("success_metrics") if isinstance(config.get("success_metrics"), dict) else {}
    metric_checks = [
        (
            "task_success_rate",
            run_summary["task_success_rate"],
            safe_float((success_metrics.get("task_success_rate") or {}).get("minimum_shadow_target"), 0),
            "minimum",
        ),
        (
            "evidence_completeness_pct",
            eval_summary["average_evidence_completeness_pct"],
            safe_float((success_metrics.get("evidence_completeness_pct") or {}).get("minimum_shadow_target"), 0),
            "minimum",
        ),
        (
            "policy_violation_count",
            eval_summary["policy_violation_count"],
            safe_float((success_metrics.get("policy_violation_count") or {}).get("maximum_shadow_target"), 0),
            "maximum",
        ),
    ]
    metric_results: list[dict[str, Any]] = []
    pilot_complete = start_date is None or days >= configured_days
    if daily_profile_telemetry.get("required") and daily_profile_telemetry.get("status") != "PASS":
        missing_days = sorted((daily_profile_telemetry.get("missing_by_day") or {}).keys())
        message = "daily profile probe/evaluation coverage is incomplete: " + ", ".join(missing_days)
        if pilot_complete:
            blockers.append(message)
        else:
            warnings.append(message)
    for metric, current_value, target, direction in metric_checks:
        if target <= 0 and direction == "minimum":
            continue
        passed = current_value >= target if direction == "minimum" else current_value <= target
        result = {
            "metric": metric,
            "current": current_value,
            "target": target,
            "direction": direction,
            "status": "PASS" if passed else ("AT_RISK" if not pilot_complete else "FAIL"),
        }
        metric_results.append(result)
        if not passed:
            message = f"{metric} {current_value} does not meet {direction} target {target}"
            if pilot_complete:
                blockers.append(message)
            else:
                warnings.append(message)

    evidence_ready = bool(current_runs or current_evals or current_cases)
    if blockers:
        status = "BLOCKED"
    elif start_date is not None and days < configured_days:
        status = "IN_PROGRESS"
    elif evidence_ready:
        status = "PASS"
    else:
        status = "NO_DATA"
    planned_end = start + dt.timedelta(days=configured_days - 1)
    return {
        "schema_version": "shadow_pilot_report.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "mode": config.get("mode", "SHADOW_ONLY"),
        "status": status,
        "pilot_window": {
            "start": iso_date(start),
            "end": iso_date(end_date),
            "days": days,
            "configured_days": configured_days,
            "planned_end": iso_date(planned_end),
        },
        "baseline_window": {"start": iso_date(baseline_start), "end": iso_date(baseline_end), "days": int(config.get("baseline_days") or days)},
        "pilot_state": pilot_state or {},
        "daily_profile_telemetry": daily_profile_telemetry,
        "production_routing_enabled": False,
        "external_actions_authorized": False,
        "allowed_internal_actions": config.get("allowed_internal_actions", []),
        "prohibited_external_actions": config.get("prohibited_external_actions", []),
        "current": {
            "run_log": run_summary,
            "evaluations": eval_summary,
            "cases": case_summary,
        },
        "baseline": {
            "run_log": baseline_run_summary,
            "evaluations": baseline_eval_summary,
            "cases": baseline_case_summary,
        },
        "comparison": {
            "run_log": compare(run_summary, baseline_run_summary),
            "evaluations": compare(eval_summary, baseline_eval_summary),
            "cases": compare(case_summary, baseline_case_summary),
        },
        "metric_results": metric_results,
        "blockers": blockers,
        "warnings": warnings,
        "next_gate": "TASK-093 after a completed shadow pilot and owner review",
        "safety_note": "Measurement only. This report does not send, submit, upload, pay, use DSC, contact buyers/suppliers, or enable production routing.",
    }


def resolve_state_file(config: dict[str, Any]) -> Path:
    configured = str(config.get("state_file") or DEFAULT_STATE_FILE)
    path = Path(configured).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def activate_pilot(config: dict[str, Any], *, start_date: dt.date, state_file: Path) -> dict[str, Any]:
    duration_days = int(config.get("duration_days") or 14)
    activated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    state = {
        "schema_version": "shadow_pilot_state.v1",
        "pilot_id": f"SHADOW-{start_date.strftime('%Y%m%d')}",
        "activated_at": activated_at,
        "start_date": iso_date(start_date),
        "planned_end_date": iso_date(start_date + dt.timedelta(days=duration_days - 1)),
        "duration_days": duration_days,
        "mode": config.get("mode", "SHADOW_ONLY"),
        "production_routing_enabled": False,
        "external_actions_authorized": False,
        "allowed_internal_actions": config.get("allowed_internal_actions", []),
        "prohibited_external_actions": config.get("prohibited_external_actions", []),
        "activation_note": "Explicit shadow-pilot activation. Historical runs before start_date are excluded from pilot pass/fail.",
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def render_html(report: dict[str, Any]) -> str:
    current = report["current"]
    telemetry = report.get("daily_profile_telemetry") if isinstance(report.get("daily_profile_telemetry"), dict) else {}
    lines = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>Shadow Pilot Report</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;line-height:1.45}table{border-collapse:collapse;width:100%;margin:16px 0}td,th{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f6f6f6}.blocked{color:#9a3412}.pass{color:#166534}.muted{color:#666}</style>",
        "</head><body>",
        "<h1>Tender Export OS Shadow Pilot Report</h1>",
        f"<p>Status: <strong class='{esc(str(report['status']).lower())}'>{esc(report['status'])}</strong></p>",
        f"<p>Window: {esc(report['pilot_window']['start'])} to {esc(report['pilot_window']['end'])} ({esc(report['pilot_window']['days'])} days)</p>",
        f"<p>Production routing enabled: <strong>{esc(report['production_routing_enabled'])}</strong></p>",
        "<h2>Current Window Metrics</h2>",
        "<table><tr><th>Area</th><th>Metric</th><th>Value</th></tr>",
    ]
    for area, metrics in current.items():
        for key, value in metrics.items():
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            lines.append(f"<tr><td>{esc(area)}</td><td>{esc(key)}</td><td>{esc(value)}</td></tr>")
    lines.append("</table>")
    if telemetry.get("required") is True:
        lines.extend(
            [
                "<h2>Daily Profile Telemetry</h2>",
                "<table><tr><th>Metric</th><th>Value</th></tr>",
                f"<tr><td>Status</td><td>{esc(telemetry.get('status'))}</td></tr>",
                f"<tr><td>Expected profiles</td><td>{esc(len(telemetry.get('expected_profiles') or []))}</td></tr>",
                f"<tr><td>Complete calendar days</td><td>{esc(telemetry.get('complete_day_count'))} / {esc(telemetry.get('observed_day_count'))}</td></tr>",
                "</table>",
            ]
        )
        missing = telemetry.get("missing_by_day") if isinstance(telemetry.get("missing_by_day"), dict) else {}
        if missing:
            lines.append("<p>Missing probe/evaluation coverage: " + esc(", ".join(sorted(missing))) + "</p>")
    lines.append("<h2>Blockers</h2>")
    if report["blockers"]:
        lines.append("<ul>")
        for blocker in report["blockers"]:
            lines.append(f"<li>{esc(blocker)}</li>")
        lines.append("</ul>")
    else:
        lines.append("<p>No blockers detected in the measured window.</p>")
    if report.get("warnings"):
        lines.append("<h2>In-Progress Warnings</h2><ul>")
        for warning in report["warnings"]:
            lines.append(f"<li>{esc(warning)}</li>")
        lines.append("</ul>")
    lines.append(f"<p class='muted'>{esc(report['safety_note'])}</p>")
    lines.append("</body></html>")
    return "\n".join(lines)


def write_report(report: dict[str, Any], output_dir: Path, date_label: str) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"shadow_pilot_{date_label}.json"
    html_path = output_dir / f"shadow_pilot_{date_label}.html"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    return {"json": str(json_path), "html": str(html_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--days", type=int, default=None)
    parser.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--activate", action="store_true", help="Create or replace the explicit shadow-pilot activation state file for --date.")
    parser.add_argument("--ignore-state", action="store_true", help="Use the legacy rolling window instead of the activation state file.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    config = load_yaml(Path(args.config).expanduser())
    end_date = parse_date(args.date)
    if end_date is None:
        raise SystemExit(f"Invalid --date: {args.date}")
    state_file = resolve_state_file(config)
    if args.activate:
        state = activate_pilot(config, start_date=end_date, state_file=state_file)
        payload = {
            "status": "ACTIVATED",
            "state_file": str(state_file),
            "pilot_id": state["pilot_id"],
            "start_date": state["start_date"],
            "planned_end_date": state["planned_end_date"],
            "production_routing_enabled": False,
            "external_actions_authorized": False,
        }
        print(json.dumps(payload, indent=2) if args.json else f"Shadow pilot activated: {state_file}")
        return 0
    pilot_state = {} if args.ignore_state else load_json(state_file)
    state_start = parse_date(str(pilot_state.get("start_date", ""))) if pilot_state else None
    days = int(args.days or config.get("duration_days") or 14)
    report = build_report(
        config=config,
        run_log=load_csv(DATA_DIR / "agent_run_log.csv"),
        evaluations=load_csv(DATA_DIR / "agent_evaluations.csv"),
        cases=load_csv(DATA_DIR / "master_cases.csv"),
        end_date=end_date,
        days=days,
        start_date=state_start,
        pilot_state=pilot_state,
    )
    paths = write_report(report, Path(args.output_dir).expanduser(), end_date.strftime("%Y%m%d"))
    payload = {
        "status": report["status"],
        "window": report["pilot_window"],
        "production_routing_enabled": False,
        "external_actions_authorized": False,
        "json": paths["json"],
        "html": paths["html"],
    }
    print(json.dumps(payload, indent=2) if args.json else f"Shadow pilot {report['status']}: {paths['html']}")
    return 0 if report["status"] in {"PASS", "NO_DATA", "IN_PROGRESS", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
