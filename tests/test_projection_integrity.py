import csv
import json
from pathlib import Path

from scripts.check_projection_integrity import build_report


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
