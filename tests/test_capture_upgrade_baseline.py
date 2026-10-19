from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.capture_upgrade_baseline import (
    capture_data_counts,
    redact,
    sha256_file,
    write_report,
)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_redact_removes_secret_bearing_fields_and_values() -> None:
    payload = {
        "profile": "tender-export-os",
        "token": "secret-token-value",
        "credentials_included": False,
        "nested": {"api_key": "abc123", "status": "healthy"},
        "lines": ["Provider healthy", "Authorization: Bearer private-value"],
    }

    redacted = redact(payload)

    assert redacted["profile"] == "tender-export-os"
    assert redacted["token"] == "[REDACTED]"
    assert redacted["credentials_included"] is False
    assert redacted["nested"]["api_key"] == "[REDACTED]"
    assert redacted["nested"]["status"] == "healthy"
    assert redacted["lines"][1] == "[REDACTED_STRING]"


def test_capture_data_counts_reports_maturity_quotes_and_inbound(tmp_path: Path) -> None:
    data = tmp_path / "data"
    write_csv(data / "master_cases.csv", ["case_id"], [{"case_id": "GOV-1"}, {"case_id": "EXP-1"}])
    write_csv(data / "forecast_candidates.csv", ["forecast_id"], [{"forecast_id": "FC-1"}])
    write_csv(
        data / "forecast_backtests.csv",
        ["backtest_id", "is_mature"],
        [{"backtest_id": "FBT-1", "is_mature": "TRUE"}, {"backtest_id": "FBT-2", "is_mature": "FALSE"}],
    )
    write_csv(
        data / "quote_master.csv",
        ["quote_id", "supplier_specific_quote", "indicative_price_only", "quote_proof_path"],
        [
            {
                "quote_id": "Q-1",
                "supplier_specific_quote": "TRUE",
                "indicative_price_only": "FALSE",
                "quote_proof_path": "receipts/supplier_quotes/q1.pdf",
            },
            {
                "quote_id": "Q-2",
                "supplier_specific_quote": "FALSE",
                "indicative_price_only": "TRUE",
                "quote_proof_path": "outputs/listing.json",
            },
        ],
    )
    write_csv(
        data / "communication_log.csv",
        ["communication_id", "direction"],
        [{"communication_id": "C-1", "direction": "INBOUND"}],
    )
    write_csv(
        data / "outreach_queue.csv",
        ["outreach_id", "send_status"],
        [{"outreach_id": "O-1", "send_status": "SENT"}],
    )

    counts = capture_data_counts(tmp_path)

    assert counts["master_cases"] == 2
    assert counts["forecast_candidates"] == 1
    assert counts["forecast_backtests"] == 2
    assert counts["mature_forecast_outcomes"] == 1
    assert counts["quote_rows"] == 2
    assert counts["strict_quote_proof_candidates"] == 1
    assert counts["inbound_communications"] == 1
    assert counts["sent_outreach"] == 1


def test_write_report_adds_archive_hash_and_never_embeds_archive_bytes(tmp_path: Path) -> None:
    archive = tmp_path / "profile.tar.gz"
    archive.write_bytes(b"profile-backup")
    output = tmp_path / "baseline.json"

    report = write_report(
        output,
        {"profiles": ["tender-export-os"], "auth": {"token": "do-not-store"}},
        archive_path=archive,
    )

    stored = json.loads(output.read_text(encoding="utf-8"))
    assert stored == report
    assert stored["profile_export"]["sha256"] == sha256_file(archive)
    assert stored["profile_export"]["bytes"] == len(b"profile-backup")
    assert stored["auth"]["token"] == "[REDACTED]"
    assert "profile-backup" not in output.read_text(encoding="utf-8")
