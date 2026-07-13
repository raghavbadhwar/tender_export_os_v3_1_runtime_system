from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from scripts.record_case_outcome import (
    append_outcome,
    build_outcome_event,
    supersede_outcome,
    validate_evidence,
    validate_outcome,
)


def outcome(evidence: Path) -> dict[str, str]:
    return {
        "outcome_id": "OUT-GOV-1-WON",
        "case_id": "GOV-1",
        "workflow_type": "GOV",
        "outcome_type": "WON",
        "outcome_value": "Contract awarded",
        "occurred_at": "2099-02-01T10:00:00+00:00",
        "evidence_path": str(evidence),
        "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
        "verification_status": "VERIFIED",
        "recorded_by": "owner",
        "recorded_at": "2099-02-01T11:00:00+00:00",
        "supersedes_outcome_id": "",
        "notes": "Fixture",
    }


def test_outcome_evidence_hash_and_event_contract(tmp_path: Path) -> None:
    evidence = tmp_path / "award.pdf"
    evidence.write_bytes(b"verified award evidence")
    row = outcome(evidence)

    proof = validate_evidence(evidence, row["evidence_sha256"])
    event = build_outcome_event(row, actor="pytest")

    assert proof["sha256"] == row["evidence_sha256"]
    assert event["event_type"] == "case.outcome_recorded"
    assert event["object_type"] == "case_outcome"
    assert event["payload"]["row"]["outcome_id"] == row["outcome_id"]
    assert event["citations"] == [str(evidence)]


def test_outcome_requires_existing_case_allowed_type_timestamp_and_explicit_verification(tmp_path: Path) -> None:
    evidence = tmp_path / "award.pdf"
    evidence.write_bytes(b"verified award evidence")
    row = outcome(evidence)

    assert validate_outcome(row, cases=[{"case_id": "GOV-1", "workflow_type": "GOV"}], existing=[])["ok"] is True
    with pytest.raises(ValueError, match="unknown case_id"):
        validate_outcome(row, cases=[], existing=[])
    with pytest.raises(ValueError, match="outcome_type"):
        validate_outcome(row | {"outcome_type": "MADE_UP"}, cases=[{"case_id": "GOV-1", "workflow_type": "GOV"}], existing=[])
    with pytest.raises(ValueError, match="occurred_at"):
        validate_outcome(row | {"occurred_at": "yesterday"}, cases=[{"case_id": "GOV-1", "workflow_type": "GOV"}], existing=[])
    with pytest.raises(ValueError, match="verification_status"):
        validate_outcome(row | {"verification_status": ""}, cases=[{"case_id": "GOV-1", "workflow_type": "GOV"}], existing=[])


def test_append_and_supersede_outcome_are_event_first_and_idempotent(tmp_path: Path) -> None:
    evidence = tmp_path / "award.pdf"
    evidence.write_bytes(b"verified award evidence")
    outcomes_path = tmp_path / "case_outcomes.csv"
    events_path = tmp_path / "events.jsonl"
    row = outcome(evidence)

    first = append_outcome(row, outcomes_path=outcomes_path, events_path=events_path, actor="pytest")
    duplicate = append_outcome(row, outcomes_path=outcomes_path, events_path=events_path, actor="pytest")
    replacement = supersede_outcome(
        row,
        row | {"outcome_id": "OUT-GOV-1-CORRECTED", "outcome_value": "Corrected award evidence"},
    )

    with outcomes_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert len(events_path.read_text(encoding="utf-8").splitlines()) == 1
    assert first["event_id"] == duplicate["event_id"]
    assert replacement["supersedes_outcome_id"] == row["outcome_id"]
