from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.capture_historical_gov_intelligence import capture_packets, normalize_record, write_capture
from scripts.past_award_intelligence import analyze_past_awards


DOMAINS = {"eprocure.gov.in", "gem.gov.in"}


def packet(tmp_path: Path) -> Path:
    path = tmp_path / "historical_gov_packet_fixture.json"
    path.write_text(
        json.dumps(
            {
                "source_name": "CPPP",
                "source_url": "https://eprocure.gov.in/archive",
                "notices": [
                    {
                        "source_record_id": "N-1",
                        "buyer_name": "  Example   Municipal Buyer ",
                        "category_name": " Office   Consumables ",
                        "product_or_service": "Paper",
                        "notice_date": "2099-01-01",
                        "deadline_date": "2099-01-20",
                        "evidence_level": "DETAIL_PAGE_READ",
                    }
                ],
                "awards": [
                    {
                        "source_record_id": "A-1",
                        "notice_id": "N-1",
                        "buyer_name": "Example Municipal Buyer",
                        "winner_name": "Example Supplier",
                        "category_name": "Office Consumables",
                        "award_date": "2099-02-01",
                        "award_value_inr": "100000",
                        "bidder_count": "3",
                        "l1_price_inr": "98000",
                        "l2_price_inr": "102000",
                        "competition_signal": "LOW_BIDDER_COUNT",
                        "evidence_level": "DOCUMENTS_DOWNLOADED",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_historical_record_normalization_keeps_provenance_hash_and_confidence(tmp_path: Path) -> None:
    path = packet(tmp_path)
    value = json.loads(path.read_text(encoding="utf-8"))
    row = normalize_record(
        value["notices"][0] | {"source_name": value["source_name"], "source_url": value["source_url"]},
        kind="notice",
        packet_path=path,
        official_domains=DOMAINS,
        as_of="2099-02-02",
    )

    assert row["buyer_name"] == "Example Municipal Buyer"
    assert row["buyer_normalized"] == "example municipal buyer"
    assert row["category_normalized"] == "office consumables"
    assert row["evidence_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert row["evidence_path"] == str(path)
    assert int(row["source_confidence"]) >= 80


def test_nonofficial_or_nonpublic_source_is_rejected(tmp_path: Path) -> None:
    path = packet(tmp_path)
    with pytest.raises(ValueError, match="official public source"):
        normalize_record(
            {
                "source_record_id": "N-2",
                "source_name": "Aggregator",
                "source_url": "https://example.com/tender",
                "buyer_name": "Buyer",
                "category_name": "Category",
                "notice_date": "2099-01-01",
                "evidence_level": "PUBLIC_LISTING_ONLY",
            },
            kind="notice",
            packet_path=path,
            official_domains=DOMAINS,
            as_of="2099-02-02",
        )


def test_capture_is_bounded_and_award_analysis_uses_canonical_winner_field(tmp_path: Path) -> None:
    path = packet(tmp_path)
    result = capture_packets([path, path], official_domains=DOMAINS, max_packets=1, max_records=1, as_of="2099-02-02")

    assert result["packets_processed"] == 1
    assert result["records_captured"] == 1
    assert result["bounded"] is True

    analysis = analyze_past_awards(
        [
            {
                "buyer_name": "Example Buyer",
                "category_name": "Water filters",
                "winner_name": "Supplier A",
                "award_value_inr": "100000",
            },
            {
                "buyer_name": "Example Buyer",
                "category_name": "Water filters AMC",
                "winner_name": "Supplier A",
                "award_value_inr": "120000",
            },
        ],
        "Example Buyer",
        "Water",
    )
    assert analysis["known_past_winners"] == ["Supplier A"]
    assert analysis["incumbent_risk"] == "high"


def test_award_capture_preserves_observed_bidder_and_l1_fields(tmp_path: Path) -> None:
    result = capture_packets([packet(tmp_path)], official_domains=DOMAINS, max_packets=1, max_records=5, as_of="2099-02-02")

    award = result["awards"][0]
    assert award["bidder_count"] == "3"
    assert award["l1_price_inr"] == "98000"
    assert award["l2_price_inr"] == "102000"
    assert award["competition_signal"] == "LOW_BIDDER_COUNT"


def test_capture_write_is_event_first_projection_backed_and_idempotent(tmp_path: Path) -> None:
    path = packet(tmp_path)
    capture = capture_packets([path], official_domains=DOMAINS, max_packets=1, max_records=5, as_of="2099-02-02")
    notices = tmp_path / "historical_tender_notices.csv"
    awards = tmp_path / "historical_awards.csv"
    events = tmp_path / "events.jsonl"

    first = write_capture(capture, notices_path=notices, awards_path=awards, events_path=events, actor="pytest")
    duplicate = write_capture(capture, notices_path=notices, awards_path=awards, events_path=events, actor="pytest")

    assert first["canonical_event_appended"] is True
    assert duplicate["notice_projection_updated"] is False
    assert duplicate["award_projection_updated"] is False
    assert len(events.read_text(encoding="utf-8").splitlines()) == 2
    assert "Example Supplier" in awards.read_text(encoding="utf-8")


def test_historical_capture_is_registered_as_a_bounded_supervised_schedule() -> None:
    root = Path(__file__).resolve().parents[1]
    cron = yaml.safe_load((root / "config/hermes_cron.yaml").read_text(encoding="utf-8"))
    jobs = {job["id"]: job for job in cron["jobs"]}
    job = jobs["weekly_historical_gov_intelligence_capture"]

    assert job["runtime"] == "hermes_no_agent_script"
    assert "capture_historical_gov_intelligence.py --write --json" in job["task_command"]
    assert "no browser fetch" in job["stop_condition"].lower()
