#!/usr/bin/env python3
"""Capture configured core sources with the read-only agent-browser backend."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Callable

import yaml

try:
    from agent_browser_capture import capture
    from event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover
    from scripts.agent_browser_capture import capture
    from scripts.event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT_ROOT / "config" / "agent_browser_research.yaml"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "core_source_browser"
CaptureFunction = Callable[..., tuple[dict[str, Any], Path]]


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def parse_gem_page_text(text: str) -> dict[str, Any]:
    count_match = re.search(r"records\s+of\s+([\d,]+)\s+records", text, flags=re.I)
    references = []
    for reference in re.findall(r"GEM/\d{4}/[BR]/\d+", text, flags=re.I):
        reference = reference.upper()
        if reference not in references:
            references.append(reference)
    return {
        "records_reported": int(count_match.group(1).replace(",", "")) if count_match else 0,
        "sample_references": references[:10],
    }


def artifact_text(receipt: dict[str, Any]) -> str:
    value = str(receipt.get("artifacts", {}).get("page_text") or "")
    if not value:
        return ""
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    return str(data.get("text") if isinstance(data, dict) else "")


def run_core_sources(
    sources: dict[str, dict[str, Any]],
    *,
    capture_func: CaptureFunction = capture,
    output_root: Path = OUTPUT_ROOT,
) -> dict[str, Any]:
    results = []
    for source_id, source in sources.items():
        try:
            receipt, receipt_path = capture_func(
                url=source["start_url"],
                source_name=source["source_name"],
                output_root=output_root / "captures",
                record_event=True,
            )
            extracted = parse_gem_page_text(artifact_text(receipt)) if source_id == "gem" else {
                "records_reported": 0,
                "sample_references": [],
            }
            results.append(
                {
                    "source_id": source_id,
                    "source_name": source["source_name"],
                    "url": source["start_url"],
                    "status": receipt.get("status", "UNKNOWN"),
                    "blockers": receipt.get("blockers", []),
                    "capture_id": receipt.get("capture_id", ""),
                    "receipt_path": relative(receipt_path),
                    **extracted,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "source_id": source_id,
                    "source_name": source.get("source_name", source_id),
                    "url": source.get("start_url", ""),
                    "status": "FAILED",
                    "blockers": [str(exc)],
                    "capture_id": "",
                    "receipt_path": "",
                    "records_reported": 0,
                    "sample_references": [],
                }
            )
    successful = sum(str(item["status"]).startswith("COMPLETED") for item in results)
    status = "PASS" if successful == len(results) and results else "DEGRADED" if successful else "FAIL"
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    return {
        "run_id": f"COREBROWSER-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "generated_at": generated_at,
        "status": status,
        "sources_checked": len(results),
        "successful_sources": successful,
        "results": results,
        "external_business_actions": False,
        "case_creation": False,
        "safety": "Read-only browser evidence. No click, login, submit, upload, message, payment, DSC, or commercial commitment.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Core Source Agent-Browser Radar — {report['generated_at']}",
        "",
        f"Status: **{report['status']}** ({report['successful_sources']}/{report['sources_checked']} captured)",
        "",
        "| Source | Status | Records reported | Sample references | Blockers |",
        "|---|---|---:|---|---|",
    ]
    for item in report["results"]:
        lines.append(
            f"| {item['source_name']} | {item['status']} | {item['records_reported']} | "
            f"{', '.join(item['sample_references'][:3]) or 'n/a'} | {', '.join(item['blockers']) or 'none'} |"
        )
    lines.extend(["", report["safety"], ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only agent-browser captures against core sources")
    parser.add_argument("--sources", default="gem,cppp,ungm")
    parser.add_argument("--record-event", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    configured = config.get("core_sources", {})
    selected = {source_id: configured[source_id] for source_id in args.sources.split(",") if source_id in configured}
    if not selected:
        raise SystemExit("No configured core sources selected")
    report = run_core_sources(selected)
    output_dir = OUTPUT_ROOT / report["run_id"]
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    md_path = output_dir / "report.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    if args.record_event:
        citations = [relative(json_path), relative(md_path), *[item["receipt_path"] for item in report["results"] if item["receipt_path"]]]
        append_event(
            "source_adapter.scan_completed",
            "core_source_agent_browser_radar",
            object_type="source_adapter",
            object_id="core_source_agent_browser_radar",
            source="agent_browser",
            payload={
                "run_id": report["run_id"],
                "status": report["status"],
                "sources_checked": report["sources_checked"],
                "successful_sources": report["successful_sources"],
                "external_business_actions": False,
            },
            citations=citations,
            idempotency_key=f"core-source-browser:{report['run_id']}",
        )
    print(json.dumps({"status": report["status"], "sources": report["successful_sources"], "report": relative(json_path)}, indent=2))
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
