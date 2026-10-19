from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts import record_relationship_memory as memory


CASE_ID = "EXP-20990101-001"
BUYER_ID = "BUY-TARGET-001"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixture_register(path: Path) -> None:
    headers, _ = memory.load_csv(Path(__file__).parents[1] / "data" / "relationship_memory.csv")
    write_csv(path, headers, [])


def fixture_value(project_root: Path, receipt: Path) -> dict[str, str]:
    digest = hashlib.sha256(receipt.read_bytes()).hexdigest()
    summary = "Buyer asks that factual product drafts be prepared before any approved reply."
    return {
        "memory_id": memory.stable_id(BUYER_ID, CASE_ID, "COMMUNICATION_PREFERENCE", summary, digest),
        "buyer_id": BUYER_ID,
        "case_id": CASE_ID,
        "memory_type": "COMMUNICATION_PREFERENCE",
        "summary": summary,
        "evidence_receipt_path": str(receipt.relative_to(project_root)),
        "evidence_sha256": digest,
        "verification_status": "VERIFIED",
        "source_communication_id": "COM-001",
        "status": "ACTIVE",
        "recorded_by": "owner",
        "recorded_at": "2099-01-02T10:00:00+00:00",
        "review_after": "2099-07-01",
        "supersedes_memory_id": "",
        "notes": "Sanitized preference only.",
    }


def prepare_project(monkeypatch, tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    project_root = tmp_path
    data = project_root / "data"
    receipt = project_root / "receipts" / "buyer_replies" / "COM-001.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({"communication_id": "COM-001", "connector": "GMAIL_PLUGIN", "classification": "SUBSTANTIVE"}), encoding="utf-8")
    register = data / "relationship_memory.csv"
    fixture_register(register)
    cases = data / "master_cases.csv"
    communications = data / "communication_log.csv"
    write_csv(cases, ["case_id", "workflow_type"], [{"case_id": CASE_ID, "workflow_type": "EXPORT"}])
    write_csv(communications, ["communication_id"], [{"communication_id": "COM-001"}])
    monkeypatch.setattr(memory, "PROJECT_ROOT", project_root)
    return register, cases, communications, receipt


def test_relationship_memory_records_only_sanitized_verified_metadata(monkeypatch, tmp_path: Path) -> None:
    register, cases, communications, receipt = prepare_project(monkeypatch, tmp_path)
    value = fixture_value(tmp_path, receipt)

    result = memory.record_memory(
        value,
        register_path=register,
        cases_path=cases,
        communications_path=communications,
        events_path=tmp_path / "data" / "events.jsonl",
        receipts_dir=tmp_path / "receipts" / "relationship_memory",
        actor="pytest",
    )

    _, rows = memory.load_csv(register)
    saved_receipt = json.loads(Path(result["receipt_path"]).read_text(encoding="utf-8"))
    event = json.loads((tmp_path / "data" / "events.jsonl").read_text(encoding="utf-8"))
    assert rows[0]["summary"] == value["summary"]
    assert "raw message" in saved_receipt["privacy_note"]
    assert event["event_type"] == "relationship_memory.recorded"
    assert event["payload"]["verification_status"] == "VERIFIED"
    assert result["external_actions_executed"] is False


def test_relationship_memory_rejects_raw_bodies_and_direct_contacts(monkeypatch, tmp_path: Path) -> None:
    register, cases, communications, receipt = prepare_project(monkeypatch, tmp_path)
    value = fixture_value(tmp_path, receipt) | {"summary": "From: buyer@example.com\nPlease quote immediately"}

    with pytest.raises(ValueError, match="single-line|identifiers"):
        memory.validate_memory(value, cases=memory.load_csv(cases)[1], communications=memory.load_csv(communications)[1], existing=[])

    raw_receipt = tmp_path / "receipts" / "buyer_replies" / "raw.json"
    raw_receipt.write_text(json.dumps({"body_text": "private raw reply"}), encoding="utf-8")
    raw = fixture_value(tmp_path, raw_receipt)
    with pytest.raises(ValueError, match="prohibited raw/private"):
        memory.validate_memory(raw, cases=memory.load_csv(cases)[1], communications=memory.load_csv(communications)[1], existing=[])


def test_opt_out_can_only_be_retained_as_active_verified_memory(monkeypatch, tmp_path: Path) -> None:
    register, cases, communications, receipt = prepare_project(monkeypatch, tmp_path)
    value = fixture_value(tmp_path, receipt) | {
        "memory_type": "OPT_OUT",
        "status": "EXPIRED",
        "summary": "Buyer opted out; do not follow up without a verified owner-recorded correction.",
    }

    with pytest.raises(ValueError, match="OPT_OUT"):
        memory.validate_memory(value, cases=memory.load_csv(cases)[1], communications=memory.load_csv(communications)[1], existing=[])
