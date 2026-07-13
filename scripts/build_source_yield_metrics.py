#!/usr/bin/env python3
"""Build source-yield metrics from local Tender Export OS ledgers."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from scripts.quote_proof import strict_quote_proofs
    from scripts.source_degradation import apply_degradation_actions, build_degradation_actions
except ModuleNotFoundError:  # pragma: no cover
    from quote_proof import strict_quote_proofs
    from source_degradation import apply_degradation_actions, build_degradation_actions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "source_yield"

PROMOTED_STATUSES = {"DEEP_READ", "SUPPLIER_SEARCH", "PRICING_READY", "ARTIFACT_PRODUCTION", "APPROVAL_REQUIRED", "APPROVED", "SENT_OR_SUBMITTED", "WON"}
REJECTED_STATUSES = {"REJECTED", "FAST_KILL", "LOST", "ARCHIVED"}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def safe_int(value: Any) -> int:
    try:
        return int(float(str(value or "0").replace(",", "")))
    except ValueError:
        return 0


def norm(value: Any) -> str:
    return str(value or "").strip()


def norm_upper(value: Any) -> str:
    return norm(value).upper()


def recommended_action(metric: dict[str, Any]) -> str:
    if metric["access_friction"]:
        return "Fix access friction or keep source in manual/watch lane."
    if metric["checks"] >= 5 and metric["leads_or_cases"] == 0:
        return "Reduce scan frequency or refine source adapter/query."
    if metric["rejected_cases"] > metric["promoted_cases"] and metric["leads_or_cases"] >= 3:
        return "Tighten source filters and kill-rule prechecks."
    if metric["strict_quote_proof_cases"] or metric["promoted_cases"]:
        return "Keep source active; prioritize proof capture and dedupe."
    return "Continue low-frequency monitoring until proof quality improves."


def build_metrics(
    source_health: list[dict[str, str]],
    cases: list[dict[str, str]],
    run_rows: list[dict[str, str]],
    quotes: list[dict[str, str]],
    approvals: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_source: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "source_name": "",
        "source_type": "",
        "workflow": "",
        "checks": 0,
        "leads_or_cases": 0,
        "promoted_cases": 0,
        "rejected_cases": 0,
        "approval_rows": 0,
        "strict_quote_proof_cases": 0,
        "access_friction": False,
        "consecutive_failures": 0,
        "access_friction_notes": [],
        "useful_lead_quality_proxy": 0,
        "recommended_action": "",
    })

    for row in source_health:
        source = row.get("source_name", "") or row.get("url", "") or "UNKNOWN_SOURCE"
        metric = by_source[source]
        metric["source_name"] = source
        metric["source_type"] = row.get("source_type", "")
        metric["workflow"] = row.get("workflow", "")
        metric["checks"] += safe_int(row.get("total_checks")) or safe_int(row.get("records_found"))
        metric["consecutive_failures"] = max(metric["consecutive_failures"], safe_int(row.get("consecutive_failures")))
        friction = norm_upper(row.get("login_required")) == "TRUE" or norm_upper(row.get("paywalled")) == "TRUE" or safe_int(row.get("consecutive_failures")) > 0
        if friction or norm_upper(row.get("health_status")) in {"PAYWALLED", "LOGIN_REQUIRED", "BLOCKED", "FAILING"}:
            metric["access_friction"] = True
            metric["access_friction_notes"].append(row.get("health_status") or row.get("notes") or "access friction")

    case_to_source: dict[str, str] = {}
    for case in cases:
        source = case.get("source_name", "") or "UNKNOWN_SOURCE"
        metric = by_source[source]
        metric["source_name"] = source
        case_to_source[case.get("case_id", "")] = source
        metric["leads_or_cases"] += 1
        status = norm_upper(case.get("status"))
        if status in PROMOTED_STATUSES:
            metric["promoted_cases"] += 1
        if status in REJECTED_STATUSES:
            metric["rejected_cases"] += 1

    approvals_by_case = defaultdict(int)
    for approval in approvals:
        if approval.get("case_id"):
            approvals_by_case[approval["case_id"]] += 1
    for case_id, count in approvals_by_case.items():
        source = case_to_source.get(case_id)
        if source:
            by_source[source]["approval_rows"] += count

    for case_id, source in case_to_source.items():
        if strict_quote_proofs(case_id, quotes):
            by_source[source]["strict_quote_proof_cases"] += 1

    run_checks = sum(safe_int(row.get("sources_checked")) for row in run_rows)
    if run_checks and not source_health:
        by_source["RUN_LOG_AGGREGATE"]["source_name"] = "RUN_LOG_AGGREGATE"
        by_source["RUN_LOG_AGGREGATE"]["checks"] = run_checks

    metrics = []
    for metric in by_source.values():
        checks = max(metric["checks"], 1)
        useful = metric["promoted_cases"] + metric["strict_quote_proof_cases"] + metric["approval_rows"]
        metric["useful_lead_quality_proxy"] = round(100 * useful / checks, 2)
        metric["recommended_action"] = recommended_action(metric)
        metric["access_friction_notes"] = sorted(set(item for item in metric["access_friction_notes"] if item))[:5]
        metrics.append(dict(metric))
    return sorted(metrics, key=lambda item: (item["useful_lead_quality_proxy"], item["leads_or_cases"]), reverse=True)


def write_csv_report(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "source_name",
        "source_type",
        "workflow",
        "checks",
        "leads_or_cases",
        "promoted_cases",
        "rejected_cases",
        "approval_rows",
        "strict_quote_proof_cases",
        "access_friction",
        "consecutive_failures",
        "useful_lead_quality_proxy",
        "recommended_action",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def write_markdown(path: Path, rows: list[dict[str, Any]], generated_at: str) -> None:
    lines = [
        "# Source Yield Metrics",
        "",
        f"- Generated at: {generated_at}",
        "- Safety: read-only metrics; no source login, outreach, submission, upload, payment, DSC, or external action.",
        "",
        "| Source | Checks | Cases | Promoted | Rejected | Strict quote proof cases | Quality proxy | Recommended action |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['source_name']} | {row['checks']} | {row['leads_or_cases']} | {row['promoted_cases']} | "
            f"{row['rejected_cases']} | {row['strict_quote_proof_cases']} | {row['useful_lead_quality_proxy']} | {row['recommended_action']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report() -> dict[str, Any]:
    rows = build_metrics(
        load_csv(DATA_DIR / "source_health.csv"),
        load_csv(DATA_DIR / "master_cases.csv"),
        load_csv(DATA_DIR / "agent_run_log.csv"),
        load_csv(DATA_DIR / "quote_master.csv"),
        load_csv(DATA_DIR / "approvals_receipts.csv"),
    )
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_count": len(rows),
        "metrics": rows,
        "safety_note": "Read-only source-yield report. No external action executed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build source-yield metrics from local ledgers")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--degradation-threshold", type=int, default=3)
    parser.add_argument("--record-degradation", action="store_true")
    args = parser.parse_args()

    report = build_report()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"source_yield_metrics_{stamp}.json"
    csv_path = output_dir / f"source_yield_metrics_{stamp}.csv"
    md_path = output_dir / f"source_yield_metrics_{stamp}.md"
    receipt_path = display_path(json_path)
    health_rows = load_csv(DATA_DIR / "source_health.csv")
    metric_results = [
        {
            "adapter": row["source_name"],
            "source_name": row["source_name"],
            "status": "FAILING" if row.get("consecutive_failures", 0) >= args.degradation_threshold else "HEALTHY",
        }
        for row in report["metrics"]
    ]
    actions = build_degradation_actions(
        health_rows,
        metric_results,
        threshold=args.degradation_threshold,
        receipt_path=receipt_path,
        increment_failure=False,
    )
    report["degradation_threshold"] = args.degradation_threshold
    report["degradation_actions"] = actions
    report["degradation_actions_applied"] = apply_degradation_actions(actions) if args.record_degradation else []
    report["kanban_mutated"] = bool(report["degradation_actions_applied"])
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv_report(csv_path, report["metrics"])
    write_markdown(md_path, report["metrics"], report["generated_at"])
    payload = {"source_count": report["source_count"], "json": display_path(json_path), "csv": display_path(csv_path), "markdown": display_path(md_path)}
    print(json.dumps(payload, indent=2) if args.json else f"Source-yield metrics wrote {display_path(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
