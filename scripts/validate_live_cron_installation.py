#!/usr/bin/env python3
"""Verify that every configured supervised Tender OS cron job is installed live.

The repository YAML is the desired scheduler state.  Hermes stores the actual
profile schedule separately, so a profile reset can otherwise leave a job
defined but never firing.  This validator is intentionally read-only: it
does not create, delete, pause, or run cron jobs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "hermes_cron.yaml"
DEFAULT_LIVE_JOBS = Path("/Users/raghav/.hermes/profiles/tender-export-os/cron/jobs.json")
DEFAULT_SCRIPTS_DIR = Path("/Users/raghav/.hermes/profiles/tender-export-os/scripts")


def load_mapping(path: Path, *, yaml_source: bool = False) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) if yaml_source else json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def desired_jobs(config: dict[str, Any]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for raw in config.get("jobs", []) or []:
        if not isinstance(raw, dict) or raw.get("enabled") is False or raw.get("cadence") == "owner-approved":
            continue
        jobs.append(raw)
    return jobs


def finding(code: str, *, job_id: str, detail: str) -> dict[str, str]:
    return {"severity": "BLOCKER", "code": code, "job_id": job_id, "detail": detail}


def build_report(
    config: dict[str, Any],
    live: dict[str, Any],
    *,
    scripts_dir: Path,
    workdir: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    expected = desired_jobs(config)
    live_jobs = [row for row in live.get("jobs", []) or [] if isinstance(row, dict) and row.get("enabled")]
    live_by_script: dict[str, list[dict[str, Any]]] = {}
    for row in live_jobs:
        script = str(row.get("script") or "")
        if script:
            live_by_script.setdefault(script, []).append(row)

    findings: list[dict[str, str]] = []
    installations: list[dict[str, Any]] = []
    expected_scripts: set[str] = set()
    for job in expected:
        job_id = str(job.get("id") or "")
        name = str(job.get("hermes_name") or "")
        script = str(job.get("hermes_script") or "")
        cadence = str(job.get("cadence") or "")
        expected_scripts.add(script)
        if not name or not script:
            findings.append(finding("CRON_METADATA_MISSING", job_id=job_id, detail="hermes_name and hermes_script are required"))
            continue
        if not (scripts_dir / script).is_file():
            findings.append(finding("CRON_WRAPPER_MISSING", job_id=job_id, detail=f"missing profile wrapper: {scripts_dir / script}"))
        matches = live_by_script.get(script, [])
        if not matches:
            findings.append(finding("LIVE_CRON_JOB_MISSING", job_id=job_id, detail=f"no active Hermes job uses {script}"))
            continue
        if len(matches) != 1:
            findings.append(finding("LIVE_CRON_JOB_DUPLICATE", job_id=job_id, detail=f"{len(matches)} active Hermes jobs use {script}"))
            continue
        actual = matches[0]
        schedule = actual.get("schedule") if isinstance(actual.get("schedule"), dict) else {}
        mismatches: list[str] = []
        if str(actual.get("name") or "") != name:
            mismatches.append("name")
        if str(schedule.get("expr") or "") != cadence:
            mismatches.append("schedule")
        if actual.get("no_agent") is not True:
            mismatches.append("no_agent")
        if Path(str(actual.get("workdir") or "")).resolve() != workdir.resolve():
            mismatches.append("workdir")
        if mismatches:
            findings.append(
                finding("LIVE_CRON_JOB_MISMATCH", job_id=job_id, detail=f"{script}: {', '.join(mismatches)} differs from desired state")
            )
        installations.append(
            {
                "job_id": job_id,
                "name": name,
                "script": script,
                "cadence": cadence,
                "live_job_id": str(actual.get("id") or ""),
                "last_status": actual.get("last_status"),
                "installed": not mismatches,
            }
        )

    for script, matches in live_by_script.items():
        if script.startswith("teos_") and script not in expected_scripts:
            findings.append(
                finding("UNMANAGED_LIVE_CRON_JOB", job_id=script, detail=f"{len(matches)} active managed wrapper job(s) are absent from config/hermes_cron.yaml")
            )

    return {
        "schema_version": "live_cron_installation.v1",
        "status": "PASS" if not findings else "BLOCKED",
        "configured_job_count": len(expected),
        "active_live_job_count": len(live_jobs),
        "installed_job_count": sum(1 for row in installations if row["installed"]),
        "installations": installations,
        "findings": findings,
        "external_actions_executed": False,
        "production_routing_enabled": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--live-jobs", default=str(DEFAULT_LIVE_JOBS))
    parser.add_argument("--scripts-dir", default=str(DEFAULT_SCRIPTS_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = load_mapping(Path(args.config), yaml_source=True)
        live = load_mapping(Path(args.live_jobs))
        report = build_report(config, live, scripts_dir=Path(args.scripts_dir))
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        report = {
            "schema_version": "live_cron_installation.v1",
            "status": "BLOCKED",
            "findings": [finding("LIVE_CRON_STATE_UNREADABLE", job_id="scheduler", detail=str(exc))],
            "external_actions_executed": False,
            "production_routing_enabled": False,
        }
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else f"Live cron installation: {report['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
