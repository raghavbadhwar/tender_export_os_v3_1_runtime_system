import csv
import json
from pathlib import Path

from scripts.check_projection_integrity import build_report
from scripts.rebuild_projections_from_events import project


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def test_projection_integrity_reports_changed_rows(tmp_path, monkeypatch) -> None:
    from scripts import check_projection_integrity as integrity
    from scripts import rebuild_projections_from_events as rebuild

    live_case = tmp_path / "master_cases.csv"
    headers = ["case_id", "status", "opportunity_title"]
    write_csv(live_case, headers, [{"case_id": "GOV-1", "status": "WATCHLIST", "opportunity_title": "Old"}])
    projections = {"case": {"file": live_case, "id_field": "case_id", "snapshot_event": "case.snapshot_imported"}}
    monkeypatch.setattr(rebuild, "PROJECTIONS", projections)
    monkeypatch.setattr(integrity, "PROJECTIONS", projections)

    events = tmp_path / "events.jsonl"
    events.write_text(
        json.dumps(
            {
                "event_id": "EVT-20990101000000-test",
                "event_time": "2099-01-01T00:00:00+00:00",
                "event_type": "case.snapshot_imported",
                "actor": "test",
                "case_id": "GOV-1",
                "object_type": "case",
                "object_id": "GOV-1",
                "source": "pytest",
                "payload": {"row": {"case_id": "GOV-1", "status": "DEEP_READ", "opportunity_title": "Old"}},
                "citations": ["data/master_cases.csv"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_report(events, tmp_path / "out", write_rebuilt_csvs=True)

    assert report["status"] == "DRIFT"
    case_report = report["projections"][0]
    assert case_report["changed_rows"][0]["id"] == "GOV-1"
    assert "status" in case_report["changed_rows"][0]["changed_fields"]


def test_projection_uses_object_id_when_snapshot_row_omits_primary_key(tmp_path, monkeypatch) -> None:
    from scripts import rebuild_projections_from_events as rebuild

    live_case = tmp_path / "master_cases.csv"
    headers = ["case_id", "status"]
    write_csv(live_case, headers, [])
    projections = {"case": {"file": live_case, "id_field": "case_id", "snapshot_event": "case.snapshot_imported"}}
    monkeypatch.setattr(rebuild, "PROJECTIONS", projections)

    rows = project(
        [
            {
                "event_type": "case.snapshot_imported",
                "object_type": "case",
                "object_id": "GOV-1",
                "payload": {"row": {"status": "WATCHLIST"}},
            }
        ]
    )["case"]

    assert rows == [{"case_id": "GOV-1", "status": "WATCHLIST"}]


def test_projection_integrity_reports_blank_primary_keys(tmp_path, monkeypatch) -> None:
    from scripts import check_projection_integrity as integrity
    from scripts import rebuild_projections_from_events as rebuild

    live_case = tmp_path / "master_cases.csv"
    headers = ["case_id", "status"]
    write_csv(live_case, headers, [{"case_id": "", "status": "WATCHLIST"}])
    projections = {"case": {"file": live_case, "id_field": "case_id", "snapshot_event": "case.snapshot_imported"}}
    monkeypatch.setattr(rebuild, "PROJECTIONS", projections)
    monkeypatch.setattr(integrity, "PROJECTIONS", projections)

    events = tmp_path / "events.jsonl"
    events.write_text("", encoding="utf-8")
    report = build_report(events, tmp_path / "out", write_rebuilt_csvs=False)

    assert report["status"] == "DRIFT"
    assert report["projections"][0]["blank_live_primary_keys"] == 1


def test_case_workspace_event_does_not_create_a_case_projection(tmp_path, monkeypatch) -> None:
    from scripts import rebuild_projections_from_events as rebuild

    live_case = tmp_path / "master_cases.csv"
    headers = ["case_id", "status"]
    write_csv(live_case, headers, [])
    projections = {"case": {"file": live_case, "id_field": "case_id", "snapshot_event": "case.snapshot_imported"}}
    monkeypatch.setattr(rebuild, "PROJECTIONS", projections)

    rows = project(
        [
            {
                "event_type": "case.updated",
                "case_id": "EXP-1",
                "object_type": "case",
                "object_id": "cases/EXP-1",
                "payload": {"workspace_view_updated": True, "files": ["cases/EXP-1/case.md"]},
            }
        ]
    )["case"]

    assert rows == []


def test_standing_authorization_is_not_an_approval_row(tmp_path, monkeypatch) -> None:
    from scripts import rebuild_projections_from_events as rebuild

    live_approval = tmp_path / "approvals_receipts.csv"
    headers = ["approval_id", "case_id", "approval_status", "receipt_path"]
    write_csv(live_approval, headers, [])
    projections = {
        "approval": {
            "file": live_approval,
            "id_field": "approval_id",
            "snapshot_event": "approval.snapshot_imported",
        }
    }
    monkeypatch.setattr(rebuild, "PROJECTIONS", projections)

    rows = project(
        [
            {
                "event_type": "approval.owner_decision_recorded",
                "case_id": "",
                "object_type": "approval",
                "object_id": "STANDING-AUTH-SUPPLIER-PORTAL",
                "payload": {"scope": ["supplier follow-up"], "receipt_path": "receipts/policy.json"},
            }
        ]
    )["approval"]

    assert rows == []


def test_source_health_aliases_collapse_to_canonical_row(tmp_path, monkeypatch) -> None:
    from scripts import rebuild_projections_from_events as rebuild

    live_health = tmp_path / "source_health.csv"
    headers = ["source_name", "health_status", "last_checked_date", "notes"]
    write_csv(live_health, headers, [])
    projections = {
        "source_health": {
            "file": live_health,
            "id_field": "source_name",
            "snapshot_event": "source_health.snapshot_imported",
        }
    }
    monkeypatch.setattr(rebuild, "PROJECTIONS", projections)

    rows = project(
        [
            {
                "event_type": "source_health.snapshot_imported",
                "object_type": "source_health",
                "object_id": "UN Global Marketplace (UNGM)",
                "payload": {
                    "row": {
                        "source_name": "UN Global Marketplace (UNGM)",
                        "health_status": "Needs Login",
                        "last_checked_date": "2026-06-30",
                        "notes": "Old",
                    }
                },
            },
            {
                "event_type": "source_health.updated",
                "object_type": "source_health",
                "object_id": "UNGM",
                "payload": {
                    "updates": {
                        "health_status": "Working",
                        "last_checked_date": "2026-07-12",
                        "notes": "Verified",
                    }
                },
            },
            {
                "event_type": "source_health.updated",
                "object_type": "source_health",
                "object_id": "daily_system_health_check",
                "payload": {"source_count": 30},
            },
        ]
    )["source_health"]

    assert rows == [
        {
            "source_name": "UN Global Marketplace (UNGM)",
            "health_status": "Working",
            "last_checked_date": "2026-07-12",
            "notes": "Verified",
        }
    ]
