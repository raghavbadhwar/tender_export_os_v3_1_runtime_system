#!/usr/bin/env python3
"""Build weekly forecast-quality report with separated target populations."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from scripts.evaluate_forecast_calibration import evaluate_rows
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from evaluate_forecast_calibration import evaluate_rows


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "demand_forecasting"


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def upper(value: Any) -> str:
    return clean(value).upper()


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def target_key(row: dict[str, Any]) -> tuple[str, str]:
    return clean(row.get("target_id")) or "UNKNOWN_TARGET", upper(row.get("workflow_type")) or "UNKNOWN_WORKFLOW"


def build_report(
    *,
    forecasts: list[dict[str, Any]],
    backtests: list[dict[str, Any]],
    source_health: list[dict[str, Any]],
    week_ending: str,
) -> dict[str, Any]:
    calibration = evaluate_rows(backtests, forecast_rows=forecasts)
    populations: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {
        "target_id": "",
        "workflow_type": "",
        "forecast_count": 0,
        "immature_count": 0,
        "proof_gap_counts": Counter(),
        "feature_schema_hashes": Counter(),
        "source_counts": Counter(),
    })
    backtest_by_forecast = {clean(row.get("forecast_id")): row for row in backtests}
    for forecast in forecasts:
        key = target_key(forecast)
        bucket = populations[key]
        bucket["target_id"], bucket["workflow_type"] = key
        bucket["forecast_count"] += 1
        proof_gap = clean(forecast.get("proof_gap")) or "none_recorded"
        bucket["proof_gap_counts"][proof_gap] += 1
        feature_hash = clean(forecast.get("feature_schema_hash")) or "missing_feature_schema_hash"
        bucket["feature_schema_hashes"][feature_hash] += 1
        source = clean(forecast.get("source_name")) or "UNKNOWN_SOURCE"
        bucket["source_counts"][source] += 1
        backtest = backtest_by_forecast.get(clean(forecast.get("forecast_id")), {})
        if upper(backtest.get("is_mature")) != "TRUE":
            bucket["immature_count"] += 1

    target_populations: list[dict[str, Any]] = []
    for bucket in populations.values():
        hashes = bucket["feature_schema_hashes"]
        target_populations.append(
            {
                "target_id": bucket["target_id"],
                "workflow_type": bucket["workflow_type"],
                "forecast_count": bucket["forecast_count"],
                "immature_count": bucket["immature_count"],
                "top_proof_gaps": dict(bucket["proof_gap_counts"].most_common(5)),
                "feature_schema_variants": len(hashes),
                "feature_drift_status": "DRIFT_REVIEW" if len(hashes) > 1 else "STABLE",
                "top_sources": dict(bucket["source_counts"].most_common(5)),
            }
        )

    source_drift = [
        {
            "source_name": clean(row.get("source_name")) or clean(row.get("url")) or "UNKNOWN_SOURCE",
            "workflow": upper(row.get("workflow")),
            "health_status": clean(row.get("health_status")),
            "consecutive_failures": clean(row.get("consecutive_failures")) or "0",
            "recommended_gap_action": "Fix adapter/access issue or downgrade to manual watch lane.",
        }
        for row in source_health
        if upper(row.get("health_status")) in {"PAYWALLED", "LOGIN_REQUIRED", "BLOCKED", "FAILING"}
        or clean(row.get("consecutive_failures")) not in {"", "0"}
    ]

    calibration_by_key = {
        (item["target_id"], upper(item["workflow_type"])): item for item in calibration.get("target_evaluations", [])
    }
    collection_gaps = []
    for population in target_populations:
        key = (population["target_id"], upper(population["workflow_type"]))
        calibration_row = calibration_by_key.get(key, {})
        collection_gaps.append(
            {
                "target_id": population["target_id"],
                "workflow_type": population["workflow_type"],
                "mature_sample_size": calibration_row.get("mature_sample_size", 0),
                "calibration_status": calibration_row.get("status", "PRIOR_UNCALIBRATED"),
                "immature_count": population["immature_count"],
                "largest_proof_gap": next(iter(population["top_proof_gaps"]), ""),
                "actionable_collection_gap": "Record verified time-separated outcomes and close proof gaps before calibration/training claims.",
            }
        )

    return {
        "week_ending": week_ending,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "safety_boundary": "Weekly forecast-quality review only. No mixed GOV/EXPORT probability claims and no external action.",
        "target_populations": sorted(target_populations, key=lambda item: (item["workflow_type"], item["target_id"])),
        "calibration_state": calibration,
        "source_drift": source_drift,
        "actionable_collection_gaps": sorted(collection_gaps, key=lambda item: (item["workflow_type"], item["target_id"])),
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        f"# Weekly Forecast Quality Report - {report['week_ending']}",
        "",
        report["safety_boundary"],
        "",
        "| Target | Workflow | Forecasts | Immature | Feature drift | Top proof gaps |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in report["target_populations"]:
        lines.append(
            f"| {row['target_id']} | {row['workflow_type']} | {row['forecast_count']} | {row['immature_count']} | "
            f"{row['feature_drift_status']} | {json.dumps(row['top_proof_gaps'], ensure_ascii=False)} |"
        )
    lines.extend(["", "## Source drift"])
    if report["source_drift"]:
        for row in report["source_drift"]:
            lines.append(f"- {row['source_name']} ({row['workflow']}): {row['health_status']} / failures={row['consecutive_failures']}")
    else:
        lines.append("- No degraded source drift found in current source_health.csv.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forecasts", default=str(DATA_DIR / "forecast_candidates.csv"))
    parser.add_argument("--backtests", default=str(DATA_DIR / "forecast_backtests.csv"))
    parser.add_argument("--source-health", default=str(DATA_DIR / "source_health.csv"))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--week-ending", default=dt.date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_report(
        forecasts=load_csv(Path(args.forecasts).expanduser().resolve()),
        backtests=load_csv(Path(args.backtests).expanduser().resolve()),
        source_health=load_csv(Path(args.source_health).expanduser().resolve()),
        week_ending=args.week_ending,
    )
    outputs: dict[str, str] = {}
    if args.write:
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = args.week_ending.replace("-", "")
        json_path = output_dir / f"weekly_forecast_quality_{stamp}.json"
        md_path = output_dir / f"weekly_forecast_quality_{stamp}.md"
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_markdown(md_path, report)
        outputs = {"json": rel(json_path), "markdown": rel(md_path)}
    payload = report | {"outputs": outputs}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
