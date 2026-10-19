from __future__ import annotations

import json
from pathlib import Path

from scripts.event_ledger import append_event
from scripts.export_ledger_checkpoint import compare_checkpoint, generate_checkpoint


def make_ledger(path: Path, count: int = 2) -> None:
    for index in range(count):
        append_event(
            "case.created",
            "test",
            case_id=f"CASE-{index}",
            object_type="case",
            object_id=f"CASE-{index}",
            payload={"status": "created", "buyer_name": "private-value"},
            citations=["fixture://source"],
            events_file=path,
        )


def test_identical_bytes_produce_identical_checkpoint(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    make_ledger(source)
    copy = tmp_path / "copy.jsonl"
    copy.write_bytes(source.read_bytes())
    assert generate_checkpoint(source) == generate_checkpoint(copy)


def test_checkpoint_contains_only_privacy_safe_digests_and_counts(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    make_ledger(source)
    checkpoint = generate_checkpoint(source)
    assert set(checkpoint) == {"schema_version", "event_count", "terminal_hash", "source_sha256", "timestamp_policy", "event_time_max_utc"}
    assert checkpoint["event_count"] == 2
    assert "private-value" not in json.dumps(checkpoint)
    assert "CASE-" not in json.dumps(checkpoint)


def test_tamper_and_truncation_do_not_match_prior_checkpoint(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    make_ledger(source, count=3)
    expected = generate_checkpoint(source)
    source.write_text(source.read_text().replace('"status": "created"', '"status":"changed"', 1))
    tampered = generate_checkpoint(source)
    assert compare_checkpoint(tampered, expected)
    source.write_text("\n".join(source.read_text().splitlines()[:-1]) + "\n")
    truncated = generate_checkpoint(source)
    assert "event_count" in compare_checkpoint(truncated, expected)
    assert "terminal_hash" in compare_checkpoint(truncated, expected)


def test_empty_ledger_has_deterministic_genesis_checkpoint(tmp_path: Path) -> None:
    first = generate_checkpoint(tmp_path / "missing.jsonl")
    second = generate_checkpoint(tmp_path / "missing.jsonl")
    assert first == second
    assert first["event_count"] == 0
