from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scripts.event_ledger import append_event, load_events


def test_concurrent_appends_remain_ordered_and_unique(tmp_path: Path) -> None:
    events_file = tmp_path / "events.jsonl"

    def append(index: int) -> None:
        append_event(
            "system.snapshot_started",
            "test",
            object_type="system",
            object_id=f"SNAP-{index}",
            payload={"index": index},
            events_file=events_file,
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(append, range(16)))
    events = load_events(events_file)
    positions = [event["stream_position"] for event in events]
    assert len(events) == 16
    assert positions == list(range(1, 17))
    assert len({event["event_id"] for event in events}) == 16
