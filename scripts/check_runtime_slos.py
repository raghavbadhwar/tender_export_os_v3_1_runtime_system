#!/usr/bin/env python3
"""Check runtime SLOs and write local exception cards for failures."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "runtime_slo.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "runtime_slo"
Runner = Callable[..., subprocess.CompletedProcess[str]]


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def file_age_hours(path: Path, *, now: dt.datetime | None = None) -> float | None:
    if not path.exists():
        return None
    now = now or now_utc()
    modified = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
    return (now - modified).total_seconds() / 3600


def latest_match(pattern: str) -> Path | None:
    matches = sorted(glob.glob(str(PROJECT_ROOT / pattern)))
    return Path(matches[-1]) if matches else None


def run_command(command: list[str], *, runner: Runner = subprocess.run, timeout: int = 30) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = runner(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "runtime_seconds": round(time.monotonic() - started, 3),
            "stdout": completed.stdout,
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "runtime_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": exc.stdout[-2000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": exc.stderr[-2000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def pass_fail(name: str, ok: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "status": "PASS" if ok else "FAIL", **details}


def check_age(name: str, pattern: str, max_age_hours: float) -> dict[str, Any]:
    path = latest_match(pattern)
    age = file_age_hours(path) if path else None
    ok = age is not None and age <= max_age_hours
    return pass_fail(name, ok, {"path": str(path or ""), "age_hours": round(age, 3) if age is not None else None, "max_age_hours": max_age_hours})


def check_disk(min_free_gb: float) -> dict[str, Any]:
    usage = shutil.disk_usage(PROJECT_ROOT)
    free_gb = usage.free / (1024 ** 3)
    return pass_fail("disk_headroom", free_gb >= min_free_gb, {"free_gb": round(free_gb, 2), "min_free_gb": min_free_gb})


def check_scheduler(max_age_hours: float) -> dict[str, Any]:
    rows = load_csv(PROJECT_ROOT / "data" / "agent_run_log.csv")
    latest_date = ""
    for row in rows:
        date = str(row.get("run_date") or "")
        time_value = str(row.get("run_time") or "00:00:00")
        if date:
            latest_date = max(latest_date, f"{date}T{time_value}")
    if not latest_date:
        return pass_fail("scheduler_heartbeat", False, {"latest_run": "", "age_hours": None, "max_age_hours": max_age_hours})
    try:
        latest = dt.datetime.fromisoformat(latest_date).replace(tzinfo=dt.timezone.utc)
        age = (now_utc() - latest).total_seconds() / 3600
    except ValueError:
        age = None
    return pass_fail("scheduler_heartbeat", age is not None and age <= max_age_hours, {"latest_run": latest_date, "age_hours": round(age, 3) if age is not None else None, "max_age_hours": max_age_hours})


def check_projection_rebuild(max_age_hours: float) -> dict[str, Any]:
    candidates = [
        latest_match("outputs/projections*/master_cases.csv"),
        latest_match("outputs/disaster_recovery_drill/DR-*/rebuilt_projections/master_cases.csv"),
    ]
    candidates = [path for path in candidates if path is not None]
    if not candidates:
        return pass_fail("projection_rebuild", False, {"path": "", "age_hours": None, "max_age_hours": max_age_hours})
    path = max(candidates, key=lambda item: item.stat().st_mtime)
    age = file_age_hours(path)
    return pass_fail("projection_rebuild", age is not None and age <= max_age_hours, {"path": str(path), "age_hours": round(age, 3) if age is not None else None, "max_age_hours": max_age_hours})


def check_gateway(runner: Runner) -> dict[str, Any]:
    result = run_command(["hermes", "gateway", "status"], runner=runner, timeout=20)
    text = (result["stdout_tail"] + result["stderr_tail"]).lower()
    ok = result["returncode"] == 0 and ("running" in text or "gateway" in text)
    return pass_fail("gateway_health", ok, {"command": result})


def check_kanban(runner: Runner) -> dict[str, Any]:
    result = run_command(["hermes", "kanban", "--board", "tender-export-os", "list", "--json"], runner=runner, timeout=20)
    ok = result["returncode"] == 0 and not result["timed_out"]
    stale_count = 0
    if ok:
        try:
            tasks = json.loads(result.get("stdout") or result["stdout_tail"] or "[]")
            if isinstance(tasks, list):
                stale_count = sum(1 for task in tasks if str(task.get("status", "")).lower() == "running")
        except json.JSONDecodeError:
            ok = False
    result.pop("stdout", None)
    return pass_fail("kanban_dispatch", ok, {"stale_running_task_count": stale_count, "command": result})


def check_operational_metrics(path: Path, thresholds: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate privacy-safe local runtime metrics; missing evidence fails closed."""
    names = [
        "kanban_dispatch_latency",
        "worker_success_rate",
        "mcp_cold_start",
        "event_to_task_latency",
        "owner_channel_delivery",
        "receipt_completeness",
    ]
    if not path.is_file():
        return [pass_fail(name, False, {"path": str(path), "reason": "metrics_evidence_missing"}) for name in names]
    try:
        metrics = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [pass_fail(name, False, {"path": str(path), "reason": "metrics_evidence_invalid"}) for name in names]
    if not isinstance(metrics, dict):
        return [pass_fail(name, False, {"path": str(path), "reason": "metrics_evidence_not_object"}) for name in names]

    def numeric(key: str) -> float | None:
        value = metrics.get(key)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    definitions = [
        ("kanban_dispatch_latency", "kanban_dispatch_p95_ms", "max", thresholds.get("kanban_dispatch_p95_ms", 300000)),
        ("worker_success_rate", "worker_success_rate_pct", "min", thresholds.get("worker_success_rate_min_pct", 100)),
        ("mcp_cold_start", "mcp_cold_start_p95_ms", "max", thresholds.get("mcp_cold_start_p95_ms", 30000)),
        ("event_to_task_latency", "event_to_task_p95_ms", "max", thresholds.get("event_to_task_p95_ms", 300000)),
        ("owner_channel_delivery", "owner_channel_delivery_age_hours", "max", thresholds.get("owner_channel_delivery_max_age_hours", 24)),
        ("receipt_completeness", "receipt_completeness_pct", "min", thresholds.get("receipt_completeness_min_pct", 100)),
    ]
    checks = []
    for name, key, operator, threshold in definitions:
        observed = numeric(key)
        limit = float(threshold)
        ok = observed is not None and (observed <= limit if operator == "max" else observed >= limit)
        checks.append(pass_fail(name, ok, {"path": str(path), "metric": key, "observed": observed, "operator": operator, "threshold": limit}))
    return checks


