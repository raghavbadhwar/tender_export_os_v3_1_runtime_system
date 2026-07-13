#!/usr/bin/env python3
"""Evaluate mature V5 forecast outcomes without overstating calibration."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from scripts.event_ledger import append_event
    from scripts.validate_forecast_targets import load_targets, maturity_status
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import append_event
    from validate_forecast_targets import load_targets, maturity_status


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKTEST_PATH = PROJECT_ROOT / "data" / "forecast_backtests.csv"
FORECAST_PATH = PROJECT_ROOT / "data" / "forecast_candidates.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "demand_forecasting"


def as_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def safe_probability(value: Any) -> float | None:
    try:
        result = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return result if 0 <= result <= 1 else None


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _forecast_lookup(forecast_rows: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    return {str(row.get("forecast_id") or ""): row for row in (forecast_rows or []) if row.get("forecast_id")}


def _calibration_bins(mature: list[tuple[float, int, str]]) -> list[dict[str, Any]]:
    bins: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for probability, outcome, _ in mature:
        lower = min(0.8, int(probability * 5) / 5)
        upper = min(1.0, lower + 0.2)
        bins[f"{lower:.1f}-{upper:.1f}"].append((probability, outcome))
    return [
        {
            "range": label,
            "count": len(values),
            "mean_predicted_probability": round(sum(value[0] for value in values) / len(values), 4),
            "observed_success_rate": round(sum(value[1] for value in values) / len(values), 4),
        }
        for label, values in sorted(bins.items())
    ]


def evaluate_rows(
    rows: list[dict[str, Any]],
    minimum_sample: int = 30,
    *,
    forecast_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    forecast_by_id = _forecast_lookup(forecast_rows)
    target_config = load_targets()
    mature: list[tuple[float, int, str, str, str]] = []
    for row in rows:
        probability = safe_probability(row.get("predicted_probability"))
        outcome = str(row.get("binary_outcome", "")).strip()
        if not as_bool(row.get("is_mature")) or probability is None or outcome not in {"0", "1"}:
            continue
        forecast = forecast_by_id.get(str(row.get("forecast_id") or ""), {})
        target_id = str(row.get("target_id") or forecast.get("target_id") or "UNKNOWN_TARGET")
        workflow_type = str(row.get("workflow_type") or forecast.get("workflow_type") or "UNKNOWN_WORKFLOW")
        mature.append((probability, int(outcome), str(row.get("model_version") or "unknown"), target_id, workflow_type))

    models: dict[str, int] = defaultdict(int)
    for _, _, model, _, _ in mature:
        models[model] += 1
    by_target: dict[tuple[str, str], list[tuple[float, int, str]]] = defaultdict(list)
    for probability, outcome, model, target_id, workflow_type in mature:
        by_target[(target_id, workflow_type)].append((probability, outcome, model))

    target_evaluations: list[dict[str, Any]] = []
    for (target_id, workflow_type), values in sorted(by_target.items()):
        positives = sum(outcome for _, outcome, _ in values)
        negatives = len(values) - positives
        if target_id == "UNKNOWN_TARGET":
            status = {
                "status": "UNKNOWN_TARGET",
                "calibration_ready": False,
                "training_ready": False,
                "calibration_required": max(30, minimum_sample),
                "training_required": 100,
                "positive_class_required": 20,
                "negative_class_required": 20,
            }
        else:
            status = maturity_status(
                target_id=target_id,
                mature_observations=len(values),
                positive_class_count=positives,
                negative_class_count=negatives,
                config=target_config,
            )
        brier = sum((probability - outcome) ** 2 for probability, outcome, _ in values) / len(values)
        hit_rate = positives / len(values)
        target_evaluations.append(
            {
                "target_id": target_id,
                "workflow_type": workflow_type,
                "mature_sample_size": len(values),
                "positive_class_count": positives,
                "negative_class_count": negatives,
                "status": status["status"],
                "calibration_ready": status["calibration_ready"],
                "training_ready": status["training_ready"],
                "brier_score": round(brier, 6) if status["calibration_ready"] else None,
                "observed_success_rate": round(hit_rate, 4) if status["calibration_ready"] else None,
                "calibration_bins": _calibration_bins(values) if status["calibration_ready"] else [],
                "interpretation": (
                    "Training gate met for this exact target/workflow; candidate models may be evaluated."
                    if status["training_ready"]
                    else "Calibration gate met for this exact target/workflow; report calibration metrics but keep learned-model training disabled."
                    if status["calibration_ready"]
                    else "Keep expert prior only; do not report calibration metrics for this target/workflow yet."
                ),
            }
        )
    any_calibrated = any(item["calibration_ready"] for item in target_evaluations)
    any_training_ready = any(item["training_ready"] for item in target_evaluations)
    return {
        "status": "TRAINING_GATE_MET" if any_training_ready else "CALIBRATION_MEASURED" if any_calibrated else "INSUFFICIENT_MATURE_SAMPLE",
        "minimum_mature_sample": max(30, minimum_sample),
        "mature_sample_size": len(mature),
        "excluded_unmatured_or_unscored": len(rows) - len(mature),
        "brier_score": None,
        "observed_success_rate": None,
        "calibration_bins": [],
        "target_evaluations": target_evaluations,
        "model_sample_sizes": dict(sorted(models.items())),
        "interpretation": (
            "At least one exact target/workflow has met the training gate; candidate training may proceed through the separate training/evaluation approval path."
            if any_training_ready
            else "At least one exact target/workflow has enough mature outcomes for calibration reporting; do not mix target populations."
            if any_calibrated
            else "Do not call these probabilities calibrated yet; keep collecting mature outcomes per exact target/workflow."
        ),
    }


def write_markdown(path: Path, report: dict[str, Any], review_date: str) -> None:
    lines = [
        f"# Forecast Calibration Report - {review_date}",
        "",
        f"Status: `{report['status']}`",
        f"Mature sample: {report['mature_sample_size']} / {report['minimum_mature_sample']} required",
        f"Brier score: {report['brier_score'] if report['brier_score'] is not None else 'not available'}",
        f"Observed success rate: {report['observed_success_rate'] if report['observed_success_rate'] is not None else 'not available'}",
        "",
        report["interpretation"],
        "",
        "| Probability bin | Count | Mean forecast | Observed success |",
        "|---|---:|---:|---:|",
    ]
    for bucket in report["calibration_bins"]:
        lines.append(
            f"| {bucket['range']} | {bucket['count']} | {bucket['mean_predicted_probability']:.4f} | {bucket['observed_success_rate']:.4f} |"
        )
    lines.extend(["", "## Target/workflow gates", "", "| Target | Workflow | Mature | Pos | Neg | Status | Brier |", "|---|---|---:|---:|---:|---|---:|"])
    for target in report.get("target_evaluations", []):
        brier = target["brier_score"] if target["brier_score"] is not None else "not reported"
        lines.append(
            f"| {target['target_id']} | {target['workflow_type']} | {target['mature_sample_size']} | {target['positive_class_count']} | {target['negative_class_count']} | {target['status']} | {brier} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate TEOS forecast calibration")
    parser.add_argument("--backtests", default=str(BACKTEST_PATH))
    parser.add_argument("--forecast-csv", default=str(FORECAST_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--minimum-sample", type=int, default=30)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    backtests = Path(args.backtests).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    forecast_path = Path(args.forecast_csv).expanduser().resolve()
    report = evaluate_rows(load_csv(backtests), minimum_sample=max(30, args.minimum_sample), forecast_rows=load_csv(forecast_path))
    report.update({"review_date": args.date, "source": str(backtests), "safety_boundary": "Internal evaluation only; no external action executed."})
    paths: dict[str, str] = {}
    if args.write:
        output_dir.mkdir(parents=True, exist_ok=True)
        compact = args.date.replace("-", "")
        json_path = output_dir / f"forecast_calibration_{compact}.json"
        md_path = output_dir / f"forecast_calibration_{compact}.md"
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_markdown(md_path, report, args.date)
        paths = {"json": str(json_path), "markdown": str(md_path)}
        evaluation_digest = hashlib.sha256(
            json.dumps(report, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]
        append_event(
            "forecast.calibration_evaluated",
            "V5 Forecast Calibration",
            object_type="forecast_calibration",
            object_id=f"CAL-{args.date.replace('-', '')}",
            source="local_prediction_runtime",
            payload={
                "review_date": args.date,
                "status": report["status"],
                "mature_sample_size": report["mature_sample_size"],
                "report_path": str(json_path.relative_to(PROJECT_ROOT)),
                "brier_score": report["brier_score"],
            },
            citations=[str(backtests.relative_to(PROJECT_ROOT)), str(forecast_path.relative_to(PROJECT_ROOT)), str(json_path.relative_to(PROJECT_ROOT))],
            idempotency_key=f"forecast.calibration:{args.date}:{evaluation_digest}",
        )
    result = report | {"outputs": paths}
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
