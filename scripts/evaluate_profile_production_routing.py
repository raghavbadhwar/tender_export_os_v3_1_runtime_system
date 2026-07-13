#!/usr/bin/env python3
"""Evaluate profile eligibility for production routing without enabling it."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import html
import json
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "profile_production_routing_gate.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profile_routing_readiness"
SUCCESS_STATUSES = {"SUCCESS", "SUCCESS_WITH_WARNINGS", "PASS", "COMPLETED"}


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def latest_shadow_report(config: dict[str, Any]) -> tuple[Path | None, dict[str, Any]]:
    pattern = PROJECT_ROOT / str(config.get("shadow_pilot_report_glob") or "")
    matches = sorted(glob.glob(str(pattern)))
    if not matches:
        return None, {}
    path = Path(matches[-1])
    return path, load_json(path)


def latest_json_report(pattern_value: str) -> tuple[Path | None, dict[str, Any]]:
    pattern = PROJECT_ROOT / str(pattern_value or "")
    matches = sorted(glob.glob(str(pattern)))
    if not matches:
        return None, {}
    path = Path(matches[-1])
    return path, load_json(path)


def canary_by_profile(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = report.get("validations") if isinstance(report.get("validations"), list) else []
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        profile = str(row.get("profile") or "").strip()
        if not profile:
            continue
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        result[profile] = {
            "ok": row.get("ok") is True,
            "task_id": row.get("task_id"),
            "task_status": row.get("task_status"),
            "external_actions_executed": payload.get("external_actions_executed"),
            "approval_required": payload.get("approval_required"),
            "evidence": payload.get("evidence") if isinstance(payload.get("evidence"), list) else [],
            "errors": row.get("errors") if isinstance(row.get("errors"), list) else [],
        }
    return result


def behavioral_reports_by_profile(pattern_value: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    pattern = PROJECT_ROOT / str(pattern_value or "")
    for raw_path in sorted(glob.glob(str(pattern), recursive=True)):
        path = Path(raw_path)
        report = load_json(path)
        profile = str(report.get("profile") or "").strip()
        if not profile:
            continue
        previous = result.get(profile)
        previous_path = Path(previous["path"]) if previous and previous.get("path") else None
        if previous_path and previous_path.stat().st_mtime > path.stat().st_mtime:
            continue
        result[profile] = {
            "path": str(path),
            "status": report.get("status"),
            "case_attempts": report.get("case_attempts"),
            "case_passes": report.get("case_passes"),
            "case_pass_rate": report.get("case_pass_rate"),
            "repeats": report.get("repeats"),
            "scenario_count": report.get("scenario_count"),
        }
    return result


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _row_date(row: dict[str, str]) -> dt.date | None:
    raw = str(row.get("run_date") or "").strip()
    if not raw:
        return None
    try:
        return dt.date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _date_from_shadow_report(report: dict[str, Any], *keys: tuple[str, str]) -> dt.date | None:
    for parent_key, child_key in keys:
        parent = report.get(parent_key) if isinstance(report.get(parent_key), dict) else {}
        raw = str(parent.get(child_key) or "").strip()
        if not raw:
            continue
        try:
            return dt.date.fromisoformat(raw[:10])
        except ValueError:
            continue
    return None


def scope_run_rows(
    rows: list[dict[str, str]],
    *,
    config: dict[str, Any],
    shadow_report: dict[str, Any],
    today: dt.date | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Return run rows relevant to the current production-routing measurement.

    Historical agent_run_log rows include baseline experiments and manual repair
    work. TASK-093 should measure the explicitly activated clean shadow pilot,
    so the default canonical config scopes run metrics to the pilot window.
    """
    scope = str(config.get("run_log_scope") or "all_history").strip() or "all_history"
    meta: dict[str, Any] = {
        "scope": scope,
        "input_run_count": len(rows),
        "filtered_run_count": len(rows),
    }
    if scope != "shadow_pilot_window":
        return rows, meta

    start = _date_from_shadow_report(
        shadow_report,
        ("pilot_state", "start_date"),
        ("pilot_window", "start"),
    )
    planned_end = _date_from_shadow_report(
        shadow_report,
        ("pilot_state", "planned_end_date"),
        ("pilot_window", "planned_end"),
        ("pilot_window", "end"),
    )
    current_end = _date_from_shadow_report(shadow_report, ("pilot_window", "end")) or today or dt.datetime.now(dt.timezone.utc).date()
    status = str(shadow_report.get("status") or "").upper()
    end = planned_end if status == "PASS" and planned_end else current_end

    meta.update(
        {
            "pilot_start_date": start.isoformat() if start else "",
            "pilot_end_date": end.isoformat() if end else "",
            "shadow_pilot_status": shadow_report.get("status") or "MISSING",
        }
    )
    if start is None or end is None:
        meta["filtered_run_count"] = 0
        meta["warning"] = "shadow pilot window missing; no run rows counted"
        return [], meta

    scoped = []
    for row in rows:
        run_date = _row_date(row)
        if run_date and start <= run_date <= end:
            scoped.append(row)
    meta["filtered_run_count"] = len(scoped)
    return scoped, meta


