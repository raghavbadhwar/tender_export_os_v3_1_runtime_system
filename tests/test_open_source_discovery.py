import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.source_runtime.open_source_discovery import (
    Candidate,
    PageCapture,
    SearchHit,
    actual_user_home,
    build_discovery_bundle,
    write_discovery_bundle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={**os.environ, "TENDER_OS_EVENTS_FILE": str(Path(os.environ.get("TMPDIR", "/tmp")) / "teos-test-events.jsonl")},
    )


def test_actual_user_home_ignores_profile_home_env(monkeypatch) -> None:
    monkeypatch.setenv("HOME", "/tmp/hermes-profile-home")

    assert str(actual_user_home()) != "/tmp/hermes-profile-home"


def test_build_discovery_bundle_dedupes_search_katana_and_captures() -> None:
    bundle = build_discovery_bundle(
        query="spice export rfq",
        workflow="EXPORT",
        run_id="run-001",
        search_hits=[
            SearchHit(title="IBP RFQ", url="https://example.test/rfq", snippet="Buyer request", engine="searxng", rank=1),
            SearchHit(title="Duplicate RFQ", url="https://example.test/rfq#top", snippet="Same page", engine="ddgs", rank=1),
            SearchHit(title="Tender", url="https://example.test/tender", snippet="Tender notice", engine="ddgs", rank=2),
        ],
        katana_urls=["https://example.test/rfq/details", "https://example.test/tender"],
        captures={
            "https://example.test/rfq": PageCapture(
                url="https://example.test/rfq",
                status="captured",
                title="IBP RFQ",
                text="Need Indian spices from verified exporter. Quantity 10 MT.",
                raw_html_path="outputs/source_discovery/run-001/raw_html/rfq.html",
                parsed_text_path="outputs/source_discovery/run-001/parsed_text/rfq.txt",
                tool="trafilatura",
            )
        },
        tool_receipts={"searxng": {"status": "ok"}, "ddgs": {"status": "ok"}, "katana": {"status": "ok"}},
    )

    assert bundle["external_side_effects"] is False
    assert bundle["query"] == "spice export rfq"
    assert bundle["workflow"] == "EXPORT"
    assert bundle["summary"]["unique_candidate_count"] == 3
    assert bundle["summary"]["captured_page_count"] == 1
    by_url = {candidate["url"]: candidate for candidate in bundle["candidates"]}
    assert by_url["https://example.test/rfq"]["engines"] == ["ddgs", "searxng"]
    assert by_url["https://example.test/rfq"]["evidence_level"] == "DETAIL_PAGE_CAPTURED"
    assert by_url["https://example.test/rfq/details"]["discovery_sources"] == ["katana"]


def test_write_discovery_bundle_creates_json_markdown_and_manifest(tmp_path: Path) -> None:
    bundle = build_discovery_bundle(
        query="government tender spices",
        workflow="GOV",
        run_id="run-002",
        search_hits=[SearchHit(title="Tender Notice", url="https://example.test/tender", snippet="Public tender", engine="searxng", rank=1)],
        katana_urls=[],
        captures={
            "https://example.test/tender": PageCapture(
                url="https://example.test/tender",
                status="captured",
                title="Tender Notice",
                text="Public tender for spice supply with deadline next month.",
                raw_html_path="outputs/source_discovery/run-002/raw_html/tender.html",
                parsed_text_path="outputs/source_discovery/run-002/parsed_text/tender.txt",
                tool="crawl4ai+trafilatura",
            )
        },
        tool_receipts={"searxng": {"status": "ok"}},
    )

    written = write_discovery_bundle(bundle, tmp_path)

    assert written["bundle_json"].endswith("bundle.json")
    assert written["bundle_md"].endswith("bundle.md")
    assert written["manifest_json"].endswith("manifest.json")
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["bundle_json"] == "bundle.json"
    assert "Tender Notice" in (tmp_path / "bundle.md").read_text()


def test_run_open_source_discovery_cli_fixture_writes_evidence_bundle(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.json"
    out_dir = tmp_path / "out"
    fixture.write_text(
        json.dumps(
            {
                "searxng": [
                    {"title": "India Business Portal RFQ", "url": "https://example.test/rfq", "snippet": "Spice buying lead"}
                ],
                "ddgs": [
                    {"title": "Duplicate", "href": "https://example.test/rfq", "body": "Duplicate via DDGS"},
                    {"title": "Tender page", "href": "https://example.test/tender", "body": "Government tender"},
                ],
                "katana": ["https://example.test/rfq/details"],
                "pages": {
                    "https://example.test/rfq": "<html><title>RFQ</title><article><h1>Spice RFQ</h1><p>Buyer seeks Indian spices in bulk for import.</p></article></html>",
                    "https://example.test/tender": "<html><title>Tender</title><article><h1>Spice tender</h1><p>Public tender notice for spice supply.</p></article></html>",
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_cmd(
        "scripts/run_open_source_discovery.py",
        "--query",
        "spice export rfq",
        "--workflow",
        "EXPORT",
        "--fixture-json",
        str(fixture),
        "--output-dir",
        str(out_dir),
        "--limit",
        "5",
        "--max-pages",
        "2",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    bundle = json.loads((out_dir / "bundle.json").read_text())
    assert bundle["external_side_effects"] is False
    assert bundle["summary"]["unique_candidate_count"] == 3
    assert bundle["summary"]["captured_page_count"] == 2
    assert (out_dir / "bundle.md").exists()
    assert (out_dir / "parsed_text").exists()
    assert "No cases created" in result.stdout
