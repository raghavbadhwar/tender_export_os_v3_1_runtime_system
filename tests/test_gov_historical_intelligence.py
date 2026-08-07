from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.gov_historical_intelligence import apply_case_intelligence, build_case_intelligence, write_report
from scripts.past_award_intelligence import analyze_past_awards
from scripts.rebuild_projections_from_events import project


DOMAINS = {"eprocure.gov.in"}
HASH = "a" * 64


def case() -> dict[str, str]:
    return {
        "case_id": "GOV-1",
        "workflow_type": "GOV",
        "buyer_name": "Example Municipal Buyer",
        "category_code": "GOV-OPS-001",
        "product_or_service": "Office Consumables",
    }


def evidence_row(**updates: str) -> dict[str, str]:
    base = {
        "source_record_id": "SRC-1",
        "notice_id": "N-1",
        "buyer_name": "Example Municipal Buyer",
        "category_code": "GOV-OPS-001",
        "category_name": "Office Consumables",
        "source_name": "CPPP",
        "source_url": "https://eprocure.gov.in/cppp/example/1",
        "evidence_level": "DOCUMENTS_DOWNLOADED",
        "evidence_path": "outputs/evidence/private/history/example.json",
        "evidence_sha256": HASH,
    }
    base.update(updates)
    return base


def test_official_history_yields_observed_competition_and_l1_features() -> None:
    notices = [
        evidence_row(notice_id="N-1", competition_signal="retender"),
        evidence_row(notice_id="N-2", source_record_id="SRC-2", competition_signal=""),
    ]
    awards = [
        evidence_row(award_id="A-1", notice_id="N-1", winner_name="Supplier A", bidder_count="2", l1_price_inr="101000"),
        evidence_row(award_id="A-2", notice_id="N-2", winner_name="Supplier A", bidder_count="3", l1_price_inr="99000"),
    ]
    signals = [evidence_row(signal_id="S-1", signal_type="LOW_BIDDER_COUNT", signal_strength="80")]

    report = build_case_intelligence(case(), notices, awards, signals, official_domains=DOMAINS)
    features = report["features"]

    assert features["evidence_status"] == "OFFICIAL_PUBLIC_EVIDENCE_OBSERVED"
    assert features["past_tender_count"] == 2
    assert features["similar_category_awards"] == 2
    assert features["known_past_winners"] == ["Supplier A"]
    assert features["competition"]["status"] == "OBSERVED"
    assert features["competition"]["observed_bidder_counts"] == [2, 3]
    assert features["l1"]["status"] == "OBSERVED"
    assert features["l1"]["historical_observed_l1_median_inr"] == 100000
    assert report["case_updates"]["typical_l1_price"] == "100000"


def test_missing_or_non_official_history_remains_unknown_not_estimated() -> None:
    untrusted_award = evidence_row(
        award_id="A-UNTRUSTED",
        winner_name="Supplier A",
        bidder_count="1",
        l1_price_inr="1",
        source_url="https://aggregator.example.test/award/1",
    )

    report = build_case_intelligence(case(), [], [untrusted_award], [], official_domains=DOMAINS)

    assert report["features"]["evidence_status"] == "NO_OFFICIAL_PUBLIC_EVIDENCE"
    assert report["features"]["competition"]["status"] == "UNKNOWN"
    assert report["features"]["competition"]["observed_bidder_counts"] == []
    assert report["features"]["l1"]["status"] == "UNKNOWN"
    assert report["case_updates"]["typical_l1_price"] == ""


def test_apply_writes_canonical_event_before_case_projection(tmp_path: Path) -> None:
    report = build_case_intelligence(
        case(),
        [evidence_row(notice_id="N-1")],
        [evidence_row(award_id="A-1", winner_name="Supplier A", bidder_count="2", l1_price_inr="100000")],
        [],
        official_domains=DOMAINS,
    )
    paths = write_report(report, tmp_path / "case_report")
    cases = tmp_path / "master_cases.csv"
    cases.write_text(
        "case_id,workflow_type,buyer_repeat_score,past_tender_count,similar_category_awards,known_past_winners,typical_l1_price,updated_at\n"
        "GOV-1,GOV,,,,,,,2099-01-01\n",
        encoding="utf-8",
    )
    events = tmp_path / "events.jsonl"

    result = apply_case_intelligence(report, report_path=paths["json_path"], master_cases_path=cases, events_path=events, actor="pytest")

    event = json.loads(events.read_text(encoding="utf-8").strip())
    assert result["event_id"] == event["event_id"]
    assert event["event_type"] == "case.historical_intelligence_recorded"
    with cases.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["known_past_winners"] == "Supplier A"
    assert row["typical_l1_price"] == "100000"


def test_past_award_helper_never_uses_award_value_as_l1_proxy() -> None:
    result = analyze_past_awards(
        [
            {
                "buyer_name": "Example Buyer",
                "category_name": "Office Consumables",
                "winner_name": "Supplier A",
                "award_value_inr": "100000",
            }
        ],
        "Example Buyer",
        "Office",
    )

    assert result["average_award_value"] == 100000
    assert result["typical_l1_price"] == ""
    assert result["l1_price_status"] == "UNKNOWN"


def test_historical_intelligence_event_rebuilds_case_projection(tmp_path: Path, monkeypatch) -> None:
    from scripts import rebuild_projections_from_events as rebuild

    projection_file = tmp_path / "master_cases.csv"
    projection_file.write_text("case_id,buyer_repeat_score,typical_l1_price\n", encoding="utf-8")
    monkeypatch.setattr(
        rebuild,
        "PROJECTIONS",
        {
            "case": {
                "file": projection_file,
                "id_field": "case_id",
                "snapshot_event": "case.snapshot_imported",
                "upsert_events": ["case.historical_intelligence_recorded"],
            }
        },
    )
    rows = project(
        [
            {
                "event_type": "case.snapshot_imported",
                "object_type": "case",
                "object_id": "GOV-1",
                "payload": {"row": {"case_id": "GOV-1", "buyer_repeat_score": ""}},
            },
            {
                "event_type": "case.historical_intelligence_recorded",
                "case_id": "GOV-1",
                "object_type": "case",
                "object_id": "GOV-1",
                "payload": {"updates": {"buyer_repeat_score": "88", "typical_l1_price": "100000"}},
            },
        ]
    )["case"]

    assert rows == [{"case_id": "GOV-1", "buyer_repeat_score": "88", "typical_l1_price": "100000"}]
