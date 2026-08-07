#!/usr/bin/env python3
"""Evaluate current artifacts against champion artifact metrics."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - direct CLI dependency error
    yaml = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "artifact_evaluation_champions.yaml"


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load artifact evaluation config")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"artifact evaluation config must be a mapping: {path}")
    return value


def number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def metric_errors(case: dict[str, Any], dimension_config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    champion = case.get("champion_metrics") if isinstance(case.get("champion_metrics"), dict) else {}
    current = case.get("current_metrics") if isinstance(case.get("current_metrics"), dict) else {}
    for metric in dimension_config.get("higher_is_better", []):
        if number(current.get(metric)) < number(champion.get(metric)):
            errors.append(f"{metric} regressed below champion")
    for metric in dimension_config.get("lower_is_better", []):
        if number(current.get(metric)) > number(champion.get(metric)):
            errors.append(f"{metric} regressed above champion")
    if number(case.get("current_score")) < number(case.get("champion_score")):
        errors.append("current_score regressed below champion_score")
    if number(case.get("current_score")) < number(dimension_config.get("minimum_current_score")):
        errors.append("current_score is below minimum_current_score")
    return errors


def evaluate_cases(cases: list[dict[str, Any]], *, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    dimensions = config.get("dimensions") if isinstance(config.get("dimensions"), dict) else {}
    required_dimensions = set(dimensions)
    seen_dimensions = {clean(case.get("dimension")) for case in cases}
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for case in cases:
        dimension = clean(case.get("dimension"))
        if dimension not in dimensions:
            case_errors = [f"unknown dimension: {dimension}"]
        else:
            case_errors = metric_errors(case, dimensions[dimension])
        status = "PASS" if not case_errors else "FAIL"
        if case_errors:
            errors.extend(f"{dimension}: {error}" for error in case_errors)
        results.append(
            {
                "dimension": dimension,
                "artifact_id": clean(case.get("artifact_id")),
                "champion_id": clean(case.get("champion_id")),
                "current_id": clean(case.get("current_id")),
                "status": status,
                "errors": case_errors,
                "champion_score": number(case.get("champion_score")),
                "current_score": number(case.get("current_score")),
            }
        )
    missing_dimensions = sorted(required_dimensions - seen_dimensions)
    errors.extend(f"missing evaluation dimension: {dimension}" for dimension in missing_dimensions)
    return {
        "schema_version": "artifact_champion_evaluation.v1",
        "generated_at": utc_now(),
        "status": "PASS" if not errors else "FAIL",
        "evaluated_count": len(cases),
        "results": results,
        "errors": errors,
        "external_actions_executed": False,
        "boundary": clean(config.get("boundary")),
    }


def write_report(report: dict[str, Any], *, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON file containing a list of evaluation cases")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--output", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    input_path = Path(args.input).expanduser()
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    value = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise SystemExit("input must be a JSON list of objects")
    config = load_config(Path(args.config).expanduser())
    report = evaluate_cases(value, config=config)
    output = args.output
    if output:
        output_path = Path(output).expanduser()
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path
        write_report(report, output_path=output_path)
        report["output_path"] = str(output_path)
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else f"Artifact champion evaluation: {report['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
