#!/usr/bin/env python3
"""Rescore saved Hermes behavioral raw responses against the current spec."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_hermes_behavioral_contracts import (  # noqa: E402
    build_report,
    evaluate_response,
    load_spec,
    parse_model_response,
)


DEFAULT_SPEC = PROJECT_ROOT / "config" / "hermes_behavioral_eval.yaml"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "hermes_behavioral_eval_rescored"


def load_report(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def rescore_report(*, source_report: dict[str, Any], spec: dict[str, Any], run_id: str) -> dict[str, Any]:
    profile = str(source_report.get("profile") or spec.get("profile") or "").strip()
    if not profile:
        raise ValueError("source report has no profile")
    profile_spec = dict(spec)
    profile_spec["profile"] = profile
    rescored_runs: list[dict[str, Any]] = []
    for run in source_report.get("runs") or []:
        raw = str(run.get("raw_response") or "")
        parsed = parse_model_response(raw)
        cases = evaluate_response(profile_spec["scenarios"], parsed)
        rescored_runs.append(
            {
                "repeat": run.get("repeat"),
                "ok": all(item["ok"] for item in cases),
                "duration_seconds": run.get("duration_seconds", 0),
                "error": "",
                "cases": cases,
                "usage": run.get("usage", {}),
                "raw_response": raw,
            }
        )
    report = build_report(profile_spec, rescored_runs, run_id)
    report["rescored_from"] = source_report.get("run_id") or ""
    report["rescored_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    return report


def write_report(report: dict[str, Any], output_root: Path) -> Path:
    profile = str(report["profile"])
    run_id = "HBRESCORE-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + profile
    output_dir = output_root / run_id / profile
    output_dir.mkdir(parents=True, exist_ok=False)
    path = output_dir / "report.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    parser.add_argument("--spec", default=str(DEFAULT_SPEC))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    source_path = Path(args.report).expanduser()
    if not source_path.is_absolute():
        source_path = PROJECT_ROOT / source_path
    output_root = Path(args.output_root).expanduser()
    if not output_root.is_absolute():
        output_root = PROJECT_ROOT / output_root
    report = rescore_report(
        source_report=load_report(source_path),
        spec=load_spec(Path(args.spec).expanduser()),
        run_id=f"RESCORED-{source_path.parent.name}",
    )
    path = write_report(report, output_root)
    payload = {"status": report["status"], "profile": report["profile"], "case_pass_rate": report["case_pass_rate"], "report": str(path)}
    print(json.dumps(payload, indent=2) if args.json else f"Rescored {report['profile']} {report['status']}: {path}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
