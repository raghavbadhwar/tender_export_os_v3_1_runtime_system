from __future__ import annotations

import json
from pathlib import Path

from scripts.run_agent_browser_core_sources import parse_gem_page_text, run_core_sources


def test_parse_gem_page_text_extracts_count_and_references() -> None:
    text = "Showing 1 - 10 records of 48,123 records\nBid No.: GEM/2026/B/7627244\nRA NO: GEM/2026/R/694620"
    assert parse_gem_page_text(text) == {
        "records_reported": 48123,
        "sample_references": ["GEM/2026/B/7627244", "GEM/2026/R/694620"],
    }


def test_run_core_sources_uses_capture_backend(tmp_path: Path) -> None:
    def fake_capture(**kwargs):
        out = tmp_path / kwargs["source_name"].replace(" ", "_")
        out.mkdir(parents=True, exist_ok=True)
        page_text = out / "page_text.json"
        page_text.write_text(json.dumps({"data": {"text": "Showing 1 - 10 records of 25 records\nGEM/2026/B/1"}}), encoding="utf-8")
        receipt_path = out / "receipt.json"
        receipt = {"capture_id": "ABCAP-1", "status": "COMPLETED", "blockers": [], "artifacts": {"page_text": str(page_text)}}
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        return receipt, receipt_path

    report = run_core_sources(
        {
            "gem": {
                "source_name": "GeM",
                "start_url": "https://bidplus.gem.gov.in/all-bids",
            }
        },
        capture_func=fake_capture,
        output_root=tmp_path,
        capture_timeout_seconds=75,
    )

    assert report["status"] == "PASS"
    assert report["results"][0]["records_reported"] == 25
    assert report["results"][0]["timeout_seconds"] == 75
    assert report["external_business_actions"] is False