def build_exception_cards(checks: list[dict[str, Any]], output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for check in checks:
        if check["status"] == "PASS":
            continue
        card = {
            "schema_version": "runtime_slo_exception.v1",
            "created_at": now_utc().replace(microsecond=0).isoformat(),
            "check": check["name"],
            "status": check["status"],
            "details": check,
            "recommended_owner_action": "Review runtime SLO failure and assign repair before relying on autonomous routing.",
            "kanban_mutated": False,
        }
        path = output_dir / f"{check['name']}_exception.json"
        path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        paths.append(str(path))
    return paths


def run_checks(*, config: dict[str, Any], runner: Runner = subprocess.run) -> dict[str, Any]:
    thresholds = config.get("thresholds") if isinstance(config.get("thresholds"), dict) else {}
    cards_dir = PROJECT_ROOT / str((config.get("exception_routing") or {}).get("output_dir") or "outputs/runtime_slo/exception_cards")
    checks = [
        check_gateway(runner),
        check_age("mcp_discovery", "outputs/upgrade_baseline/mcp_discovery_reliability.json", float(thresholds.get("mcp_discovery_max_age_hours", 168))),
        check_kanban(runner),
        check_scheduler(float(thresholds.get("scheduler_heartbeat_max_age_hours", 24))),
        check_age("source_canary", "outputs/source_canary/*/canary_report.json", float(thresholds.get("source_canary_max_age_hours", 24))),
        check_projection_rebuild(float(thresholds.get("projection_rebuild_max_age_hours", 168))),
        check_age("behavioral_eval_freshness", "outputs/hermes_behavioral_eval/HBEVAL-*/report.json", float(thresholds.get("behavioral_eval_max_age_hours", 168))),
        check_disk(float(thresholds.get("disk_free_gb_min", 5))),
        check_age("backup_age", "outputs/disaster_recovery_drill/DR-*/disaster_recovery_drill_report.json", float(thresholds.get("disaster_recovery_drill_max_age_hours", 168))),
        check_age("production_readiness_gate_freshness", "outputs/production_readiness/production_readiness_gate_*.json", float(thresholds.get("production_readiness_gate_max_age_hours", 24))),
    ]
    checks.extend(
        check_operational_metrics(
            PROJECT_ROOT / str((config.get("observability") or {}).get("metrics_path") or "outputs/observability/runtime_metrics.json"),
            thresholds,
        )
    )
    exception_cards = build_exception_cards(checks, cards_dir)
    return {
        "schema_version": "runtime_slo_report.v1",
        "generated_at": now_utc().replace(microsecond=0).isoformat(),
        "status": "PASS" if not exception_cards else "FAIL",
        "checks": checks,
        "exception_cards": exception_cards,
        "kanban_mutated": False,
        "external_actions_executed": False,
    }


def write_report(report: dict[str, Any], output_dir: Path = DEFAULT_OUTPUT_DIR) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_utc().strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"runtime_slo_report_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = run_checks(config=load_config(Path(args.config).expanduser()))
    path = write_report(report)
    payload = {"status": report["status"], "report": path, "exception_cards": len(report["exception_cards"])}
    print(json.dumps(payload, indent=2) if args.json else f"Runtime SLO {report['status']}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
