#!/usr/bin/env python3
"""7-day V5 demand/low-competition shadow-run harness."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = PROJECT_ROOT / "scripts" / "generate_v5_demand_forecast_low_competition.py"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "demand_forecasting" / "shadow_harness"

WEAK_EVIDENCE = {
    "",
    "RAW_LEAD",
    "MISSING",
    "RESEARCH_ONLY_NOT_RFQ",
    "PUBLIC_LISTING_ONLY",
    "LOW_EVIDENCE",
    "UNKNOWN",
    "MARKETPLACE_MASKED",
}
EXTERNAL_WORDS = {"send", "contact", "submit", "upload", "pay", "dsc", "commit", "invoice", "purchase order"}


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def date_range(days: int, end_date: dt.date | None = None) -> list[str]:
    end_date = end_date or dt.date.today()
    start = end_date - dt.timedelta(days=days - 1)
    return [(start + dt.timedelta(days=index)).strftime("%Y%m%d") for index in range(days)]


def norm_upper(value: Any) -> str:
    return str(value or "").strip().upper()


def action_has_external_words(value: Any) -> bool:
    text = str(value or "").lower()
    return any(word in text for word in EXTERNAL_WORDS)


def forecast_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in (
        "active_case_forecasts",
        "research_forecasts",
        "low_competition_candidates",
        "buyer_repeat_predictions",
        "category_demand_predictions",
        "killed_or_not_ready",
    ):
        value = payload.get(key, [])
        if isinstance(value, list):
            rows.extend(item for item in value if isinstance(item, dict))
    return rows


def summarize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = forecast_rows(payload)
    weak_rows = [
        row for row in rows
        if norm_upper(row.get("evidence_label") or row.get("evidence_level")) in WEAK_EVIDENCE
    ]
    unsafe_weak_actions = [row for row in weak_rows if action_has_external_words(row.get("next_safe_action") or row.get("recommended_next_action"))]
    proof_required = int(payload.get("summary", {}).get("proof_required_candidates", 0) or 0)
    weak_promotions_avoided = sum(
        1 for row in weak_rows
        if not row.get("bid_ready") and not action_has_external_words(row.get("next_safe_action") or row.get("recommended_next_action"))
    )
    return {
        "run_id": payload.get("run_id", ""),
        "date": payload.get("date", ""),
        "forecast_rows": len(rows),
        "weak_evidence_rows": len(weak_rows),
        "proof_required_candidates": proof_required,
        "weak_promotions_avoided": weak_promotions_avoided,
        "unsafe_weak_actions": len(unsafe_weak_actions),
        "proof_gated_status": "PASS" if not unsafe_weak_actions else "BLOCKED",
        "next_action": "Continue shadow mode and capture missing proof before promotion." if not unsafe_weak_actions else "Fix unsafe weak-evidence recommendations before any operational promotion.",
    }


def run_generator(date_str: str, output_dir: Path) -> dict[str, Any]:
    if not GENERATOR.exists():
        return {"date": date_str, "ok": False, "returncode": None, "error": "forecast generator missing"}
    day_dir = output_dir / date_str
    day_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["python3", str(GENERATOR), "--date", date_str, "--output-dir", str(day_dir)],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
        check=False,
    )
    payload_path = day_dir / f"v5_demand_forecast_low_competition_{date_str}.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8")) if payload_path.exists() else {}
    return {
        "date": date_str,
        "ok": completed.returncode == 0 and bool(payload),
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
        "payload_path": display_path(payload_path) if payload_path.exists() else "",
        "summary": summarize_payload(payload) if payload else {},
    }


def build_shadow_report(days: int, output_dir: Path, *, run_existing_generator: bool = True, end_date: dt.date | None = None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    runs = []
    for date_str in date_range(days, end_date=end_date):
        if run_existing_generator:
            runs.append(run_generator(date_str, output_dir))
            continue
        payload_path = output_dir / date_str / f"v5_demand_forecast_low_competition_{date_str}.json"
        payload = json.loads(payload_path.read_text(encoding="utf-8")) if payload_path.exists() else {}
        runs.append({
            "date": date_str,
            "ok": bool(payload),
            "returncode": 0 if payload else None,
            "payload_path": display_path(payload_path) if payload else "",
            "summary": summarize_payload(payload) if payload else {},
        })

    blocked = [
        run for run in runs
        if not run.get("ok") or run.get("summary", {}).get("proof_gated_status") == "BLOCKED"
    ]
    weak_promotions_avoided = sum(int(run.get("summary", {}).get("weak_promotions_avoided", 0) or 0) for run in runs)
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "days": days,
        "generator_present": GENERATOR.exists(),
        "generator_run_enabled": run_existing_generator,
        "status": "PASS" if not blocked else "BLOCKED",
        "runs": runs,
        "weak_promotions_avoided": weak_promotions_avoided,
        "next_action": "Keep V5 forecast in shadow mode; stage only proof-backed candidates for Hermes review.",
        "delivery_enabled": False,
        "safety_note": "Shadow-run only. No external delivery, buyer/supplier contact, portal login, submission, upload, payment, DSC, or final commercial/compliance claim.",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# V5 Forecast Shadow Harness",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Days: {report['days']}",
        f"- Status: **{report['status']}**",
        f"- Weak promotions avoided: {report['weak_promotions_avoided']}",
        f"- Delivery enabled: {report['delivery_enabled']}",
        "",
        report["safety_note"],
        "",
        "| Date | OK | Proof gate | Weak rows | Weak promotions avoided | Payload |",
        "|---|---:|---|---:|---:|---|",
    ]
    for run in report["runs"]:
        summary = run.get("summary", {})
        lines.append(
            f"| {run['date']} | {run.get('ok')} | {summary.get('proof_gated_status', 'NO_OUTPUT')} | "
            f"{summary.get('weak_evidence_rows', 0)} | {summary.get('weak_promotions_avoided', 0)} | `{run.get('payload_path', '')}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run/read the V5 forecast shadow harness")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--no-run-generator", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    report = build_shadow_report(args.days, output_dir, run_existing_generator=not args.no_run_generator)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"v5_shadow_harness_{stamp}.json"
    md_path = output_dir / f"v5_shadow_harness_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, report)
    payload = {"status": report["status"], "json": display_path(json_path), "markdown": display_path(md_path), "delivery_enabled": False}
    print(json.dumps(payload, indent=2) if args.json else f"V5 shadow harness {report['status']}: {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
