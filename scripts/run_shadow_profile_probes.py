#!/usr/bin/env python3
"""Run local-only shadow probes for every Hermes profile.

The probes create real TASK-093 run evidence without enabling production
routing or performing external actions. By default the script only writes a
receipt. Use --write-log to append idempotent rows to data/agent_run_log.csv.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

try:
    from event_ledger import EVENTS_FILE, append_event
except ModuleNotFoundError:  # pragma: no cover - package import path used by pytest
    from scripts.event_ledger import EVENTS_FILE, append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_REGISTRY = PROJECT_ROOT / "config" / "hermes_specialist_profiles.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "shadow_profile_probes"
DEFAULT_RUN_LOG = DATA_DIR / "agent_run_log.csv"
DEFAULT_EVALUATIONS = DATA_DIR / "agent_evaluations.csv"

EVIDENCE_BY_PROFILE = {
    "tender-export-os": "HERMES.md",
    "teos-orchestrator": "config/kanban_board.yaml",
    "gov-tender-intelligence": "config/sources.gov.yaml",
    "export-buyer-intelligence": "config/sources.export.yaml",
    "supplier-commercial": "config/supplier_532_gate.yaml",
    "pricing-risk": "config/pricing_assumptions.yaml",
    "compliance-due-diligence": "config/compliance_source_policy.yaml",
    "relationship-ops": "config/approval_policy.yaml",
    "learning-evaluation": "config/demand_forecasting.yaml",
}

RUN_LOG_HEADERS = [
    "run_id",
    "run_date",
    "run_time",
    "agent_name",
    "trigger_type",
    "cases_processed",
    "cases_created",
    "cases_rejected",
    "cases_updated",
    "sources_checked",
    "sources_failed",
    "actions_taken",
    "approval_cards_created",
    "receipts_created",
    "errors",
    "warnings",
    "runtime_seconds",
    "status",
    "notes",
]
EVALUATION_HEADERS = [
    "evaluation_id",
    "profile",
    "scenario_id",
    "scenario_type",
    "case_id",
    "run_id",
    "repeat_number",
    "expected_result",
    "actual_result",
    "evidence_completeness_pct",
    "policy_compliance",
    "latency_ms",
    "input_tokens",
    "output_tokens",
    "cost_usd",
    "score",
    "status",
    "report_path",
    "evaluated_at",
    "notes",
]


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def profile_names(registry: dict[str, Any]) -> list[str]:
    owner = str(registry.get("owner_profile") or "").strip()
    specialists = [str(value).strip() for value in registry.get("specialist_profiles") or [] if str(value).strip()]
    return list(dict.fromkeys(([owner] if owner else []) + specialists))


def resolve_project_path(path: str) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def probe_profile(profile: str, *, registry: dict[str, Any]) -> dict[str, Any]:
    evidence_path = EVIDENCE_BY_PROFILE.get(profile, "config/hermes_specialist_profiles.yaml")
    resolved = resolve_project_path(evidence_path)
    errors: list[str] = []
    sha256 = ""
    size_bytes = 0
    if not resolved.is_file():
        errors.append(f"missing evidence file: {evidence_path}")
    else:
        payload = resolved.read_bytes()
        sha256 = hashlib.sha256(payload).hexdigest()
        size_bytes = len(payload)

    profile_config = (registry.get("profiles") or {}).get(profile) if isinstance(registry.get("profiles"), dict) else {}
    allowed_toolsets = profile_config.get("allowed_toolsets") if isinstance(profile_config, dict) else []
    forbidden_toolsets = profile_config.get("forbidden_toolsets") if isinstance(profile_config, dict) else []

    if not isinstance(allowed_toolsets, list):
        errors.append("allowed_toolsets is not a list")
    if not isinstance(forbidden_toolsets, list):
        errors.append("forbidden_toolsets is not a list")

    return {
        "profile": profile,
        "status": "PASS" if not errors else "FAIL",
        "summary": f"Verified local profile evidence for {profile}.",
        "evidence": [
            {
                "path": evidence_path,
                "exists": resolved.is_file(),
                "sha256": sha256,
                "size_bytes": size_bytes,
            }
        ],
        "toolset_summary": {
            "allowed_toolset_count": len(allowed_toolsets) if isinstance(allowed_toolsets, list) else 0,
            "forbidden_toolset_count": len(forbidden_toolsets) if isinstance(forbidden_toolsets, list) else 0,
        },
        "errors": errors,
        "approval_required": False,
        "external_actions_executed": False,
        "production_routing_enabled": False,
    }


def build_report(*, registry: dict[str, Any], as_of: dt.datetime | None = None) -> dict[str, Any]:
    current_time = (as_of or dt.datetime.now(dt.timezone.utc)).replace(microsecond=0)
    probes = [probe_profile(profile, registry=registry) for profile in profile_names(registry)]
    errors = [error for probe in probes for error in probe["errors"]]
    return {
        "schema_version": "shadow_profile_probe.v1",
        "generated_at": current_time.isoformat(),
        "mode": "SHADOW_ONLY",
        "status": "PASS" if probes and not errors else "FAIL",
        "profile_count": len(probes),
        "pass_count": sum(1 for probe in probes if probe["status"] == "PASS"),
        "probes": probes,
        "external_actions_executed": False,
        "production_routing_enabled": False,
        "safety_note": "Local file and registry checks only. No browser, network, email, portal, payment, DSC, upload, contact, or production routing action is performed.",
    }


def write_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.fromisoformat(report["generated_at"]).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"shadow_profile_probe_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_run_log(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def append_run_log_rows(report: dict[str, Any], *, run_log_path: Path, receipt_path: Path) -> dict[str, Any]:
    generated_at = dt.datetime.fromisoformat(report["generated_at"])
    date_label = generated_at.date().isoformat()
    time_label = generated_at.time().replace(microsecond=0).isoformat()
    existing_rows = load_run_log(run_log_path)
    existing_ids = {row.get("run_id", "") for row in existing_rows}
    appended: list[str] = []
    rows = list(existing_rows)
    try:
        receipt_label = str(receipt_path.relative_to(PROJECT_ROOT))
    except ValueError:
        receipt_label = str(receipt_path)

    for probe in report["probes"]:
        profile = str(probe["profile"])
        run_id = f"RUN-{generated_at.strftime('%Y%m%d')}-SHADOW-PROFILE-{profile}"
        if run_id in existing_ids:
            continue
        evidence_count = len(probe.get("evidence") or [])
        row = {
            "run_id": run_id,
            "run_date": date_label,
            "run_time": time_label,
            "agent_name": profile,
            "trigger_type": "shadow_profile_probe",
            "cases_processed": "0",
            "cases_created": "0",
            "cases_rejected": "0",
            "cases_updated": "0",
            "sources_checked": str(evidence_count),
            "sources_failed": "0" if probe["status"] == "PASS" else "1",
            "actions_taken": "shadow_profile_probe",
            "approval_cards_created": "0",
            "receipts_created": "1",
            "errors": "0" if probe["status"] == "PASS" else str(len(probe.get("errors") or [])),
            "warnings": "0",
            "runtime_seconds": "0",
            "status": "SUCCESS" if probe["status"] == "PASS" else "FAIL",
            "notes": f"Local shadow profile evidence probe. receipt={receipt_label}",
        }
        rows.append(row)
        appended.append(run_id)

    if appended:
        write_csv(run_log_path, rows, RUN_LOG_HEADERS)
    return {"appended_count": len(appended), "appended_run_ids": appended}


def append_evaluation_rows(
    report: dict[str, Any],
    *,
    evaluations_path: Path,
    receipt_path: Path,
    events_file: Path | None = None,
) -> dict[str, Any]:
    generated_at = dt.datetime.fromisoformat(report["generated_at"])
    date_label = generated_at.strftime("%Y%m%d")
    existing_rows = load_csv(evaluations_path)
    existing_by_id = {row.get("evaluation_id", ""): row for row in existing_rows}
    rows = list(existing_rows)
    appended: list[str] = []
    event_ids: list[str] = []
    try:
        receipt_label = str(receipt_path.relative_to(PROJECT_ROOT))
    except ValueError:
        receipt_label = str(receipt_path)

    for probe in report["probes"]:
        profile = str(probe["profile"])
        evaluation_id = f"AE-{date_label}-SHADOW-PROFILE-{profile}"
        row = existing_by_id.get(evaluation_id)
        if row is None:
            passed = probe["status"] == "PASS"
            run_id = f"RUN-{date_label}-SHADOW-PROFILE-{profile}"
            row = {
                "evaluation_id": evaluation_id,
                "profile": profile,
                "scenario_id": "shadow_profile_probe",
                "scenario_type": "ROUTINE",
                "case_id": "SHADOW_PROFILE_PROBE",
                "run_id": run_id,
                "repeat_number": "1",
                "expected_result": "PASS_LOCAL_EVIDENCE_ONLY",
                "actual_result": "PASS_LOCAL_EVIDENCE_ONLY" if passed else "FAIL_LOCAL_EVIDENCE_ONLY",
                "evidence_completeness_pct": "100" if passed else "0",
                "policy_compliance": "PASS" if probe["external_actions_executed"] is False else "FAIL",
                "latency_ms": "0",
                "input_tokens": "",
                "output_tokens": "",
                "cost_usd": "0",
                "score": "100" if passed else "0",
                "status": "PASS" if passed else "FAIL",
                "report_path": receipt_label,
                "evaluated_at": generated_at.isoformat(),
                "notes": "Local shadow profile evidence evaluation; no external action.",
            }
            rows.append(row)
            appended.append(evaluation_id)

        if events_file is not None:
            report_citation = str(row.get("report_path") or receipt_label)
            event = append_event(
                "agent_evaluation.created",
                "run_shadow_profile_probes",
                case_id=str(row.get("case_id") or ""),
                object_type="agent_evaluation",
                object_id=evaluation_id,
                source="shadow_profile_probe",
                payload={"row": row},
                citations=[report_citation],
                idempotency_key=f"agent-evaluation:{evaluation_id}:{hashlib.sha256(json.dumps(row, sort_keys=True).encode('utf-8')).hexdigest()}",
                events_file=events_file,
            )
            event_ids.append(str(event["event_id"]))

    if appended:
        write_csv(evaluations_path, rows, EVALUATION_HEADERS)
    return {
        "evaluation_appended_count": len(appended),
        "appended_evaluation_ids": appended,
        "evaluation_event_count": len(event_ids),
        "evaluation_event_ids": event_ids,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-log", default=str(DEFAULT_RUN_LOG))
    parser.add_argument("--evaluations", default=str(DEFAULT_EVALUATIONS))
    parser.add_argument("--write-log", action="store_true", help="Append idempotent profile probe rows to data/agent_run_log.csv.")
    parser.add_argument("--write-evaluations", action="store_true", help="Append idempotent profile probe rows to data/agent_evaluations.csv.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    registry = load_yaml(Path(args.registry).expanduser())
    report = build_report(registry=registry)
    receipt_path = write_report(report, Path(args.output_dir).expanduser())
    append_result = {"appended_count": 0, "appended_run_ids": []}
    if args.write_log:
        append_result = append_run_log_rows(
            report,
            run_log_path=Path(args.run_log).expanduser(),
            receipt_path=receipt_path,
        )
    evaluation_result = {
        "evaluation_appended_count": 0,
        "appended_evaluation_ids": [],
        "evaluation_event_count": 0,
        "evaluation_event_ids": [],
    }
    if args.write_evaluations:
        evaluation_result = append_evaluation_rows(
            report,
            evaluations_path=Path(args.evaluations).expanduser(),
            receipt_path=receipt_path,
            events_file=EVENTS_FILE,
        )
    payload = {
        "status": report["status"],
        "profile_count": report["profile_count"],
        "pass_count": report["pass_count"],
        "receipt": str(receipt_path),
        "write_log": bool(args.write_log),
        "write_evaluations": bool(args.write_evaluations),
        **append_result,
        **evaluation_result,
        "external_actions_executed": False,
        "production_routing_enabled": False,
    }
    print(json.dumps(payload, indent=2) if args.json else f"Shadow profile probes {report['status']}: {receipt_path}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
