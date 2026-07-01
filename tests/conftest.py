import sys
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _read_headers(example_name: str) -> list[str]:
    with (PROJECT_ROOT / "data" / "examples" / example_name).open(newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def _write_csv_if_missing(relative_path: str, headers: list[str], rows: list[dict[str, object]]) -> None:
    path = PROJECT_ROOT / relative_path
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in headers})


def _case(case_id: str, workflow_type: str = "EXPORT", **updates: object) -> dict[str, object]:
    row = {
        "case_id": case_id,
        "workflow_type": workflow_type,
        "source_name": "Example RFQ Board",
        "source_url": "https://example.com/rfq/fixture",
        "opportunity_title": f"Sanitized fixture opportunity {case_id}",
        "buyer_name": "Example Buyer",
        "buyer_type": "Company",
        "product_or_service": "Example product",
        "quantity": "100",
        "unit": "each",
        "deadline_date": "2099-01-31",
        "status": "SUPPLIER_SEARCH" if workflow_type == "EXPORT" else "WATCHLIST",
        "deep_read_done": "TRUE",
        "supplier_search_done": "FALSE",
        "pricing_done": "FALSE",
        "approval_status": "PENDING",
        "scomet_flag": "FALSE",
        "buyer_country": "Exampleland",
        "delivery_location": "Exampleland",
        "created_at": "2099-01-01",
        "updated_at": "2099-01-01",
        "created_by_agent": "pytest_fixture",
        "evidence_level": "PUBLIC_LISTING_ONLY",
    }
    row.update(updates)
    return row


def _rfq(case_id: str, stage: str = "RAW_LEAD", evidence_status: str = "MISSING") -> dict[str, object]:
    return {
        "rfq_id": f"RFQ-{case_id}",
        "case_id": case_id,
        "buyer_id": f"BUY-{case_id}",
        "source_name": "Example RFQ Board",
        "source_url": "https://example.com/rfq/fixture",
        "rfq_reference": f"REF-{case_id}",
        "product_or_service": "Example product",
        "quantity": "100",
        "unit": "each",
        "buyer_country": "Exampleland",
        "deadline_date": "2099-01-31",
        "evidence_status": evidence_status,
        "rfq_stage": stage,
        "rfq_score": "20",
        "market_fit_score": "55",
        "source_reliability_score": "40",
        "missing_evidence": "sanitized fixture evidence gap",
        "evidence_links": "https://example.com/rfq/fixture",
        "notes": "Pytest-only sanitized runtime fixture.",
        "created_at": "2099-01-01",
        "updated_at": "2099-01-01",
    }


def ensure_public_template_runtime_fixtures() -> None:
    master_headers = _read_headers("master_cases.example.csv")
    _write_csv_if_missing(
        "data/master_cases.csv",
        master_headers,
        [
            _case("GOV-20260630-001", "GOV", delivery_location="Example City"),
            _case("EXP-20260630-001", source_name="Alibaba RFQ", source_url="https://rfq.alibaba.com", buyer_name="Unknown buyer"),
            _case("EXP-20260630-002", source_name="Example Directory", source_url="", buyer_name="Unknown buyer"),
            _case("EXP-20260630-003", source_name="TradeKey", source_url="https://example.com/tradekey/fixture", buyer_name="Masked marketplace buyer"),
            _case("EXP-20260630-004", source_name="Masked RFQ Board", source_url="https://example.com/hidden/fixture", buyer_name="Visible example buyer"),
            _case("EXP-20260630-005", source_name="UNDP Procurement", source_url="https://example.com/undp/rfq-005", buyer_name="UNDP Example Office", notes="public procurement portal"),
            _case("EXP-20260630-006", source_name="UNDP Procurement", source_url="https://example.com/undp/rfq-006", buyer_name="UNDP Example Office", notes="public procurement portal"),
        ],
    )

    _write_csv_if_missing(
        "data/approvals_receipts.csv",
        _read_headers("approvals_receipts.example.csv"),
        [
            {
                "approval_id": "APR-EXAMPLE-001",
                "case_id": "GOV-20260630-001",
                "workflow_type": "GOV",
                "action_approved": "review_example_bid_pack",
                "proposed_by_agent": "approval_desk_agent",
                "approval_card_path": "receipts/examples/sample_approval_card.html",
                "amount_inr": "1000",
                "approval_status": "PENDING",
                "receipt_id": "RCPT-EXAMPLE-001",
                "receipt_path": "receipts/examples/sample_approval_card.html",
                "external_effect": "NONE_DECISION_ONLY",
                "notes": "Pytest-only sanitized approval fixture.",
            }
        ],
    )
    _write_csv_if_missing("data/buyer_master.csv", _read_headers("buyer_master.example.csv"), [])
    _write_csv_if_missing("data/quote_master.csv", _read_headers("quote_master.example.csv"), [])
    _write_csv_if_missing(
        "data/rfq_master.csv",
        _read_headers("rfq_master.example.csv"),
        [_rfq("EXP-20260630-001"), _rfq("EXP-20260630-002")],
    )
    _write_csv_if_missing(
        "data/source_health.csv",
        _read_headers("source_health.example.csv"),
        [
            {
                "source_name": "Example Public Tender Portal",
                "source_type": "gov",
                "url": "https://example.com/tenders",
                "health_status": "Working",
                "last_checked_at": "2099-01-01T09:00:00+05:30",
                "records_found": "1",
                "notes": "Pytest-only sanitized source health fixture.",
                "created_at": "2099-01-01",
                "updated_at": "2099-01-01",
            }
        ],
    )
    _write_csv_if_missing("data/plugin_health.csv", _read_headers("plugin_health.example.csv"), [])
    _write_csv_if_missing("data/demand_research.csv", _read_headers("demand_research.example.csv"), [])
    _write_csv_if_missing("data/drive_manifest.csv", _read_headers("drive_manifest.example.csv"), [])
    _write_csv_if_missing(
        "data/agent_run_log.csv",
        [
            "run_id",
            "run_date",
            "run_time",
            "agent_name",
            "trigger_type",
            "cases_processed",
            "cases_created",
            "cases_rejected",
            "cases_updated",
            "sources_checked",
            "sources_failed",
            "actions_taken",
            "approval_cards_created",
            "receipts_created",
            "errors",
            "warnings",
            "runtime_seconds",
            "status",
            "notes",
        ],
        [
            {
                "run_id": "RUN-20990101090000-PYTEST",
                "run_date": "2099-01-01",
                "run_time": "09:00:00",
                "agent_name": "pytest_fixture",
                "trigger_type": "public_template_test",
                "status": "SUCCESS",
                "notes": "Pytest-only sanitized runtime fixture.",
            }
        ],
    )


ensure_public_template_runtime_fixtures()