def profile_list(registry: dict[str, Any]) -> list[str]:
    owner = str(registry.get("owner_profile") or "").strip()
    specialists = [str(value).strip() for value in registry.get("specialist_profiles") or [] if str(value).strip()]
    return list(dict.fromkeys(([owner] if owner else []) + specialists))


def summarize_runs(profile: str, aliases: list[str], rows: list[dict[str, str]]) -> dict[str, Any]:
    alias_set = {value.lower() for value in aliases + [profile]}
    profile_rows = [
        row for row in rows
        if str(row.get("agent_name", "")).strip().lower() in alias_set
    ]
    total = len(profile_rows)
    successes = sum(1 for row in profile_rows if str(row.get("status", "")).upper() in SUCCESS_STATUSES)
    return {
        "run_count": total,
        "success_count": successes,
        "task_success_rate_pct": round((successes / total) * 100, 2) if total else 0.0,
    }


def summarize_evals(profile: str, rows: list[dict[str, str]], behavioral_report: dict[str, Any] | None = None) -> dict[str, Any]:
    profile_rows = [row for row in rows if str(row.get("profile", "")).strip() == profile]
    critical_rows = [
        row for row in profile_rows
        if str(row.get("scenario_type", "")).upper() == "CRITICAL"
        or str(row.get("scenario_id", "")).lower().startswith("critical")
        or str(row.get("notes", "")).lower().find("critical") >= 0
    ]
    if not critical_rows:
        critical_rows = profile_rows
    critical_passes = sum(1 for row in critical_rows if str(row.get("status", "")).upper() == "PASS")
    evidence_values = [
        safe_float(row.get("evidence_completeness_pct"))
        for row in profile_rows
        if str(row.get("evidence_completeness_pct", "")).strip()
    ]
    policy_violations = [
        row for row in profile_rows if str(row.get("policy_compliance", "")).upper() == "FAIL"
    ]
    summary = {
        "evaluation_count": len(profile_rows),
        "critical_evaluation_count": len(critical_rows),
        "critical_eval_pass_rate_pct": round((critical_passes / len(critical_rows)) * 100, 2) if critical_rows else 0.0,
        "average_evidence_completeness_pct": round(sum(evidence_values) / len(evidence_values), 2) if evidence_values else 0.0,
        "policy_violation_count": len(policy_violations),
        "source": "agent_evaluations_csv",
    }
    behavioral_report = behavioral_report or {}
    if behavioral_report:
        attempts = int(safe_float(behavioral_report.get("case_attempts"), 0))
        pass_rate = safe_float(behavioral_report.get("case_pass_rate"), 0.0) * 100
        if attempts > summary["critical_evaluation_count"]:
            summary.update(
                {
                    "evaluation_count": attempts,
                    "critical_evaluation_count": attempts,
                    "critical_eval_pass_rate_pct": round(pass_rate, 2),
                    "average_evidence_completeness_pct": 100.0 if behavioral_report.get("status") == "PASS" else 0.0,
                    "policy_violation_count": 0,
                    "source": "hermes_behavioral_eval_report",
                    "behavioral_report_path": behavioral_report.get("path", ""),
                    "behavioral_report_status": behavioral_report.get("status"),
                }
            )
    return summary


