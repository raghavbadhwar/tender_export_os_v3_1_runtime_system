#!/usr/bin/env python3
"""Evaluate a learning proposal before approval/application."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_EVALUATIONS = PROJECT_ROOT / "data" / "agent_evaluations.csv"
LEARNING_PROPOSALS = PROJECT_ROOT / "data" / "learning_proposals.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "learning_evaluations"
AGENT_EVALUATION_COLUMNS = [
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


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AGENT_EVALUATION_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in AGENT_EVALUATION_COLUMNS})


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("evaluation input must be a JSON object")
    return value


def safe_float(value: Any) -> float:
    try:
        return float(clean(value) or "0")
    except ValueError:
        return 0.0


def evaluate_payload(payload: dict[str, Any], *, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    proposal_id = clean(payload.get("proposal_id"))
    runs = payload.get("repeated_runs", [])
    policy_checks = payload.get("policy_checks", [])
    current = payload.get("current_metrics", {})
    candidate = payload.get("candidate_metrics", {})
    rollback_path = clean(payload.get("rollback_artifact_path"))
    errors: list[str] = []
    if not proposal_id:
        errors.append("proposal_id is required")
    if not isinstance(runs, list) or len(runs) != 3:
        errors.append("exactly three repeated_runs are required")
    if not isinstance(policy_checks, list) or not policy_checks:
        errors.append("policy_checks are required")
    elif any(check.get("status") != "PASS" for check in policy_checks if isinstance(check, dict)):
        errors.append("all policy checks must PASS")
    if rollback_path and not (root / rollback_path).exists() and not Path(rollback_path).expanduser().exists():
        errors.append("rollback artifact path does not exist")
    if not rollback_path:
        errors.append("rollback_artifact_path is required")

    rows: list[dict[str, Any]] = []
    for index, run in enumerate(runs if isinstance(runs, list) else [], start=1):
        expected = clean(run.get("expected_result"))
        actual = clean(run.get("actual_result"))
        policy = "PASS" if all(check.get("status") == "PASS" for check in policy_checks if isinstance(check, dict)) else "FAIL"
        status = "PASS" if expected and expected == actual and policy == "PASS" else "FAIL"
        evidence = safe_float(run.get("evidence_completeness_pct"))
        if evidence < 90:
            status = "FAIL"
            errors.append(f"repeat {index} evidence completeness below 90")
        rows.append(
            {
                "evaluation_id": f"EVAL-{proposal_id}-{index}",
                "profile": clean(payload.get("profile")) or "learning-evaluator",
                "scenario_id": clean(payload.get("scenario_id")) or proposal_id,
                "scenario_type": clean(payload.get("scenario_type")) or "INTEGRATION",
                "case_id": clean(payload.get("case_id")),
                "run_id": clean(run.get("run_id")) or f"RUN-{proposal_id}-{index}",
                "repeat_number": index,
                "expected_result": expected,
                "actual_result": actual,
                "evidence_completeness_pct": evidence,
                "policy_compliance": policy,
                "latency_ms": safe_float(run.get("latency_ms")),
                "input_tokens": safe_float(run.get("input_tokens")),
                "output_tokens": safe_float(run.get("output_tokens")),
                "cost_usd": safe_float(run.get("cost_usd")),
                "score": safe_float(run.get("score")),
                "status": status,
                "report_path": clean(payload.get("report_path")) or "outputs/learning_evaluations/pending.json",
                "evaluated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
                "notes": clean(run.get("notes")),
            }
        )

    current_latency = safe_float(current.get("latency_ms"))
    candidate_latency = safe_float(candidate.get("latency_ms"))
    current_cost = safe_float(current.get("cost_usd"))
    candidate_cost = safe_float(candidate.get("cost_usd"))
    if current_latency and candidate_latency > current_latency * 2:
        errors.append("candidate latency exceeds 2x current")
    if current_cost and candidate_cost > current_cost * 2:
        errors.append("candidate cost exceeds 2x current")
    if any(row["status"] != "PASS" for row in rows):
        errors.append("all three repeated runs must PASS")

    return {
        "proposal_id": proposal_id,
        "evaluation_status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "promotion_gate": {
            "required_repeated_runs": 3,
            "passing_repeated_runs": sum(row["status"] == "PASS" for row in rows),
            "rollback_artifact_present": bool(rollback_path and (root / rollback_path).exists()) or bool(rollback_path and Path(rollback_path).expanduser().exists()),
            "ready_for_owner_approval": not errors and len(rows) == 3 and all(row["status"] == "PASS" for row in rows),
        },
        "rows": rows,
        "cost_latency_comparison": {
            "current_latency_ms": current_latency,
            "candidate_latency_ms": candidate_latency,
            "current_cost_usd": current_cost,
            "candidate_cost_usd": candidate_cost,
        },
        "rollback_artifact_path": rollback_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON evaluation input")
    parser.add_argument("--agent-evaluations", default=str(AGENT_EVALUATIONS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = load_json(Path(args.input).expanduser())
    report = evaluate_payload(payload)
    outputs: dict[str, str] = {}
    if args.write:
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"learning_evaluation_{report['proposal_id']}.json"
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        existing = load_csv(Path(args.agent_evaluations).expanduser())
        by_id = {row.get("evaluation_id", ""): row for row in existing}
        by_id.update({row["evaluation_id"]: row for row in report["rows"]})
        write_csv(Path(args.agent_evaluations).expanduser(), list(by_id.values()))
        outputs = {"json": str(output_path)}
    result = report | {"outputs": outputs}
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False))
    return 0 if report["evaluation_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
