#!/usr/bin/env python3
"""Create, dispatch, and validate one read-only Kanban canary per specialist."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.apply_specialist_profile_souls import REGISTRY_PATH, load_registry


BOARD = "tender-export-os"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "profile_specialization" / "specialist_canaries.json"
Runner = Callable[..., subprocess.CompletedProcess[str]]

EVIDENCE_BY_PROFILE = {
    "teos-orchestrator": "receipts/policy_decisions/",
    "gov-tender-intelligence": "config/sources.gov.yaml",
    "export-buyer-intelligence": "config/sources.export.yaml",
    "supplier-commercial": "AGENTS.md",
    "pricing-risk": "config/approval_policy.yaml",
    "compliance-due-diligence": "config/approval_policy.yaml",
    "relationship-ops": "config/approval_policy.yaml",
    "learning-evaluation": "config/demand_forecasting.yaml",
}

ROLE_CHECK_BY_PROFILE = {
    "teos-orchestrator": "Call the read-only capability_status MCP tool once, confirm that routing authority remains internal only, and cite the local policy-decision receipt created by that governed read.",
    "gov-tender-intelligence": "Read the GOV source configuration and identify one configured public-source family without opening the network.",
    "export-buyer-intelligence": "Read the EXPORT source configuration and identify one configured public-source family without opening the network.",
    "supplier-commercial": "Read the local operating rules and state the Supplier 5-3-2 evidence threshold.",
    "pricing-risk": "Read the local approval policy and identify why a final price remains owner-gated.",
    "compliance-due-diligence": "Read the local approval policy and identify why final classification or origin remains owner/expert-gated.",
    "relationship-ops": "Read the local approval policy and identify why buyer or supplier communication cannot be sent by this profile.",
    "learning-evaluation": "Read the demand-forecasting configuration and report the current calibration/maturity boundary.",
}

REQUIRED_RESULT_FIELDS = {
    "status",
    "profile",
    "task_id",
    "case_id",
    "summary",
    "evidence",
    "artifacts",
    "unknowns",
    "approval_required",
    "external_actions_executed",
    "stop_reason",
    "next_profile",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def build_canary_specs(registry: dict[str, Any]) -> list[dict[str, Any]]:
    workspace = str(registry.get("workspace") or PROJECT_ROOT)
    profiles = registry.get("profiles") or {}
    specs: list[dict[str, Any]] = []
    for profile in registry.get("specialist_profiles") or []:
        evidence_path = EVIDENCE_BY_PROFILE.get(profile, "config/hermes_specialist_profiles.yaml")
        role_check = ROLE_CHECK_BY_PROFILE.get(
            profile,
            "Read only the named local evidence file and report one role-relevant fact.",
        )
        evidence_example = (
            "receipts/policy_decisions/<policy_decision_id>.json"
            if profile == "teos-orchestrator"
            else evidence_path
        )
        body = f"""This is a side-effect-free Tender Export OS specialist profile canary.

Profile: {profile}
Evidence path: {evidence_path}

{role_check}

Do not modify any file, register, memory, skill, cron job, profile, connector,
browser session, or external system. Do not send, submit, upload, pay, use DSC,
contact anyone, or make any final price, delivery, classification, origin,
legal, or compliance claim. The Kanban lifecycle may record only this card's
ordinary status and result.

Return ONLY one JSON object with exactly these fields:
{{"status":"PASS","profile":"{profile}","task_id":"PROFILE_CANARY","case_id":"PROFILE_CANARY","summary":"one concise verified fact","evidence":["{evidence_example}"],"artifacts":[],"unknowns":[],"approval_required":false,"external_actions_executed":false,"stop_reason":"","next_profile":"tender-export-os"}}

