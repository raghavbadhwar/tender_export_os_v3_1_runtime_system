#!/usr/bin/env python3
"""Run source adapters in safe output/evidence-only mode by default."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from pathlib import Path

from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "source_runs"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.source_adapters.adapter_registry import ADAPTERS, create_adapter  # noqa: E402
from scripts.source_runtime.credential_policy import sanitize_payload  # noqa: E402
from scripts.source_runtime.deep_source_result import to_plain_dict, write_json  # noqa: E402
from scripts.source_runtime.source_health import append_source_health_event, upsert_source_health_csv  # noqa: E402


def run_id() -> str:
    return f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


def record_event(enabled: bool, event_type: str, adapter_name: str, payload: dict, citations: list[str] | None = None, case_id: str = "") -> None:
    if not enabled:
        return
    append_event(
        event_type,
        "run_source_adapter",
        case_id=case_id,
        object_type="source_adapter",
        object_id=adapter_name,
        source=adapter_name,
        payload=sanitize_payload(payload),
        citations=citations or [],
    )


def is_blocked(item: dict) -> bool:
    return bool(item.get("blocker_status") or item.get("shallow", {}).get("blocker_status"))


def source_health_should_update(blockers: list[str]) -> bool:
    runtime_blockers = {"CODEX_RUNTIME_OR_PLAYWRIGHT_UNAVAILABLE", "BROWSER_DISABLED_BY_ENV"}
    return not blockers or any(blocker not in runtime_blockers for blocker in blockers)


def adapter_names(selected: str) -> list[str]:
    if selected == "all":
        return list(ADAPTERS)
    return [selected]


def load_adapter(name: str, args: argparse.Namespace, run: str):
    return create_adapter(
        name,
        keyword=args.keyword or "",
        limit=args.limit,
        headless=not args.headful,
        run_id=run,
        evidence_only=args.evidence_only,
    )


def run_scan(name: str, args: argparse.Namespace, run: str) -> dict:
    record_event(args.record_event, "source_adapter.scan_started", name, {"mode": "scan", "keyword": args.keyword, "limit": args.limit})
    adapter = load_adapter(name, args, run)
    opportunities = [item.to_dict() for item in adapter.scan()[: args.limit]]
    blocked = [item for item in opportunities if item.get("blocker_status")]
    record_event(
        args.record_event,
        "source_adapter.scan_completed",
        name,
        {"opportunities": len(opportunities), "blocked": len(blocked)},
        citations=[item.get("source_url", "") for item in opportunities],
    )
    for item in blocked:
        record_event(args.record_event, "source_adapter.blocked", name, item, citations=item.get("citations", []))
    status = "Manual Check Required" if blocked and len(blocked) == len(opportunities) else "Working"
    if blocked and any("CAPTCHA" in item.get("blocker_status", "") for item in blocked):
        status = "Blocked by CAPTCHA"
    source_display_name = getattr(adapter, "source_name", name)
    blocker_reasons = [item.get("blocker_status", "") for item in blocked]
    if name != "mock" and source_health_should_update(blocker_reasons):
        upsert_source_health_csv(source_display_name, {"health_status": status, "notes": f"Deep source scan run {run}: records_found={len(opportunities)} blockers={len(blocked)}"})
        if args.record_event:
            append_source_health_event(source_display_name, {"health_status": status, "last_attempted_at": run, "records_found": len(opportunities), "blocker_type": ",".join(blocker_reasons)})
    return {"adapter": name, "mode": "scan", "opportunities": opportunities}


def run_deep(name: str, args: argparse.Namespace, run: str) -> dict:
    adapter = load_adapter(name, args, run)
    record_event(args.record_event, "source_adapter.scan_started", name, {"mode": "deep_pre_scan", "keyword": args.keyword, "limit": args.limit})
    opportunities = adapter.scan()[: args.limit]
    record_event(args.record_event, "source_adapter.scan_completed", name, {"opportunities": len(opportunities)}, citations=[item.source_url for item in opportunities])
    deep_results = []
    for opportunity in opportunities:
        record_event(args.record_event, "source_adapter.deep_read_started", name, opportunity.to_dict(), citations=opportunity.citations)
        result = adapter.deep_read(opportunity)
        result_dict = to_plain_dict(result)
        deep_results.append(result_dict)
        citations = result_dict.get("citations", [])
        if result_dict.get("blocker_status"):
            record_event(args.record_event, "source_adapter.blocked", name, result_dict, citations=citations)
        for document in result_dict.get("documents", []):
            record_event(args.record_event, "source_adapter.document_downloaded", name, document, citations=[document.get("local_path", ""), document.get("source_url", "")])
            record_event(args.record_event, "source_adapter.document_parse_completed", name, document, citations=[document.get("extracted_text_path", "")])
        record_event(args.record_event, "source_adapter.extraction_completed", name, result_dict.get("extracted", {}), citations=citations)
        if not result_dict.get("blocker_status"):
            record_event(args.record_event, "source_adapter.case_candidate_created", name, {"external_reference": opportunity.external_reference, "evidence_dir": result_dict.get("evidence_dir", "")}, citations=citations)
        record_event(args.record_event, "source_adapter.deep_read_completed", name, {"status": result_dict.get("extraction_status", ""), "blocker": result_dict.get("blocker_status", "")}, citations=citations)
    blocked_count = sum(1 for item in deep_results if item.get("blocker_status"))
    blocker_reasons = sorted({item.get("blocker_status", "") for item in deep_results if item.get("blocker_status")})
    source_display_name = getattr(adapter, "source_name", name)
    if name != "mock" and source_health_should_update(blocker_reasons):
        upsert_source_health_csv(source_display_name, {"health_status": "Manual Check Required" if blocked_count == len(deep_results) and deep_results else "Working", "notes": f"Deep source run {run}: deep_read={len(deep_results)} blockers={blocked_count}"})
        if args.record_event:
            append_source_health_event(source_display_name, {"last_attempted_at": run, "records_deep_read": len(deep_results), "blocker_type": ",".join(blocker_reasons), "health_status": "Manual Check Required" if blocked_count == len(deep_results) and deep_results else "Working"})
    return {"adapter": name, "mode": "deep", "opportunities": [item.to_dict() for item in opportunities], "deep_results": deep_results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run source adapter in safe output/evidence-only mode")
    parser.add_argument("--adapter", default="mock", help="Adapter name")
    parser.add_argument("--mode", choices=["scan", "deep"], default="scan", help="Run mode")
    parser.add_argument("--keyword", default="", help="Search keyword")
    parser.add_argument("--limit", type=int, default=25, help="Maximum results per adapter")
    parser.add_argument("--headful", action="store_true", help="Open visible browser window")
    parser.add_argument("--output", default="", help="Output JSON path")
    parser.add_argument("--record-event", action="store_true", help="Append source adapter events")
    parser.add_argument("--create-cases", action="store_true", help="Create candidate cases from deep results")
    parser.add_argument("--respect-deadline", action="store_true", help="Do not create cases for expired tenders")
    parser.add_argument("--evidence-only", action="store_true", help="Only produce evidence/artifacts; never create cases")
    args = parser.parse_args()

    run = run_id()
    results = []
    for name in adapter_names(args.adapter):
        try:
            results.append(run_scan(name, args, run) if args.mode == "scan" else run_deep(name, args, run))
        except Exception as exc:
            payload = {"adapter": name, "mode": args.mode, "error": str(exc)}
            record_event(args.record_event, "source_adapter.error", name, payload)
            results.append(payload)

    output = Path(args.output) if args.output else DEFAULT_OUTPUT_ROOT / run / ("deep_results.json" if args.mode == "deep" else "scan_results.json")
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    payload = {"run_id": run, "mode": args.mode, "adapter": args.adapter, "create_cases": bool(args.create_cases), "external_side_effects": False, "results": results}
    write_json(output, payload)
    print(f"Wrote source run output to {output}")
    print("Default safe mode: create_cases=false unless --create-cases is passed; external_side_effects=false always.")
    if args.create_cases and args.mode == "deep" and not args.evidence_only:
        from scripts.create_cases_from_deep_source_results import create_cases_from_file

        created = create_cases_from_file(output, respect_deadline=args.respect_deadline, record_event=args.record_event)
        print(f"Created {len(created)} case candidates from {relative(output)}")
    else:
        print("No cases created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
