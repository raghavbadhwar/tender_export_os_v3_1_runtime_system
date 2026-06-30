import csv
import json

from scripts.source_adapters.base import SourceOpportunity
import scripts.source_runtime.dedupe as dedupe_module
from scripts.source_runtime.dedupe import DedupeEngine


def write_csv(path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def test_dedupe_loads_events_and_evidence_manifests(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dedupe_module, "PROJECT_ROOT", tmp_path)
    master = tmp_path / "data" / "master_cases.csv"
    headers = ["case_id", "workflow_type", "source_url", "opportunity_title", "buyer_name", "deadline_date", "source_name", "product_or_service"]
    write_csv(master, headers, [])
    events = tmp_path / "data" / "events.jsonl"
    events.write_text(
        json.dumps(
            {
                "event_type": "case.created",
                "object_type": "case",
                "case_id": "GOV-20990101-001",
                "object_id": "GOV-20990101-001",
                "payload": {
                    "source_name": "CPPP",
                    "source_url": "https://example.test/tender/1",
                    "opportunity_title": "Fixture Tender",
                    "buyer_name": "Fixture Buyer",
                    "deadline_date": "2099-01-31",
                    "workflow_type": "GOV",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "outputs" / "evidence" / "private" / "GOV" / "CASE" / "evidence_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"case_id": "GOV-20990101-002", "downloads": [{"sha256": "abc123"}]}), encoding="utf-8")

    engine = DedupeEngine(master)
    opportunity = SourceOpportunity("CPPP", "primary", "GOV", "https://example.test/tender/1", "NEW", "Fixture Tender")
    assert engine.find_duplicate(opportunity) == "GOV-20990101-001"
    assert engine.existing
