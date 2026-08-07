import csv
import json
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
        ["case_id", "workflow_type", "opportunity_title", "buyer_name", "status", "deadline_date", "source_name", "source_url", "evidence_level", "score_gov", "score_export"],
        [
            {
                "case_id": "GOV-TEST-001",
                "workflow_type": "GOV",
                "opportunity_title": "Stationery supply",
                "buyer_name": "Example Department",
                "status": "SUPPLIER_SEARCH",
                "deadline_date": "2026-07-05",
                "source_name": "GeM",
                "source_url": "https://example.test/gem",
                "evidence_level": "DOCUMENTS_DOWNLOADED",
                "score_gov": "88",
            },
            {
                "case_id": "EXP-TEST-001",
                "workflow_type": "EXPORT",
                "opportunity_title": "Turmeric RFQ",
                "buyer_name": "Example Buyer",
                "status": "WATCHLIST",
                "deadline_date": "2026-07-20",
                "source_name": "Alibaba",
                "source_url": "https://example.test/rfq",
                "evidence_level": "RFQ_VERIFIED",
                "score_export": "81",
            },
        ],
    )
    write_csv(
        data / "approvals_receipts.csv",
        ["approval_id", "case_id", "workflow_type", "action_approved", "approval_status", "approval_card_path", "external_effect", "receipt_path", "approval_timeout_at"],
        [
            {
                "approval_id": "APR-TEST-001",
                "case_id": "EXP-TEST-001",
                "workflow_type": "EXPORT",
                "action_approved": "send_export_quotation",
                "approval_status": "PENDING",
                "approval_card_path": "receipts/approvals/EXP-TEST-001.html",
                "approval_timeout_at": "2026-07-04T12:00:00+00:00",
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
    write_csv(
        data / "buyer_demand_signals.csv",
        ["signal_id", "company_name", "country", "category_name", "market_fit_score", "demand_confidence", "contact_status", "next_safe_action", "case_id"],
        [
            {
                "signal_id": "SIG-TEST-001",
                "company_name": "Example Ethical Store",
                "country": "United Kingdom",
                "category_name": "Handicrafts",
                "market_fit_score": "82",
                "demand_confidence": "MEDIUM",
                "contact_status": "PUBLIC_GENERAL_CONTACT",
                "next_safe_action": "DRAFT_OUTREACH_FOR_APPROVAL",
                "case_id": "EXP-TEST-001",
            }
        ],
    )
    write_csv(
        data / "outreach_queue.csv",
        ["outreach_id", "case_id", "buyer_id", "signal_id", "subject", "approval_id", "approval_status", "send_status", "reply_status", "last_reply_at", "stop_reason"],
        [
            {
                "outreach_id": "OUT-TEST-001",
                "case_id": "EXP-TEST-001",
                "buyer_id": "BUY-TEST-001",
                "signal_id": "SIG-TEST-001",
                "subject": "Indian artisan homeware",
                "approval_id": "APR-TEST-001",
                "approval_status": "PENDING",
                "send_status": "DRAFT_ONLY",
                "reply_status": "NO_REPLY",
            }
        ],
    )
    write_csv(
        data / "communication_log.csv",
        ["communication_id", "outreach_id", "case_id", "buyer_id", "direction", "occurred_at", "subject", "classification", "requires_owner_action", "recommended_next_action", "content_path"],
        [
            {
                "communication_id": "COM-TEST-001",
                "outreach_id": "OUT-TEST-001",
                "case_id": "EXP-TEST-001",
                "buyer_id": "BUY-TEST-001",
                "direction": "INBOUND",
                "occurred_at": "2026-07-02T08:00:00+00:00",
                "subject": "Re: Indian artisan homeware",
                "classification": "POSITIVE_INTEREST",
                "requires_owner_action": "TRUE",
                "recommended_next_action": "Prepare a factual response draft for approval.",
                "content_path": "receipts/buyer_replies/COM-TEST-001.txt",
            }
        ],
    )
    write_csv(
        data / "case_outcomes.csv",
        ["outcome_id", "case_id", "workflow_type", "outcome_type", "occurred_at", "evidence_path", "evidence_sha256", "verification_status"],
        [
            {
                "outcome_id": "OUT-PAY-1",
                "case_id": "GOV-TEST-001",
                "workflow_type": "GOV",
                "outcome_type": "PAYMENT_DUE",
                "occurred_at": "2026-06-29T00:00:00+00:00",
                "evidence_path": "receipts/payment_due.json",
                "evidence_sha256": "a" * 64,
                "verification_status": "VERIFIED",
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
    assert report["buyer_acquisition"]["target_count"] == 1
    assert report["buyer_acquisition"]["outreach_draft_count"] == 1
    assert report["buyer_acquisition"]["reply_count"] == 1
    assert report["buyer_acquisition"]["owner_action_replies"][0]["classification"] == "POSITIVE_INTEREST"
    assert report["one_smallest_owner_action"].startswith("Review buyer reply COM-TEST-001")
    assert any(queue["agent"] == "supplier_engine_agent" for queue in report["employee_queues"])
    assert report["top_three_evidenced_opportunities"][0]["case_id"] == "GOV-TEST-001"
    assert report["expiring_approvals"][0]["approval_id"] == "APR-TEST-001"
    assert report["substantive_replies"][0]["communication_id"] == "COM-TEST-001"
    assert report["overdue_payments"][0]["case_id"] == "GOV-TEST-001"
    assert report["exception_first"]["one_primary_action"] == report["one_smallest_owner_action"]
    assert report["exception_first"]["top_three_evidenced_opportunities"]
    assert report["summary"]["exceptions"] >= 1


def test_operating_desk_keeps_safety_held_approved_action_blocked(tmp_path: Path) -> None:
    seed_operating_desk_root(tmp_path)
    approvals = tmp_path / "data" / "approvals_receipts.csv"
    rows = list(csv.DictReader(approvals.open(newline="", encoding="utf-8")))
    for row in rows:
        row["approval_status"] = "APPROVED"
    rows[0]["external_effect"] = "PENDING_APPROVED_EXECUTION"
    rows[0]["notes"] = "Execution clearance attempt: SAFETY_HELD_NOT_SENT because RFQ is RAW_LEAD."
    headers = list(rows[0].keys())
    if "notes" not in headers:
        headers.append("notes")
    write_csv(approvals, headers, rows)

    report = desk.build_report(project_root=tmp_path, today=desk.dt.date(2026, 7, 2), deadline_window_days=14)

    assert report["approved_actions_awaiting_execution"][0]["next_action"].startswith("Keep held")
    assert report["one_smallest_owner_action"].startswith("Review buyer reply COM-TEST-001")


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


def test_operating_desk_flags_stale_health_and_strict_quote_gap(tmp_path: Path) -> None:
    seed_operating_desk_root(tmp_path)
    source_health = tmp_path / "data" / "source_health.csv"
    rows = list(csv.DictReader(source_health.open(newline="", encoding="utf-8")))
    rows[0]["last_checked_date"] = "2026-06-20"
    write_csv(source_health, list(rows[0]), rows)
    write_csv(
        tmp_path / "data" / "quote_master.csv",
        [
            "quote_id",
            "case_id",
            "supplier_id",
            "quote_received_at",
            "quote_proof_type",
            "quote_proof_path",
            "indicative_price_only",
        ],
        [
            {
                "quote_id": "Q-LISTING",
                "case_id": "GOV-TEST-001",
                "supplier_id": "SUP-1",
                "quote_received_at": "2026-07-01T09:00:00",
                "quote_proof_type": "marketplace_listing",
                "quote_proof_path": "outputs/listing.html",
                "indicative_price_only": "TRUE",
            }
        ],
    )

    report = desk.build_report(
        project_root=tmp_path,
        today=desk.dt.date(2026, 7, 2),
        deadline_window_days=14,
        stale_days=1,
    )

    stale = next(item for item in report["source_blockers"] if item["name"] == "Working Source")
    assert stale["stale"] is True
    assert stale["next_action"].startswith("Refresh this health probe")
    assert report["quote_proof_gaps"][0]["case_id"] == "GOV-TEST-001"
    assert report["quote_proof_gaps"][0]["strict_quote_proof_count"] == 0
    assert report["summary"]["quote_proof_gaps"] == 1


def test_operating_desk_surfaces_hermes_and_prediction_health(tmp_path: Path) -> None:
    seed_operating_desk_root(tmp_path)
    cron_dir = tmp_path / "outputs" / "cron_gateway"
    cron_dir.mkdir(parents=True)
    (cron_dir / "cron_gateway_reliability_20990101_090000.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "generated_at": "2099-01-01T09:00:00+00:00",
                "hermes_cron_status": {"gateway_running": True, "active_jobs": 7, "profile": "tender-export-os"},
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    forecast_dir = tmp_path / "outputs" / "demand_forecasting"
    forecast_dir.mkdir(parents=True)
    (forecast_dir / "forecast_calibration_20990101.json").write_text(
        json.dumps(
            {
                "status": "INSUFFICIENT_MATURE_SAMPLE",
                "review_date": "2099-01-01",
                "mature_sample_size": 0,
                "minimum_mature_sample": 30,
                "brier_score": None,
            }
        ),
        encoding="utf-8",
    )

    report = desk.build_report(project_root=tmp_path, today=desk.dt.date(2099, 1, 1))

    assert report["hermes_runtime_health"]["status"] == "PASS"
    assert report["hermes_runtime_health"]["active_jobs"] == 7
    assert report["prediction_health"]["status"] == "INSUFFICIENT_MATURE_SAMPLE"
    assert report["prediction_health"]["mature_sample_size"] == 0


def test_operating_desk_surfaces_hermes_capability_utilization(tmp_path: Path) -> None:
    audit_dir = tmp_path / "outputs" / "hermes_profile_audit"
    audit_dir.mkdir(parents=True)
    (audit_dir / "hermes_profile_capability_audit_20260714T000000Z.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "capability_utilization": {
                    "schema_version": "hermes_capability_utilization.v1",
                    "capabilities": {
                        "scheduler": {"status": "CONFIGURED_AND_OBSERVED", "observed_jobs": 16},
                        "profiles": {"status": "CONFIGURED", "configured_profiles": 9},
                        "mcp": {"status": "CONFIGURED_AND_USED", "observed_calls_in_insights_window": 44},
                        "session_runtime": {"status": "USED", "sessions_in_insights_window": 52},
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    report = desk.build_report(project_root=tmp_path, today=desk.dt.date(2026, 7, 14))

    utilization = report["hermes_capability_utilization"]
    assert utilization["status"] == "PASS"
    assert utilization["observed_jobs"] == 16
    assert utilization["configured_profiles"] == 9
    assert report["summary"]["hermes_capability_audit_status"] == "PASS"
