#!/usr/bin/env python3
"""Evaluate a forecast model candidate on mature holdout rows."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKTESTS = PROJECT_ROOT / "data" / "forecast_backtests.csv"
DEFAULT_MODEL_REGISTRY = PROJECT_ROOT / "data" / "model_registry.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "models"


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def safe_float(value: Any) -> float | None:
    try:
        result = float(clean(value))
    except ValueError:
        return None
    return result if 0 <= result <= 1 else None


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mature_scored_rows(rows: list[dict[str, Any]], *, target_id: str = "", workflow_type: str = "") -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in rows:
        if target_id and clean(row.get("target_id")) != target_id:
            continue
        if workflow_type and clean(row.get("workflow_type")).upper() != workflow_type.upper():
            continue
        probability = safe_float(row.get("predicted_probability"))
        outcome = clean(row.get("binary_outcome"))
        if clean(row.get("is_mature")).upper() == "TRUE" and probability is not None and outcome in {"0", "1"}:
            selected.append(row | {"_probability": probability, "_outcome": int(outcome)})
    return selected


def metric_summary(rows: list[dict[str, Any]], *, threshold: float) -> dict[str, Any]:
    if not rows:
        return {
            "count": 0,
            "brier_score": None,
            "log_loss": None,
            "calibration_error": None,
            "precision_at_threshold": None,
            "recall_at_threshold": None,
        }
    eps = 1e-15
    brier = sum((row["_probability"] - row["_outcome"]) ** 2 for row in rows) / len(rows)
    log_loss = -sum(
        row["_outcome"] * math.log(max(eps, min(1 - eps, row["_probability"])))
        + (1 - row["_outcome"]) * math.log(max(eps, min(1 - eps, 1 - row["_probability"])))
        for row in rows
    ) / len(rows)
    bins: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        lower = min(0.8, int(row["_probability"] * 5) / 5)
        upper = min(1.0, lower + 0.2)
        bins[f"{lower:.1f}-{upper:.1f}"].append(row)
    calibration_error = sum(
        (len(values) / len(rows))
        * abs(
            (sum(row["_probability"] for row in values) / len(values))
            - (sum(row["_outcome"] for row in values) / len(values))
        )
        for values in bins.values()
    )
    true_positive = sum(1 for row in rows if row["_probability"] >= threshold and row["_outcome"] == 1)
    false_positive = sum(1 for row in rows if row["_probability"] >= threshold and row["_outcome"] == 0)
    false_negative = sum(1 for row in rows if row["_probability"] < threshold and row["_outcome"] == 1)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else None
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else None
    return {
        "count": len(rows),
        "brier_score": round(brier, 6),
        "log_loss": round(log_loss, 6),
        "calibration_error": round(calibration_error, 6),
        "precision_at_threshold": round(precision, 6) if precision is not None else None,
        "recall_at_threshold": round(recall, 6) if recall is not None else None,
    }


def subgroup_breakdown(rows: list[dict[str, Any]], *, threshold: float) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[f"workflow:{clean(row.get('workflow_type')) or 'UNKNOWN'}"].append(row)
        groups[f"forecast_type:{clean(row.get('forecast_type')) or 'UNKNOWN'}"].append(row)
    return {name: metric_summary(values, threshold=threshold) for name, values in sorted(groups.items())}


def champion_for_target(rows: list[dict[str, str]], target_id: str, workflow_type: str) -> dict[str, str] | None:
    champions = [
        row
        for row in rows
        if clean(row.get("target_id")) == target_id
        and clean(row.get("workflow_type")).upper() == workflow_type.upper()
        and clean(row.get("status")).upper() == "CHAMPION"
    ]
    return champions[-1] if champions else None


def evaluate_candidate(
    *,
    rows: list[dict[str, Any]],
    model_registry_rows: list[dict[str, str]],
    candidate_model_id: str,
    target_id: str,
    workflow_type: str,
    threshold: float = 0.5,
) -> dict[str, Any]:
    started = time.perf_counter()
    selected = mature_scored_rows(rows, target_id=target_id, workflow_type=workflow_type)
    metrics = metric_summary(selected, threshold=threshold)
    total_target_rows = [
        row
        for row in rows
        if (not target_id or clean(row.get("target_id")) == target_id)
        and (not workflow_type or clean(row.get("workflow_type")).upper() == workflow_type.upper())
    ]
    coverage = len(selected) / len(total_target_rows) if total_target_rows else 0
    champion = champion_for_target(model_registry_rows, target_id, workflow_type)
    champion_metric = None
    improvement = None
    if champion and clean(champion.get("brier_score")):
        try:
            champion_metric = float(champion["brier_score"])
            improvement = champion_metric - metrics["brier_score"] if metrics["brier_score"] is not None else None
        except ValueError:
            champion_metric = None
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    return {
        "candidate_model_id": candidate_model_id,
        "target_id": target_id,
        "workflow_type": workflow_type,
        "operational_threshold": threshold,
        "primary_metric": "brier_score",
        "metrics": metrics,
        "coverage": round(coverage, 6),
        "subgroup_breakdown": subgroup_breakdown(selected, threshold=threshold),
        "latency_ms": latency_ms,
        "current_champion": champion.get("model_id") if champion else None,
        "champion_brier_score": champion_metric,
        "brier_improvement_vs_champion": round(improvement, 6) if improvement is not None else None,
        "promotion_decision": "NOT_PROMOTED_BY_EVALUATION_SCRIPT",
        "safety_boundary": "Evaluation only; no registry promotion, external action, price, bid, quote, legal, or compliance commitment.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backtests", default=str(DEFAULT_BACKTESTS))
    parser.add_argument("--model-registry", default=str(DEFAULT_MODEL_REGISTRY))
    parser.add_argument("--candidate-model-id", required=True)
    parser.add_argument("--target-id", required=True)
    parser.add_argument("--workflow-type", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = evaluate_candidate(
        rows=load_csv(Path(args.backtests).expanduser().resolve()),
        model_registry_rows=load_csv(Path(args.model_registry).expanduser().resolve()),
        candidate_model_id=args.candidate_model_id,
        target_id=args.target_id,
        workflow_type=args.workflow_type,
        threshold=args.threshold,
    )
    outputs: dict[str, str] = {}
    if args.write:
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"candidate_eval_{args.candidate_model_id}_{dt.date.today().strftime('%Y%m%d')}.json"
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            outputs["json"] = str(output.relative_to(PROJECT_ROOT))
        except ValueError:
            outputs["json"] = str(output)
    payload = report | {"outputs": outputs}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
