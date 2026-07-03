from scripts.build_source_yield_metrics import build_metrics


def test_source_yield_tracks_access_friction_and_quote_proofs() -> None:
    rows = build_metrics(
        source_health=[
            {"source_name": "Example Portal", "source_type": "gov", "workflow": "GOV", "total_checks": "10", "health_status": "Working"},
            {"source_name": "Paywall Source", "source_type": "gov", "workflow": "GOV", "total_checks": "5", "paywalled": "TRUE", "health_status": "Paywalled"},
        ],
        cases=[{"case_id": "GOV-1", "source_name": "Example Portal", "status": "PRICING_READY"}],
        run_rows=[],
        quotes=[
            {
                "quote_id": "Q-1",
                "case_id": "GOV-1",
                "supplier_id": "SUP-1",
                "quote_received_at": "2026-07-01T10:00:00",
                "quote_proof_type": "quotation_pdf",
                "quote_proof_path": "receipts/supplier_quotes/q1.pdf",
            }
        ],
        approvals=[{"case_id": "GOV-1", "approval_id": "APR-1"}],
    )

    by_source = {row["source_name"]: row for row in rows}
    assert by_source["Example Portal"]["strict_quote_proof_cases"] == 1
    assert by_source["Example Portal"]["promoted_cases"] == 1
    assert by_source["Paywall Source"]["access_friction"] is True
