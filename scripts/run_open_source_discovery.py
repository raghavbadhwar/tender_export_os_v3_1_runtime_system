#!/usr/bin/env python3
"""Run open-source source discovery and write an evidence-only bundle.

Pipeline: SearXNG + DDGS search -> Katana URL expansion -> Trafilatura/Crawl4AI
page capture -> bundle.json/bundle.md/manifest.json.  No cases are created and no
external business actions are performed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.source_runtime.credential_policy import sanitize_payload  # noqa: E402
from scripts.source_runtime.open_source_discovery import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    actual_user_home,
    build_discovery_bundle,
    capture_crawl4ai_pages,
    capture_fixture_pages,
    capture_http_pages,
    load_fixture,
    make_run_id,
    merge_captures,
    query_ddgs,
    query_searxng,
    relative,
    run_katana,
    write_discovery_bundle,
)
from scripts.source_runtime.source_health import append_source_health_event, upsert_source_health_csv  # noqa: E402

try:  # noqa: E402
    from scripts.event_ledger import append_event
except Exception:  # pragma: no cover
    append_event = None  # type: ignore


def record_event(enabled: bool, event_type: str, payload: dict, citations: list[str] | None = None) -> None:
    if not enabled or append_event is None:
        return
    append_event(
        event_type,
        "open_source_discovery",
        object_type="source_adapter",
        object_id="open_source_discovery",
        source="open_source_discovery",
        payload=sanitize_payload(payload),
        citations=citations or [],
    )


def ensure_searxng(enabled: bool) -> dict:
    if not enabled:
        return {"status": "skipped"}
    helper = actual_user_home() / ".local" / "bin" / "teos-searxng-start"
    if not helper.exists():
        return {"status": "missing", "error": f"{helper} not found"}
    env = os.environ.copy()
    user_home = actual_user_home()
    env["HOME"] = str(user_home)
    env.setdefault("COLIMA_HOME", str(user_home / ".colima-teos"))
    env.setdefault("DOCKER_CONFIG", str(user_home / ".docker-teos"))
    proc = subprocess.run([str(helper)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=240, env=env)
    return {
        "status": "ok" if proc.returncode == 0 else "blocked_or_error",
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip()[-1000:],
        "stderr": proc.stderr.strip()[-1000:],
    }


def choose_capture_urls(search_hits, katana_urls: list[str], max_pages: int) -> list[str]:
    urls = []
    for hit in search_hits:
        if hit.url and hit.url not in urls:
            urls.append(hit.url)
        if len(urls) >= max_pages:
            return urls
    for url in katana_urls:
        if url and url not in urls:
            urls.append(url)
        if len(urls) >= max_pages:
            return urls
    return urls


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open-source search/scrape wrapper for Tender Export OS")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--workflow", choices=["GOV", "EXPORT", "SUPPLIER", "MIXED"], default="MIXED")
    parser.add_argument("--limit", type=int, default=10, help="Max results per search layer")
    parser.add_argument("--max-pages", type=int, default=3, help="Max detail pages to capture")
    parser.add_argument("--katana-depth", type=int, default=1, help="Katana crawl depth")
    parser.add_argument("--katana-limit", type=int, default=10, help="Max Katana-discovered URLs")
    parser.add_argument("--crawl4ai-limit", type=int, default=1, help="Max pages to capture with Crawl4AI after Trafilatura")
    parser.add_argument("--searxng-url", default="http://127.0.0.1:8888", help="Local SearXNG base URL")
    parser.add_argument("--ensure-searxng", action="store_true", help="Start/repair local TEOS SearXNG before search")
    parser.add_argument("--fixture-json", default="", help="Offline fixture JSON for tests/reproducible dry-runs")
    parser.add_argument("--output-dir", default="", help="Output directory; default outputs/source_discovery/<run_id>")
    parser.add_argument("--record-event", action="store_true", help="Append schema-valid source adapter events")
    parser.add_argument("--update-source-health", action="store_true", help="Update data/source_health.csv for the discovery stack")
    parser.add_argument("--skip-katana", action="store_true", help="Skip Katana URL expansion")
    parser.add_argument("--skip-ddgs", action="store_true", help="Skip DDGS fallback search")
    parser.add_argument("--skip-searxng", action="store_true", help="Skip SearXNG search")
    parser.add_argument("--skip-crawl4ai", action="store_true", help="Skip Crawl4AI capture")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = make_run_id()
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_ROOT / run_id
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    record_event(args.record_event, "source_adapter.scan_started", {"query": args.query, "workflow": args.workflow, "run_id": run_id})

    tool_receipts: dict = {"external_side_effects": {"status": "ok", "value": False}}
    if args.fixture_json:
        searxng_hits, ddgs_hits, katana_urls, fixture_pages, fixture_receipts = load_fixture(Path(args.fixture_json), args.limit)
        tool_receipts.update(fixture_receipts)
        captures, receipt = capture_fixture_pages(fixture_pages, output_dir, args.max_pages)
        tool_receipts["trafilatura"] = receipt
        tool_receipts["searxng"] = {"status": "ok", "result_count": len(searxng_hits), "fixture": True}
        tool_receipts["ddgs"] = {"status": "ok", "result_count": len(ddgs_hits), "fixture": True}
        tool_receipts["katana"] = {"status": "ok", "url_count": len(katana_urls), "fixture": True}
    else:
        ensure_receipt = ensure_searxng(args.ensure_searxng)
        tool_receipts["ensure_searxng"] = ensure_receipt
        searxng_hits, searxng_receipt = ([], {"status": "skipped"}) if args.skip_searxng else query_searxng(args.searxng_url, args.query, args.limit)
        ddgs_hits, ddgs_receipt = ([], {"status": "skipped"}) if args.skip_ddgs else query_ddgs(args.query, args.limit)
        tool_receipts["searxng"] = searxng_receipt
        tool_receipts["ddgs"] = ddgs_receipt
        search_hits = [*searxng_hits, *ddgs_hits]
        seed_urls = [hit.url for hit in search_hits]
        katana_urls, katana_receipt = ([], {"status": "skipped"}) if args.skip_katana else run_katana(seed_urls, depth=args.katana_depth, limit=args.katana_limit, timeout_seconds=12)
        tool_receipts["katana"] = katana_receipt
        capture_urls = choose_capture_urls(search_hits, katana_urls, args.max_pages)
        captures, trafilatura_receipt = capture_http_pages(capture_urls, output_dir, args.max_pages)
        tool_receipts["trafilatura"] = trafilatura_receipt
        if args.skip_crawl4ai or args.crawl4ai_limit <= 0:
            tool_receipts["crawl4ai"] = {"status": "skipped"}
        else:
            c4a_captures, c4a_receipt = capture_crawl4ai_pages(capture_urls, output_dir, min(args.crawl4ai_limit, args.max_pages))
            captures = merge_captures(captures, c4a_captures)
            tool_receipts["crawl4ai"] = c4a_receipt

    if args.fixture_json:
        search_hits = [*searxng_hits, *ddgs_hits]

    bundle = build_discovery_bundle(
        query=args.query,
        workflow=args.workflow,
        run_id=run_id,
        search_hits=search_hits,
        katana_urls=katana_urls,
        captures=captures,
        tool_receipts=tool_receipts,
    )
    written = write_discovery_bundle(bundle, output_dir)

    citations = [relative(Path(path)) for path in written.values()]
    record_event(
        args.record_event,
        "source_adapter.scan_completed",
        {"query": args.query, "workflow": args.workflow, "run_id": run_id, "summary": bundle["summary"], "output_dir": relative(output_dir)},
        citations=citations,
    )
    if bundle["blockers"]:
        record_event(args.record_event, "source_adapter.blocked", {"run_id": run_id, "blockers": bundle["blockers"]}, citations=citations)

    if args.update_source_health:
        health = "Working" if bundle["summary"]["unique_candidate_count"] else "Manual Check Required"
        notes = f"Open-source discovery run {run_id}: query={args.query!r} candidates={bundle['summary']['unique_candidate_count']} captured={bundle['summary']['captured_page_count']} blockers={bundle['summary']['blocker_count']}"
        upsert_source_health_csv("Open Source Discovery Stack", {"health_status": health, "notes": notes, "url": args.searxng_url, "workflow": args.workflow})
        if args.record_event:
            append_source_health_event("Open Source Discovery Stack", {"health_status": health, "last_attempted_at": run_id, "records_found": bundle["summary"]["unique_candidate_count"]}, citations=citations)

    print(f"Wrote open-source discovery bundle to {written['bundle_json']}")
    print(f"Wrote markdown report to {written['bundle_md']}")
    print("No cases created. External side effects=false. Stage leads through proof gates before operational use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
