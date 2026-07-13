#!/usr/bin/env python3
"""Probe public tender sources in evidence-only mode and grade the result.

The underlying adapter runner historically exits successfully even when every
adapter produced a blocker. This canary inspects the generated evidence and
returns a failure when no non-mock adapter produced an evidence-backed record.
It never creates cases or performs credentialed/external business actions.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

try:
    from scripts.source_degradation import apply_degradation_actions, build_degradation_actions
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from source_degradation import apply_degradation_actions, build_degradation_actions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_ADAPTERS = ["cppp", "ungm", "gem"]
Runner = Callable[..., subprocess.CompletedProcess[str]]
DATEISH = re.compile(
    r"^(?:\d{1,2}[-/ ](?:[A-Za-z]{3,9}|\d{1,2})[-/ ]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})(?:\s+\d{1,2}:\d{2}(?:\s*[AP]M)?)?$",
    re.IGNORECASE,
)


def timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def python_for(project_root: Path) -> str:
    repository_python = project_root / ".venv" / "bin" / "python"
    return str(repository_python) if repository_python.is_file() else sys.executable


def opportunity_quality_issues(opportunity: dict[str, Any]) -> list[str]:
    reference = str(opportunity.get("external_reference") or "").strip()
    title = str(opportunity.get("opportunity_title") or "").strip()
    source_url = str(opportunity.get("source_url") or "").strip()
    issues: list[str] = []

    reference_upper = reference.upper()
    if (
        not reference
        or DATEISH.fullmatch(reference)
        or reference_upper.startswith(("LISTING-", "CPP-LISTING-"))
        or reference_upper in {"REQUEST", "NOTICE", "TENDER", "PROCUREMENT", "OPPORTUNITY"}
    ):
        issues.append("external_reference looks like a date or placeholder")
    letter_count = sum(character.isalpha() for character in title)
    if not title or DATEISH.fullmatch(title) or letter_count < 8 or len(title.split()) < 2:
        issues.append("opportunity_title is missing or not semantically plausible")
    if len(title) > 400 or sum(marker in title.lower() for marker in ("help center", "log in", "register", "language")) >= 2:
        issues.append("opportunity_title looks like page navigation rather than a record")
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path in {"", "/"}:
        issues.append("source_url does not identify a detail or listing path")
    return issues


def classify_adapter_payload(adapter: str, payload: dict[str, Any]) -> dict[str, Any]:
    matching_results = [
        item for item in payload.get("results", [])
        if isinstance(item, dict) and (item.get("adapter") or adapter) == adapter
    ]
    opportunities = [
        opportunity
        for item in matching_results
        for opportunity in item.get("opportunities", [])
        if isinstance(opportunity, dict)
    ]
    errors = [str(item.get("error")) for item in matching_results if item.get("error")]
    blockers = sorted(
        {
            str(opportunity.get("blocker_status"))
            for opportunity in opportunities
            if opportunity.get("blocker_status")
        }
    )
    quality_by_record = [opportunity_quality_issues(opportunity) for opportunity in opportunities]
    evidence_backed = [
        opportunity
        for opportunity, quality_issues in zip(opportunities, quality_by_record)
        if not opportunity.get("blocker_status") and not quality_issues
    ]
    quality_issues = sorted({issue for issues in quality_by_record for issue in issues})

    if errors:
        status = "ERROR"
    elif evidence_backed:
        status = "HEALTHY"
    elif blockers:
        status = "BLOCKED"
    elif opportunities:
        status = "UNPROVEN"
    else:
        status = "EMPTY"
    return {
        "adapter": adapter,
        "status": status,
        "records_seen": len(opportunities),
        "evidence_backed_records": len(evidence_backed),
        "blockers": blockers,
        "errors": errors,
        "quality_issues": quality_issues,
        "sample_citations": [
            str(item.get("source_url")) for item in evidence_backed[:3] if item.get("source_url")
        ],
    }


def run_canary(
    adapters: list[str],
    *,
    project_root: Path = PROJECT_ROOT,
    runner: Runner = subprocess.run,
    stamp: str | None = None,
    limit: int = 3,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    stamp = stamp or timestamp()
    run_dir = project_root / "outputs" / "source_canary" / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for adapter in adapters:
        output_path = run_dir / f"{adapter}.json"
        command = [
            python_for(project_root),
            "scripts/run_source_adapter.py",
            "--adapter",
            adapter,
            "--mode",
            "scan",
            "--limit",
            str(limit),
            "--evidence-only",
            "--record-event",
            "--output",
            str(output_path),
        ]
        try:
            completed = runner(
                command,
                cwd=project_root,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            results.append(
                {
                    "adapter": adapter,
                    "status": "ERROR",
                    "records_seen": 0,
                    "evidence_backed_records": 0,
                    "blockers": [],
                    "errors": [f"timed out after {timeout_seconds}s"],
                    "quality_issues": [],
                    "sample_citations": [],
                    "exit_code": 124,
                }
            )
            continue

        if completed.returncode != 0:
            result = {
                "adapter": adapter,
                "status": "ERROR",
                "records_seen": 0,
                "evidence_backed_records": 0,
                "blockers": [],
                "errors": [(completed.stderr or completed.stdout or "adapter failed")[-1000:]],
                "quality_issues": [],
                "sample_citations": [],
            }
        elif not output_path.is_file():
            result = {
                "adapter": adapter,
                "status": "ERROR",
                "records_seen": 0,
                "evidence_backed_records": 0,
                "blockers": [],
                "errors": ["adapter returned success without an output artifact"],
                "quality_issues": [],
                "sample_citations": [],
            }
        else:
            try:
                result = classify_adapter_payload(adapter, json.loads(output_path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError) as exc:
                result = {
                    "adapter": adapter,
                    "status": "ERROR",
                    "records_seen": 0,
                    "evidence_backed_records": 0,
                    "blockers": [],
                    "errors": [f"invalid adapter artifact: {exc}"],
                    "quality_issues": [],
                    "sample_citations": [],
                }
        result["exit_code"] = completed.returncode
        result["artifact_path"] = str(output_path.relative_to(project_root))
        results.append(result)

    healthy = sum(item["status"] == "HEALTHY" for item in results)
    errors = sum(item["status"] == "ERROR" for item in results)
    if healthy == len(results) and results:
        status = "PASS"
    elif healthy:
        status = "DEGRADED"
    else:
        status = "FAIL"
    return {
        "run_id": f"CANARY-{stamp}",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "adapters_checked": len(results),
        "healthy_adapters": healthy,
        "adapter_errors": errors,
        "results": results,
        "external_business_actions": False,
        "case_creation": False,
        "approval_boundary": "Public evidence-only probes; no login, send, submission, payment, DSC, or commercial commitment.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Live Source Canary — {report['generated_at']}",
        "",
        f"Status: **{report['status']}**",
        f"Healthy adapters: {report['healthy_adapters']}/{report['adapters_checked']}",
        "",
        "| Adapter | Status | Records | Evidence-backed | Blockers / errors |",
        "|---|---:|---:|---:|---|",
    ]
    for item in report["results"]:
        detail = "; ".join([*item["blockers"], *item["errors"], *item.get("quality_issues", [])]) or "none"
        lines.append(
            f"| {item['adapter']} | {item['status']} | {item['records_seen']} | "
            f"{item['evidence_backed_records']} | {detail} |"
        )
    lines.extend(["", report["approval_boundary"], ""])
    return "\n".join(lines)


def write_report(report: dict[str, Any], project_root: Path = PROJECT_ROOT) -> tuple[Path, Path]:
    stamp = report["run_id"].removeprefix("CANARY-")
    output_dir = project_root / "outputs" / "source_canary" / stamp
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "canary_report.json"
    markdown_path = output_dir / "canary_report.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def load_source_health(path: Path = DATA_DIR / "source_health.csv") -> list[dict[str, str]]:
    import csv

    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapters", default=",".join(DEFAULT_ADAPTERS), help="Comma-separated non-mock adapter names")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=180, help="Per-adapter timeout seconds")
    parser.add_argument("--degradation-threshold", type=int, default=3)
    parser.add_argument("--record-degradation", action="store_true", help="Emit deduplicated degradation events and repair cards")
    args = parser.parse_args()

    adapters = [item.strip() for item in args.adapters.split(",") if item.strip()]
    if not adapters or "mock" in adapters:
        print("Live canary requires at least one non-mock adapter", file=sys.stderr)
        return 2
    report = run_canary(adapters, limit=args.limit, timeout_seconds=args.timeout)
    json_path, _ = write_report(report)
    receipt_path = str(json_path.relative_to(PROJECT_ROOT))
    actions = build_degradation_actions(
        load_source_health(),
        report["results"],
        threshold=args.degradation_threshold,
        receipt_path=receipt_path,
    )
    report["degradation_threshold"] = args.degradation_threshold
    report["degradation_actions"] = actions
    report["degradation_actions_applied"] = (
        apply_degradation_actions(actions) if args.record_degradation else []
    )
    report["kanban_mutated"] = bool(report["degradation_actions_applied"])
    write_report(report)
    print(f"Live source canary {report['status']}: {json_path}")
    print(f"Healthy adapters: {report['healthy_adapters']}/{report['adapters_checked']}")
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