def evaluate_profile(
    profile: str,
    *,
    aliases: list[str],
    run_rows: list[dict[str, str]],
    eval_rows: list[dict[str, str]],
    thresholds: dict[str, Any],
    shadow_status: str,
    canary: dict[str, Any] | None = None,
    behavioral_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runs = summarize_runs(profile, aliases, run_rows)
    evals = summarize_evals(profile, eval_rows, behavioral_report=behavioral_report)
    canary = canary or {}
    canary_ok = canary.get("ok") is True and canary.get("external_actions_executed") is False
    blockers: list[str] = []
    if shadow_status != thresholds.get("shadow_pilot_required_status", "PASS"):
        blockers.append(f"shadow pilot status is {shadow_status or 'MISSING'}")
    if evals["critical_evaluation_count"] == 0:
        blockers.append("missing critical/profile evaluation records")
    if runs["run_count"] == 0 and not canary_ok:
        blockers.append("missing profile run records")
    if evals["critical_eval_pass_rate_pct"] < safe_float(thresholds.get("critical_eval_pass_rate_pct"), 100):
        blockers.append("critical eval pass rate below threshold")
    if runs["run_count"] == 0 and canary_ok:
        blockers.append("missing shadow task run records beyond read-only canary")
    elif runs["task_success_rate_pct"] < safe_float(thresholds.get("task_success_rate_pct"), 90):
        blockers.append("task success rate below threshold")
    if evals["average_evidence_completeness_pct"] < safe_float(thresholds.get("evidence_completeness_pct"), 95):
        blockers.append("evidence completeness below threshold")
    if evals["policy_violation_count"] > int(safe_float(thresholds.get("policy_violation_count"), 0)):
        blockers.append("policy violation detected")
    eligible = not blockers
    return {
        "profile": profile,
        "eligible_for_production_routing": eligible,
        "recommended_routing_status": "ELIGIBLE_PENDING_OWNER_REVIEW" if eligible else "SHADOW",
        "production_routing_enabled": False,
        "run_metrics": runs,
        "canary_metrics": {
            "available": bool(canary),
            "ok": canary_ok,
            "task_id": canary.get("task_id"),
            "evidence": canary.get("evidence", []),
        },
        "evaluation_metrics": evals,
        "blockers": blockers,
    }


def build_report(
    *,
    config: dict[str, Any],
    registry: dict[str, Any],
    run_rows: list[dict[str, str]],
    eval_rows: list[dict[str, str]],
    shadow_report_path: Path | None,
    shadow_report: dict[str, Any],
    canary_report_path: Path | None = None,
    canary_report: dict[str, Any] | None = None,
    behavioral_reports: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    thresholds = config.get("thresholds") if isinstance(config.get("thresholds"), dict) else {}
    aliases = config.get("profile_run_log_aliases") if isinstance(config.get("profile_run_log_aliases"), dict) else {}
    shadow_status = str(shadow_report.get("status") or "")
    canaries = canary_by_profile(canary_report or {})
    behavioral_reports = behavioral_reports or {}
    scoped_run_rows, run_log_scope = scope_run_rows(
        run_rows,
        config=config,
        shadow_report=shadow_report,
    )
    rows = [
        evaluate_profile(
            profile,
            aliases=[str(value) for value in aliases.get(profile, [])],
            run_rows=scoped_run_rows,
            eval_rows=eval_rows,
            thresholds=thresholds,
            shadow_status=shadow_status,
            canary=canaries.get(profile),
            behavioral_report=behavioral_reports.get(profile),
        )
        for profile in profile_list(registry)
    ]
    eligible = [row for row in rows if row["eligible_for_production_routing"]]
    blocker_summary: dict[str, int] = {}
    for row in rows:
        for blocker in row["blockers"]:
            blocker_summary[blocker] = blocker_summary.get(blocker, 0) + 1
    blockers = [
        f"{reason} ({count} profile{'s' if count != 1 else ''})"
        for reason, count in sorted(blocker_summary.items())
    ]
    return {
        "schema_version": "profile_production_routing_readiness.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "mode": config.get("mode", "MEASURE_ONLY"),
        "status": "PASS" if rows and len(eligible) == len(rows) else "BLOCKED",
        "shadow_pilot_report": str(shadow_report_path) if shadow_report_path else "",
        "shadow_pilot_status": shadow_status or "MISSING",
        "specialist_canary_report": str(canary_report_path) if canary_report_path else "",
        "specialist_canary_status": (canary_report or {}).get("status") or "MISSING",
        "behavioral_eval_profile_count": len(behavioral_reports),
        "run_log_scope": run_log_scope,
        "thresholds": thresholds,
        "profile_count": len(rows),
        "eligible_profile_count": len(eligible),
        "blockers": blockers,
        "blocker_summary": blocker_summary,
        "production_routing_enabled": False,
        "owner_review_required_before_enable": bool((config.get("defaults") or {}).get("owner_review_required_before_enable", True)),
        "profiles": rows,
        "safety_note": "Readiness measurement only. This script does not mutate Kanban routing, enable profiles, contact anyone, submit, upload, pay, use DSC, or make final commercial/compliance commitments.",
    }


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def render_html(report: dict[str, Any]) -> str:
    lines = [
        "<!doctype html><html><head><meta charset='utf-8'><title>Profile Routing Readiness</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;line-height:1.45}table{border-collapse:collapse;width:100%;margin:16px 0}td,th{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f6f6f6}.blocked{color:#9a3412}.eligible{color:#166534}.muted{color:#666}</style>",
        "</head><body><h1>Profile Production Routing Readiness</h1>",
        f"<p>Status: <strong>{esc(report['status'])}</strong></p>",
        f"<p>Shadow pilot status: <strong>{esc(report['shadow_pilot_status'])}</strong></p>",
        f"<p>Production routing enabled: <strong>{esc(report['production_routing_enabled'])}</strong></p>",
        f"<p>Top-level blockers: <strong>{esc('; '.join(report.get('blockers', [])) or 'none')}</strong></p>",
        "<table><tr><th>Profile</th><th>Recommended status</th><th>Task success</th><th>Canary</th><th>Critical eval pass</th><th>Evidence</th><th>Policy violations</th><th>Blockers</th></tr>",
    ]
    for row in report["profiles"]:
        blockers = "; ".join(row["blockers"])
        lines.append(
            "<tr>"
            f"<td>{esc(row['profile'])}</td>"
            f"<td>{esc(row['recommended_routing_status'])}</td>"
            f"<td>{esc(row['run_metrics']['task_success_rate_pct'])}%</td>"
            f"<td>{esc(row.get('canary_metrics', {}).get('ok'))}</td>"
            f"<td>{esc(row['evaluation_metrics']['critical_eval_pass_rate_pct'])}%</td>"
            f"<td>{esc(row['evaluation_metrics']['average_evidence_completeness_pct'])}%</td>"
            f"<td>{esc(row['evaluation_metrics']['policy_violation_count'])}</td>"
            f"<td>{esc(blockers)}</td>"
            "</tr>"
        )
    lines.extend(["</table>", f"<p class='muted'>{esc(report['safety_note'])}</p>", "</body></html>"])
    return "\n".join(lines)


def write_report(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"profile_routing_readiness_{stamp}.json"
    html_path = output_dir / f"profile_routing_readiness_{stamp}.html"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    return {"json": str(json_path), "html": str(html_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    config = load_yaml(Path(args.config).expanduser())
    registry = load_yaml(PROJECT_ROOT / str(config.get("source_registry")))
    shadow_path, shadow_report = latest_shadow_report(config)
    canary_path, canary_report = latest_json_report(str(config.get("specialist_canary_report_glob") or ""))
    behavioral_reports = behavioral_reports_by_profile(str(config.get("behavioral_eval_report_glob") or ""))
    report = build_report(
        config=config,
        registry=registry,
        run_rows=load_csv(DATA_DIR / "agent_run_log.csv"),
        eval_rows=load_csv(DATA_DIR / "agent_evaluations.csv"),
        shadow_report_path=shadow_path,
        shadow_report=shadow_report,
        canary_report_path=canary_path,
        canary_report=canary_report,
        behavioral_reports=behavioral_reports,
    )
    paths = write_report(report, Path(args.output_dir).expanduser())
    payload = {
        "status": report["status"],
        "eligible_profile_count": report["eligible_profile_count"],
        "profile_count": report["profile_count"],
        "blockers": report.get("blockers", []),
        "production_routing_enabled": False,
        "json": paths["json"],
        "html": paths["html"],
    }
    print(json.dumps(payload, indent=2) if args.json else f"Profile routing readiness {report['status']}: {paths['html']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
