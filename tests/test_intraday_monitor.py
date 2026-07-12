import csv
import datetime as dt
import json
from pathlib import Path

from scripts import generate_intraday_monitor as monitor


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def seed_monitor_root(root: Path) -> None:
    data = root / "data"
    write_csv(
        data / "master_cases.csv",
        ["case_id", "workflow_type", "opportunity_title", "status", "deadline_date"],
        [
            {
                "case_id": "EXP-TEST-001",
                "workflow_type": "EXPORT",
                "opportunity_title": "Turmeric RFQ",
                "status": "SUPPLIER_SEARCH",
                "deadline_date": "2026-07-20",
            },
            {
                "case_id": "GOV-TEST-001",
                "workflow_type": "GOV",
                "opportunity_title": "Stationery tender",
                "status": "APPROVED",
                "deadline_date": "2026-07-15",
            },
        ],
    )
    write_csv(
        data / "approvals_receipts.csv",
        [
            "approval_id",
            "case_id",
            "approval_status",
            "requested_at",
            "approval_timeout_at",
            "external_effect",
            "receipt_path",
        ],
        [
            {
                "approval_id": "APR-UNDATED",
                "case_id": "EXP-TEST-001",
                "approval_status": "PENDING",
            },
            {
                "approval_id": "APR-APPROVED",
                "case_id": "GOV-TEST-001",
                "approval_status": "APPROVED",
                "requested_at": "2026-07-11T06:00:00+00:00",
                "external_effect": "PENDING_APPROVED_EXECUTION",
            },
        ],
    )
    write_csv(
        data / "quote_master.csv",
        [
            "quote_id",
            "case_id",
            "supplier_id",
            "supplier_name",
            "quote_received_at",
            "quote_proof_type",
            "quote_proof_path",
            "supplier_specific_quote",
        ],
        [
            {
                "quote_id": "Q-STRICT",
                "case_id": "EXP-TEST-001",
                "supplier_id": "SUP-001",
                "quote_received_at": "2026-07-12T08:00:00+05:30",
                "quote_proof_type": "supplier_written_quote",
                "quote_proof_path": "receipts/supplier_quotes/Q-STRICT.pdf",
            },
            {
                "quote_id": "Q-LISTING",
                "case_id": "EXP-TEST-001",
                "supplier_id": "SUP-002",
                "quote_received_at": "2026-07-12T08:30:00+05:30",
                "quote_proof_type": "marketplace_listing",
                "quote_proof_path": "evidence/listing.html",
            },
        ],
    )


def test_build_report_uses_strict_quote_and_approval_semantics(tmp_path: Path) -> None:
    seed_monitor_root(tmp_path)

    report = monitor.build_report(
        project_root=tmp_path,
        now=dt.datetime(2026, 7, 12, 10, 0, tzinfo=dt.timezone.utc),
    )

    assert report["summary"] == {
        "pending_approvals_checked": 1,
        "quote_proof_gap_cases": 1,
        "approved_actions_tracked": 1,
        "receipts_created": 0,
        "owner_decision_blockers": 3,
    }
    assert report["pending_approvals"][0]["state"] == "PENDING_UNDATED"
    assert report["pending_approvals"][0]["requires_reissue"] is True
    assert report["quote_proof_gaps"][0]["strict_quote_proof_count"] == 1
    assert report["quote_proof_gaps"][0]["required_quote_proof_count"] == 2
    assert report["quote_proof_gaps"][0]["proof_gap"] == 1
    assert report["approved_actions_tracked"][0]["approval_id"] == "APR-APPROVED"
    assert report["external_business_actions"] is False


def test_write_report_and_record_event_are_auditable(tmp_path: Path) -> None:
    seed_monitor_root(tmp_path)
    report = monitor.build_report(
        project_root=tmp_path,
        now=dt.datetime(2026, 7, 12, 10, 0, tzinfo=dt.timezone.utc),
    )

    json_path, markdown_path = monitor.write_report(report, tmp_path / "outputs" / "intraday_monitor")
    monitor.record_completion(
        report,
        json_path=json_path,
        markdown_path=markdown_path,
        project_root=tmp_path,
        events_file=tmp_path / "data" / "events.jsonl",
        run_log_file=tmp_path / "data" / "agent_run_log.csv",
    )

    assert json.loads(json_path.read_text(encoding="utf-8"))["schedule_id"] == "intra_day_monitor"
    assert "PENDING_UNDATED" in markdown_path.read_text(encoding="utf-8")
    events = [json.loads(line) for line in (tmp_path / "data" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert events[-1]["event_type"] == "intraday_monitor.completed"
    assert events[-1]["payload"]["report_path"] == "outputs/intraday_monitor/intraday_monitor_20260712T100000Z.json"
    assert "intraday_monitor" in (tmp_path / "data" / "agent_run_log.csv").read_text(encoding="utf-8")
