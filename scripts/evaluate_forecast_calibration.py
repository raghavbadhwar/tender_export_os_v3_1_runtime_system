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
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKTEST_PATH = PROJECT_ROOT / "data" / "forecast_backtests.csv"
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


def evaluate_rows(rows: list[dict[str, Any]], minimum_sample: int = 30) -> dict[str, Any]:
    mature: list[tuple[float, int, str]] = []
    for row in rows:
        probability = safe_probability(row.get("predicted_probability"))
        outcome = str(row.get("binary_outcome", "")).strip()
        if not as_bool(row.get("is_mature")) or probability is None or outcome not in {"0", "1"}:
            continue
        mature.append((probability, int(outcome), str(row.get("model_version") or "unknown")))

    brier = sum((probability - outcome) ** 2 for probability, outcome, _ in mature) / len(mature) if mature else None
    hit_rate = sum(outcome for _, outcome, _ in mature) / len(mature) if mature else None
    bins: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for probability, outcome, _ in mature:
        lower = min(0.8, int(probability * 5) / 5)
        upper = min(1.0, lower + 0.2)
        bins[f"{lower:.1f}-{upper:.1f}"].append((probability, outcome))
    calibration_bins = [
        {
            "range": label,
            "count": len(values),
            "mean_predicted_probability": round(sum(value[0] for value in values) / len(values), 4),
            "observed_success_rate": round(sum(value[1] for value in values) / len(values), 4),
        }
        for label, values in sorted(bins.items())
    ]
    models: dict[str, int] = defaultdict(int)
    for _, _, model in mature:
        models[model] += 1
    return {
        "status": "CALIBRATION_MEASURED" if len(mature) >= minimum_sample else "INSUFFICIENT_MATURE_SAMPLE",
        "minimum_mature_sample": minimum_sample,
        "mature_sample_size": len(mature),
        "excluded_unmatured_or_unscored": len(rows) - len(mature),
        "brier_score": round(brier, 6) if brier is not None else None,
        "observed_success_rate": round(hit_rate, 4) if hit_rate is not None else None,
        "calibration_bins": calibration_bins,
        "model_sample_sizes": dict(sorted(models.items())),
        "interpretation": (
            "Measured on enough mature outcomes; use bins and Brier score for model revision."
            if len(mature) >= minimum_sample
            else "Do not call these probabilities calibrated yet; keep collecting mature outcomes."
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
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate TEOS forecast calibration")
    parser.add_argument("--backtests", default=str(BACKTEST_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--minimum-sample", type=int, default=30)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    backtests = Path(args.backtests).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    report = evaluate_rows(load_csv(backtests), minimum_sample=max(1, args.minimum_sample))
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
            citations=[str(backtests.relative_to(PROJECT_ROOT)), str(json_path.relative_to(PROJECT_ROOT))],
            idempotency_key=f"forecast.calibration:{args.date}:{evaluation_digest}",
        )
    result = report | {"outputs": paths}
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