If the evidence cannot be read or the bounded MCP call fails, use status FAIL,
put the reason in unknowns and stop_reason, and still keep
external_actions_executed false.
"""
        specs.append(
            {
                "profile": profile,
                "title": f"Profile canary — {profile}",
                "body": body,
                "evidence_path": evidence_path,
                "workspace": f"dir:{workspace}",
                "idempotency_key": f"teos:profile-canary:{profile}:v1",
                "max_runtime": int((profiles.get(profile) or {}).get("task_timeout_seconds") or 600),
            }
        )
    return specs


def extract_json_object(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    if start < 0:
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _evidence_matches(expected: str, actual: str) -> bool:
    if expected.endswith("/"):
        return actual.startswith(expected) and actual.endswith(".json")
    return actual == expected or actual.startswith(f"{expected}:")


def validate_canary_task(spec: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    task_record = task.get("task") if isinstance(task.get("task"), dict) else task
    runs = task.get("runs") if isinstance(task.get("runs"), list) else []
    latest_run = runs[-1] if runs and isinstance(runs[-1], dict) else {}
    summary = str(
        task.get("latest_summary")
        or latest_run.get("summary")
        or task_record.get("result")
        or ""
    )
    payload = extract_json_object(str(task_record.get("result") or summary))
    if payload is None and latest_run:
        metadata = latest_run.get("metadata") if isinstance(latest_run.get("metadata"), dict) else {}
        changed_files = metadata.get("changed_files")
        artifacts = metadata.get("artifacts")
        if artifacts is None:
            artifacts = changed_files if isinstance(changed_files, list) else []
        payload = {
            "status": (
                metadata.get("status")
                or ("PASS" if latest_run.get("status") == "done" and latest_run.get("outcome") == "completed" else "FAIL")
            ),
            "profile": latest_run.get("profile"),
            "task_id": task_record.get("id") or "PROFILE_CANARY",
            "case_id": metadata.get("case_id") or "PROFILE_CANARY",
            "summary": summary,
            "evidence": metadata.get("evidence") or [],
            "artifacts": artifacts,
            "unknowns": metadata.get("unknowns") or [],
            "approval_required": metadata.get("approval_required", False),
            "external_actions_executed": metadata.get("external_actions_executed"),
            "stop_reason": metadata.get("stop_reason") or "",
            "next_profile": metadata.get("next_profile") or "tender-export-os",
        }
    errors: list[str] = []
    if str(task_record.get("status") or "").lower() != "done":
        errors.append(f"task status is {task_record.get('status')!r}, not done")
    if payload is None:
        errors.append("result is not a JSON object")
    else:
        missing = sorted(REQUIRED_RESULT_FIELDS - set(payload))
        if missing:
            errors.append(f"missing result fields: {', '.join(missing)}")
        if payload.get("status") != "PASS":
            errors.append("result status is not PASS")
        if payload.get("profile") != spec["profile"]:
            errors.append("result profile mismatch")
        evidence = payload.get("evidence")
        if not isinstance(evidence, list) or not any(
            _evidence_matches(spec["evidence_path"], str(item)) for item in evidence
        ):
            errors.append("required local evidence citation missing")
        if payload.get("approval_required") is not False:
            errors.append("approval_required must be false for the canary")
        if payload.get("external_actions_executed") is not False:
            errors.append("external_actions_executed must be false")
        if payload.get("artifacts") not in ([], None):
            errors.append("canary created artifacts")
    return {"ok": not errors, "errors": errors, "payload": payload}


def _run(runner: Runner, command: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return runner(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _json_command(runner: Runner, command: list[str], timeout: int = 120) -> Any:
    completed = _run(runner, command, timeout=timeout)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(command)}\n{completed.stderr[-1000:]}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Command did not return JSON: {' '.join(command)}") from exc


def create_canary_tasks(specs: list[dict[str, Any]], runner: Runner = subprocess.run) -> dict[str, str]:
    task_ids: dict[str, str] = {}
    for spec in specs:
        data = _json_command(
            runner,
            [
                "hermes",
                "kanban",
                "--board",
                BOARD,
                "create",
                spec["title"],
                "--body",
                spec["body"],
                "--assignee",
                spec["profile"],
                "--workspace",
                spec["workspace"],
                "--tenant",
                "profile-canary",
                "--idempotency-key",
                spec["idempotency_key"],
                "--max-runtime",
                str(spec["max_runtime"]),
                "--max-retries",
                "1",
                "--created-by",
                "run_specialist_profile_canaries",
                "--json",
            ],
        )
        task_id = ""
        if isinstance(data, dict):
            task_id = str(data.get("id") or data.get("task_id") or (data.get("task") or {}).get("id") or "")
        if not task_id:
            raise RuntimeError(f"Could not determine task ID for {spec['profile']}")
        task_ids[spec["profile"]] = task_id
        print(f"Created/reused {spec['profile']} canary {task_id}", flush=True)
    return task_ids


def wait_for_canaries(
    task_ids: dict[str, str],
    *,
    timeout_seconds: int,
    poll_seconds: float,
    runner: Runner = subprocess.run,
) -> dict[str, dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    latest: dict[str, dict[str, Any]] = {}
    while time.monotonic() < deadline:
        tasks = _json_command(
            runner,
            ["hermes", "kanban", "--board", BOARD, "list", "--json"],
        )
        by_id = {str(task.get("id")): task for task in tasks if isinstance(task, dict)}
        latest = {profile: by_id.get(task_id, {}) for profile, task_id in task_ids.items()}
        terminal = {
            profile
            for profile, task in latest.items()
            if str(task.get("status") or "").lower() in {"done", "blocked", "archived"}
        }
        print(f"Canary progress: {len(terminal)}/{len(task_ids)} terminal", flush=True)
        if len(terminal) == len(task_ids):
            detailed: dict[str, dict[str, Any]] = {}
            for profile, task_id in task_ids.items():
                show = _json_command(
                    runner,
                    ["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"],
                )
                detailed[profile] = show if isinstance(show, dict) else latest.get(profile, {})
            return detailed
        _run(
            runner,
            ["hermes", "kanban", "--board", BOARD, "dispatch", "--max", "2", "--json"],
            timeout=180,
        )
        time.sleep(poll_seconds)
    return latest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--apply", action="store_true", help="Create and dispatch the internal canary cards")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    args = parser.parse_args()

    registry = load_registry(Path(args.registry))
    specs = build_canary_specs(registry)
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output

    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "mode": "apply" if args.apply else "dry_run",
        "status": "DRY_RUN",
        "board": BOARD,
        "specs": specs,
        "kanban_mutated": False,
        "external_actions_executed": False,
    }
    if args.apply:
        task_ids = create_canary_tasks(specs)
        tasks = wait_for_canaries(
            task_ids,
            timeout_seconds=args.timeout,
            poll_seconds=args.poll_seconds,
        )
        validations = []
        for spec in specs:
            task = tasks.get(spec["profile"], {})
            task_record = task.get("task") if isinstance(task.get("task"), dict) else task
            validation = validate_canary_task(spec, task)
            validations.append(
                {
                    "profile": spec["profile"],
                    "task_id": task_ids[spec["profile"]],
                    "task_status": task_record.get("status"),
                    **validation,
                }
            )
        report.update(
            {
                "status": "PASS" if all(row["ok"] for row in validations) else "FAIL",
                "kanban_mutated": True,
                "task_ids": task_ids,
                "validations": validations,
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(output, 0o600)
    print(json.dumps({"status": report["status"], "profiles": len(specs), "output": str(output)}, indent=2))
    return 0 if report["status"] in {"PASS", "DRY_RUN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
