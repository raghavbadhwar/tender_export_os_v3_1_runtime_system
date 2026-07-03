import csv
import sys
from pathlib import Path

from scripts import generate_operating_desk_report as desk


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def seed_operating_desk_root(root: Path) -> None:
    data = root / "data"
    write_csv(
        data / "master_cases.csv",
        ["case_id", "workflow_type", "opportunity_title", "buyer_name", "status", "deadline_date"],
        [
            {
                "case_id": "GOV-TEST-001",
                "workflow_type": "GOV",
                "opportunity_title": "Stationery supply",
                "buyer_name": "Example Department",
                "status": "SUPPLIER_SEARCH",
                "deadline_date": "2026-07-05",
            },
            {
                "case_id": "EXP-TEST-001",
                "workflow_type": "EXPORT",
                "opportunity_title": "Turmeric RFQ",
                "buyer_name": "Example Buyer",
                "status": "WATCHLIST",
                "deadline_date": "2026-07-20",
            },
        ],
    )
    write_csv(
        data / "approvals_receipts.csv",
        ["approval_id", "case_id", "workflow_type", "action_approved", "approval_status", "approval_card_path", "external_effect", "receipt_path"],
        [
            {
                "approval_id": "APR-TEST-001",
                "case_id": "EXP-TEST-001",
                "workflow_type": "EXPORT",
                "action_approved": "send_export_quotation",
                "approval_status": "PENDING",
                "approval_card_path": "receipts/approvals/EXP-TEST-001.html",
            },
            {
                "approval_id": "APR-TEST-002",
                "case_id": "GOV-TEST-001",
                "workflow_type": "GOV",
                "action_approved": "send_supplier_quote_request",
                "approval_status": "APPROVED",
                "external_effect": "PENDING_APPROVED_EXECUTION",
                "receipt_path": "receipts/owner_decisions/GOV-TEST-001.json",
            },
        ],
    )
    write_csv(
        data / "source_health.csv",
        ["source_name", "health_status", "last_checked_date", "consecutive_failures", "notes"],
        [
            {"source_name": "Working Source", "health_status": "Working", "last_checked_date": "2026-07-02"},
            {"source_name": "Paywall Source", "health_status": "Paywalled", "last_checked_date": "2026-07-02"},
        ],
    )
    write_csv(
        data / "plugin_health.csv",
        ["plugin_or_tool", "health_status", "last_checked_at", "blocker", "notes"],
        [
            {"plugin_or_tool": "codex", "health_status": "Working", "last_checked_at": "2026-07-02T09:00:00"},
            {"plugin_or_tool": "drive", "health_status": "Working", "last_checked_at": "2026-07-02T09:00:00", "blocker": "auth warning"},
        ],
    )
    write_csv(
        data / "agent_run_log.csv",
        desk.RUN_LOG_HEADERS,
        [
            {
                "run_id": "RUN-TEST-001",
                "run_date": "2026-07-01",
                "run_time": "09:00:00",
                "agent_name": "source_health_agent",
                "status": "FAILED",
                "notes": "fixture failure",
            }
        ],
    )


def test_operating_desk_report_sections_and_health_status(tmp_path: Path) -> None:
    seed_operating_desk_root(tmp_path)
    report = desk.build_report(project_root=tmp_path, today=desk.dt.date(2026, 7, 2), deadline_window_days=14)

    assert report["pending_approvals"][0]["approval_id"] == "APR-TEST-001"
    assert report["approved_actions_awaiting_execution"][0]["approval_id"] == "APR-TEST-002"
    assert report["supplier_search_cases"][0]["case_id"] == "GOV-TEST-001"
    assert report["watchlist_triage"][0]["case_id"] == "EXP-TEST-001"
    assert report["deadline_risks"][0]["case_id"] == "GOV-TEST-001"
    assert report["stale_or_failed_agent_runs"][0]["status"] == "FAILED"
    assert report["source_blockers"][0]["health_status"] == "Paywalled"
    assert report["plugin_blockers"][0]["blocker"] == "auth warning"
    assert report["one_smallest_owner_action"].startswith("Review approval APR-TEST-001")
    assert any(queue["agent"] == "supplier_engine_agent" for queue in report["employee_queues"])


def test_operating_desk_no_log_does_not_mutate_run_log(tmp_path: Path, monkeypatch) -> None:
    seed_operating_desk_root(tmp_path)
    run_log = tmp_path / "data" / "agent_run_log.csv"
    before = run_log.read_text(encoding="utf-8")

    monkeypatch.setattr(desk, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["generate_operating_desk_report.py", "--date", "20260702", "--no-log"])

    assert desk.main() == 0
    assert run_log.read_text(encoding="utf-8") == before
    assert (tmp_path / "outputs" / "operating_desk" / "operating_desk_20260702.json").exists()
    assert (tmp_path / "outputs" / "operating_desk" / "operating_desk_20260702.html").exists()
