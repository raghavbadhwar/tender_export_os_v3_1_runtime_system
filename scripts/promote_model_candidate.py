#!/usr/bin/env python3
"""Promote a model candidate only after evaluation and approval gates pass."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    from scripts.validate_model_registry_gates import validate_model_registry_gates
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from validate_model_registry_gates import validate_model_registry_gates


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_REGISTRY = PROJECT_ROOT / "data" / "model_registry.csv"
LEARNING_PROPOSALS = PROJECT_ROOT / "data" / "learning_proposals.csv"
MODEL_COLUMNS = [
    "model_id",
    "target_id",
    "workflow_type",
    "horizon_days",
    "model_version",
    "feature_schema_hash",
    "training_window_start",
    "training_window_end",
    "evaluation_window_start",
    "evaluation_window_end",
    "mature_sample_count",
    "positive_class_count",
    "negative_class_count",
    "primary_metric",
    "metric_value",
    "brier_score",
    "log_loss",
    "calibration_error",
    "calibration_status",
    "status",
    "artifact_path",
    "approval_id",
    "rollback_version",
    "registered_at",
    "notes",
]


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def upper(value: Any) -> str:
    return clean(value).upper()


def safe_float(value: Any) -> float | None:
    try:
        return float(clean(value))
    except ValueError:
        return None


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_model_registry(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MODEL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in MODEL_COLUMNS})


def approved_proposal(
    rows: list[dict[str, str]],
    *,
    proposal_id: str,
    candidate_model_id: str,
    target_id: str,
    workflow_type: str,
) -> dict[str, str] | None:
    for row in rows:
        if clean(row.get("proposal_id")) != proposal_id:
            continue
        if upper(row.get("proposal_type")) != "MODEL":
            return None
        if upper(row.get("status")) != "APPROVED":
            return None
        target_blob = f"{row.get('proposal_target', '')} {row.get('proposed_version', '')} {row.get('affected_workflows', '')}"
        if candidate_model_id not in target_blob or target_id not in target_blob or workflow_type not in target_blob:
            return None
        if not clean(row.get("approval_id")) or not clean(row.get("rollback_artifact_path")):
            return None
        return row
    return None


def validate_promotion(
    *,
    model_registry_rows: list[dict[str, Any]],
    learning_proposals: list[dict[str, str]],
    evaluation_report: dict[str, Any],
    candidate_model_id: str,
    proposal_id: str,
    min_coverage: float = 0.8,
) -> list[str]:
    errors: list[str] = []
    candidate = next((row for row in model_registry_rows if clean(row.get("model_id")) == candidate_model_id), None)
    if candidate is None:
        return [f"candidate model not found: {candidate_model_id}"]
    target_id = clean(candidate.get("target_id"))
    workflow_type = clean(candidate.get("workflow_type"))
    if upper(candidate.get("status")) != "CANDIDATE":
        errors.append(f"{candidate_model_id}.status must be CANDIDATE")
    if upper(candidate.get("calibration_status")) != "CALIBRATED":
        errors.append(f"{candidate_model_id}.calibration_status must be CALIBRATED")
    if not clean(candidate.get("rollback_version")):
        errors.append(f"{candidate_model_id}.rollback_version is required")
    errors.extend(validate_model_registry_gates([candidate]))

    if clean(evaluation_report.get("candidate_model_id")) != candidate_model_id:
        errors.append("evaluation_report.candidate_model_id mismatch")
    if clean(evaluation_report.get("target_id")) != target_id:
        errors.append("evaluation_report.target_id mismatch")
    if upper(evaluation_report.get("workflow_type")) != upper(workflow_type):
        errors.append("evaluation_report.workflow_type mismatch")
    if evaluation_report.get("promotion_decision") != "NOT_PROMOTED_BY_EVALUATION_SCRIPT":
        errors.append("evaluation report must not pre-promote the model")
    if evaluation_report.get("deterministic_tests_passed") is not True:
        errors.append("deterministic tests must pass before promotion")
    if evaluation_report.get("behavioral_tests_passed") is not True:
        errors.append("behavioral tests must pass before promotion")
    coverage = safe_float(evaluation_report.get("coverage"))
    if coverage is None or coverage < min_coverage:
        errors.append(f"coverage must be at least {min_coverage}")
    improvement = safe_float(evaluation_report.get("brier_improvement_vs_champion"))
    champion = clean(evaluation_report.get("current_champion"))
    if champion and (improvement is None or improvement <= 0):
        errors.append("candidate must improve brier score versus current champion")
    metrics = evaluation_report.get("metrics", {})
    if not isinstance(metrics, dict) or safe_float(metrics.get("brier_score")) is None:
        errors.append("evaluation_report.metrics.brier_score is required")

    proposal = approved_proposal(
        learning_proposals,
        proposal_id=proposal_id,
        candidate_model_id=candidate_model_id,
        target_id=target_id,
        workflow_type=workflow_type,
    )
    if proposal is None:
        errors.append("matching APPROVED MODEL learning proposal with approval_id and rollback artifact is required")
    return errors


def promote_rows(
    rows: list[dict[str, Any]],
    *,
    candidate_model_id: str,
    approval_id: str,
    promoted_at: str,
) -> list[dict[str, Any]]:
    candidate = next(row for row in rows if clean(row.get("model_id")) == candidate_model_id)
    target_id = clean(candidate.get("target_id"))
    workflow_type = upper(candidate.get("workflow_type"))
    updated: list[dict[str, Any]] = []
    for row in rows:
        new_row = dict(row)
        if clean(row.get("model_id")) == candidate_model_id:
            new_row["status"] = "CHAMPION"
            new_row["approval_id"] = approval_id
            new_row["registered_at"] = promoted_at
        elif (
            clean(row.get("target_id")) == target_id
            and upper(row.get("workflow_type")) == workflow_type
            and upper(row.get("status")) == "CHAMPION"
        ):
            new_row["status"] = "RETIRED"
            new_row["notes"] = (clean(new_row.get("notes")) + f" Retired by {candidate_model_id} at {promoted_at}.").strip()
        updated.append(new_row)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-registry", default=str(MODEL_REGISTRY))
    parser.add_argument("--learning-proposals", default=str(LEARNING_PROPOSALS))
    parser.add_argument("--evaluation-report", required=True)
    parser.add_argument("--candidate-model-id", required=True)
    parser.add_argument("--proposal-id", required=True)
    parser.add_argument("--min-coverage", type=float, default=0.8)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    model_path = Path(args.model_registry).expanduser().resolve()
    proposals_path = Path(args.learning_proposals).expanduser().resolve()
    evaluation = json.loads(Path(args.evaluation_report).expanduser().read_text(encoding="utf-8"))
    models = load_csv(model_path)
    proposals = load_csv(proposals_path)
    errors = validate_promotion(
        model_registry_rows=models,
        learning_proposals=proposals,
        evaluation_report=evaluation,
        candidate_model_id=args.candidate_model_id,
        proposal_id=args.proposal_id,
        min_coverage=args.min_coverage,
    )
    status = "PASS" if not errors else "FAIL"
    outputs: dict[str, str] = {}
    if args.write and not errors:
        proposal = next(row for row in proposals if clean(row.get("proposal_id")) == args.proposal_id)
        promoted = promote_rows(
            models,
            candidate_model_id=args.candidate_model_id,
            approval_id=proposal["approval_id"],
            promoted_at=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        )
        write_model_registry(model_path, promoted)
        outputs["model_registry"] = str(model_path)
    payload = {"status": status, "errors": errors, "write_applied": bool(args.write and not errors), "outputs": outputs}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else json.dumps(payload, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
