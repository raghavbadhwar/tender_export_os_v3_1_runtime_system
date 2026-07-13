from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

from scripts.event_ledger import load_events
from scripts.run_shadow_profile_probes import append_evaluation_rows, append_run_log_rows, build_report, write_report


def _registry() -> dict:
    return {
        "owner_profile": "tender-export-os",
        "specialist_profiles": ["gov-tender-intelligence"],
        "profiles": {
            "tender-export-os": {"allowed_toolsets": ["file"], "forbidden_toolsets": []},
            "gov-tender-intelligence": {"allowed_toolsets": ["file"], "forbidden_toolsets": []},
        },
    }


def test_shadow_profile_probe_report_is_local_only() -> None:
    report = build_report(
        registry=_registry(),
        as_of=dt.datetime(2026, 7, 13, 9, 0, tzinfo=dt.timezone.utc),
    )

    assert report["status"] == "PASS"
    assert report["profile_count"] == 2
    assert report["pass_count"] == 2
    assert report["external_actions_executed"] is False
    assert report["production_routing_enabled"] is False
    assert {probe["profile"] for probe in report["probes"]} == {
        "tender-export-os",
        "gov-tender-intelligence",
    }


def test_shadow_profile_probe_appends_idempotent_run_log_rows(tmp_path: Path) -> None:
    report = build_report(
        registry=_registry(),
        as_of=dt.datetime(2026, 7, 13, 9, 0, tzinfo=dt.timezone.utc),
    )
    receipt = write_report(report, tmp_path / "receipts")
    run_log = tmp_path / "agent_run_log.csv"

    first = append_run_log_rows(report, run_log_path=run_log, receipt_path=receipt)
    second = append_run_log_rows(report, run_log_path=run_log, receipt_path=receipt)

    rows = list(csv.DictReader(run_log.open(newline="", encoding="utf-8")))
    assert first["appended_count"] == 2
    assert second["appended_count"] == 0
    assert len(rows) == 2
    assert {row["agent_name"] for row in rows} == {"tender-export-os", "gov-tender-intelligence"}
    assert all(row["trigger_type"] == "shadow_profile_probe" for row in rows)
    assert all(row["status"] == "SUCCESS" for row in rows)
    assert all(row["actions_taken"] == "shadow_profile_probe" for row in rows)


def test_shadow_profile_probe_appends_idempotent_evaluation_rows(tmp_path: Path) -> None:
    report = build_report(
        registry=_registry(),
        as_of=dt.datetime(2026, 7, 13, 9, 0, tzinfo=dt.timezone.utc),
    )
    receipt = write_report(report, tmp_path / "receipts")
    evaluations = tmp_path / "agent_evaluations.csv"

    first = append_evaluation_rows(report, evaluations_path=evaluations, receipt_path=receipt)
    second = append_evaluation_rows(report, evaluations_path=evaluations, receipt_path=receipt)

    rows = list(csv.DictReader(evaluations.open(newline="", encoding="utf-8")))
    assert first["evaluation_appended_count"] == 2
    assert second["evaluation_appended_count"] == 0
    assert len(rows) == 2
    assert {row["profile"] for row in rows} == {"tender-export-os", "gov-tender-intelligence"}
    assert all(row["scenario_id"] == "shadow_profile_probe" for row in rows)
    assert all(row["evidence_completeness_pct"] == "100" for row in rows)
    assert all(row["policy_compliance"] == "PASS" for row in rows)


def test_shadow_profile_probe_records_canonical_evaluation_events(tmp_path: Path) -> None:
    report = build_report(
        registry=_registry(),
        as_of=dt.datetime(2026, 7, 13, 9, 0, tzinfo=dt.timezone.utc),
    )
    receipt = write_report(report, tmp_path / "receipts")
    evaluations = tmp_path / "agent_evaluations.csv"
    events = tmp_path / "events.jsonl"

    first = append_evaluation_rows(
        report,
        evaluations_path=evaluations,
        receipt_path=receipt,
        events_file=events,
    )
    second = append_evaluation_rows(
        report,
        evaluations_path=evaluations,
        receipt_path=receipt,
        events_file=events,
    )

    recorded = load_events(events)
    assert first["evaluation_event_count"] == 2
    assert second["evaluation_event_count"] == 2
    assert len(recorded) == 2
    assert {event["event_type"] for event in recorded} == {"agent_evaluation.created"}
    assert {event["object_id"] for event in recorded} == {
        "AE-20260713-SHADOW-PROFILE-tender-export-os",
        "AE-20260713-SHADOW-PROFILE-gov-tender-intelligence",
    }
