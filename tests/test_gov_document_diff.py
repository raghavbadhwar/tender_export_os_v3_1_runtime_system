from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.gov_deep_read_contract import load_contract
from scripts.gov_document_diff import apply_invalidation, compare_reports, write_document_diff
from scripts.rebuild_projections_from_events import project
from scripts.validate_case_readiness import evaluate_case


def citation(page: int = 1) -> dict[str, str | int]:
    return {"source_path": "outputs/evidence/private/GOV-1/tender.pdf", "source_url": "https://eprocure.gov.in/tender/GOV-1", "page": page, "section": "fixture"}


def report() -> dict:
    facts = {
        key: {"status": "EXTRACTED", "value": f"Observed {key}", "reason": "", "citations": [citation()]}
        for key in load_contract()["required_fact_keys"]
    }
    return {
        "schema_version": "gov_deep_read.v1",
        "case_id": "GOV-1",
        "workflow_type": "GOV",
        "extraction_status": "COMPLETE",
        "generated_at": "2099-01-01T00:00:00+00:00",
        "source_documents": [{"source_path": "outputs/evidence/private/GOV-1/tender.pdf", "source_url": "https://eprocure.gov.in/tender/GOV-1", "sha256": "a" * 64, "document_type": "NIT", "page_count": 5}],
        "facts": facts,
        "corrigenda": [{"status": "NONE_FOUND", "summary": "None", "citations": [citation()]}],
        "boq_lines": [{"line_id": "1", "description": "Item A", "quantity": "1", "unit": "each", "specification": "Base", "citations": [citation(2)]}],
        "ambiguous_clauses": [],
        "recommended_case_status": "SUPPLIER_SEARCH",
        "external_actions_executed": False,
    }


def test_document_diff_detects_risky_changes_and_invalidation_scope() -> None:
    before = report()
    after = report()
    after["facts"]["deadline_date"]["value"] = "2099-02-01"
    after["facts"]["emd"]["value"] = "500000"
    after["boq_lines"][0]["quantity"] = "25"

    diff = compare_reports(before, after)

    assert {change["field"] for change in diff["changes"]} >= {"deadline_date", "emd", "boq_lines"}
    assert {"deep_read", "supplier", "pricing", "compliance", "artifacts", "approval", "execution"} <= set(diff["invalidate_stages"])
    assert diff["case_updates"]["corrigenda_status"] == "CHANGED_REVIEW_REQUIRED"


def test_every_material_tender_clause_family_creates_a_readiness_hold() -> None:
    cases = {
        "eligibility": ("facts", "eligibility", "Different eligibility criterion", {"fast_kill", "deep_read", "approval"}),
        "deadline": ("facts", "deadline_date", "2099-02-01", {"fast_kill", "deep_read", "execution"}),
        "price": ("facts", "unit_price", "999", {"pricing", "artifacts", "approval"}),
        "delivery": ("facts", "delivery", "Delivery in 120 days", {"supplier", "pricing", "approval"}),
        "emd": ("facts", "emd", "500000", {"pricing", "artifacts", "approval"}),
        "pbg": ("facts", "pbg", "10 percent", {"pricing", "artifacts", "approval"}),
        "submission": ("facts", "required_documents", "Add OEM authorization", {"artifacts", "approval", "execution"}),
        "boq": ("boq", "boq_lines", "25", {"deep_read", "supplier", "pricing", "approval"}),
    }
    for label, (kind, key, value, expected_stages) in cases.items():
        before = report()
        after = report()
        if kind == "boq":
            after["boq_lines"][0]["quantity"] = value
        else:
            if key not in after["facts"]:
                after["facts"][key] = {
                    "status": "EXTRACTED",
                    "value": "",
                    "reason": "",
                    "citations": [citation()],
                }
            after["facts"][key]["value"] = value
        diff = compare_reports(before, after)

        assert diff["review_required"], label
        assert diff["case_updates"]["pricing_done"] == "FALSE", label
        assert expected_stages <= set(diff["invalidate_stages"]), label


def test_apply_invalidation_is_event_first_and_blocks_readiness_until_review(tmp_path: Path) -> None:
    before = report()
    after = report()
    after["facts"]["payment"]["value"] = "Payment after 180 days"
    diff = compare_reports(before, after)
    report_path = write_document_diff(diff, output_dir=tmp_path)
    cases = tmp_path / "master_cases.csv"
    cases.write_text(
        "case_id,workflow_type,status,corrigenda_status,corrigenda_summary,deep_read_done,supplier_search_done,pricing_done,execution_sub_status,updated_at\n"
        "GOV-1,GOV,PRICING_READY,,,TRUE,TRUE,TRUE,,2099-01-01\n",
        encoding="utf-8",
    )
    events = tmp_path / "events.jsonl"

    result = apply_invalidation(diff, report_path=report_path, master_cases_path=cases, events_path=events, actor="pytest")

    assert result["event_id"]
    event = json.loads(events.read_text(encoding="utf-8").strip())
    assert event["event_type"] == "case.updated_from_corrigendum"
    with cases.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["corrigenda_status"] == "CHANGED_REVIEW_REQUIRED"
    assert row["pricing_done"] == "FALSE"
    readiness = evaluate_case(row, quotes=[], approvals=[])
    assert any("corrigenda review" in item.lower() for item in readiness["blockers"])


def test_corrigendum_event_rebuilds_the_case_projection(tmp_path: Path, monkeypatch) -> None:
    from scripts import rebuild_projections_from_events as rebuild

    projection_file = tmp_path / "master_cases.csv"
    projection_file.write_text("case_id,status,corrigenda_status,pricing_done\n", encoding="utf-8")
    monkeypatch.setattr(
        rebuild,
        "PROJECTIONS",
        {
            "case": {
                "file": projection_file,
                "id_field": "case_id",
                "snapshot_event": "case.snapshot_imported",
                "upsert_events": ["case.updated_from_corrigendum"],
            }
        },
    )
    rows = project(
        [
            {
                "event_type": "case.snapshot_imported",
                "case_id": "GOV-1",
                "object_type": "case",
                "object_id": "GOV-1",
                "payload": {"row": {"case_id": "GOV-1", "status": "PRICING_READY", "pricing_done": "TRUE"}},
            },
            {
                "event_type": "case.updated_from_corrigendum",
                "case_id": "GOV-1",
                "object_type": "case",
                "object_id": "GOV-1",
                "payload": {"updates": {"corrigenda_status": "CHANGED_REVIEW_REQUIRED", "pricing_done": "FALSE"}},
            },
        ]
    )["case"]

    assert rows == [{"case_id": "GOV-1", "status": "PRICING_READY", "corrigenda_status": "CHANGED_REVIEW_REQUIRED", "pricing_done": "FALSE"}]
