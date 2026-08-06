from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

from scripts.initialize_event_ledger import REGISTER_SPECS
from scripts.rebuild_projections_from_events import PROJECTIONS, project


ROOT = Path(__file__).resolve().parents[1]
NEW_EVENTS = {
    "source.adapter_degraded",
    "tender.deadline_changed",
    "case.fast_kill_completed",
    "supplier.candidate_verified",
    "supplier.quote_received",
    "supplier.quote_rejected",
    "buyer.reply_received",
    "buyer.opted_out",
    "buyer.rfq_verified",
    "approval.expired",
    "execution.receipt_ingested",
    "case.outcome_recorded",
    "payment.received",
    "forecast.matured",
    "learning.proposal_staged",
    "learning.proposal_evaluated",
    "learning.promoted",
}


def public_example_projections() -> dict:
    projections = {}
    for name, spec in PROJECTIONS.items():
        source = Path(spec["file"])
        example = ROOT / "data" / "examples" / f"{source.stem}.example.csv"
        assert example.is_file(), f"missing public example for {source.name}"
        projections[name] = spec | {"file": example}
    return projections


def test_phase3_event_types_and_object_types_are_registered() -> None:
    schema = json.loads((ROOT / "config/schemas/event.schema.json").read_text(encoding="utf-8"))
    registry = yaml.safe_load((ROOT / "config/schemas/event_types.yaml").read_text(encoding="utf-8"))

    assert NEW_EVENTS <= set(schema["event_types"])
    assert NEW_EVENTS <= set(registry["events"])
    assert {
        "case_outcome",
        "learning_proposal",
        "model_registry",
        "agent_evaluation",
        "payment",
        "buyer_reply",
        "forecast_observation",
    } <= set(schema["object_types"])


def test_four_learning_grade_registers_match_schemas_and_examples() -> None:
    expected = {
        "case_outcomes": {
            "outcome_id",
            "case_id",
            "workflow_type",
            "outcome_type",
            "outcome_value",
            "occurred_at",
            "evidence_path",
            "evidence_sha256",
            "verification_status",
            "recorded_by",
            "recorded_at",
            "supersedes_outcome_id",
            "notes",
        },
        "learning_proposals": {
            "proposal_id",
            "proposal_target",
            "evidence_event_ids",
            "affected_workflows",
            "current_version",
            "proposed_version",
            "fixtures",
            "evaluation_report_path",
            "rollback_artifact_path",
            "status",
            "approval_id",
            "applied_at",
        },
        "model_registry": {
            "model_id",
            "target_id",
            "workflow_type",
            "horizon_days",
            "model_version",
            "feature_schema_hash",
            "mature_sample_count",
            "positive_class_count",
            "negative_class_count",
            "calibration_status",
            "status",
            "artifact_path",
            "approval_id",
            "rollback_version",
        },
        "agent_evaluations": {
            "evaluation_id",
            "profile",
            "scenario_id",
            "case_id",
            "run_id",
            "repeat_number",
            "expected_result",
            "actual_result",
            "evidence_completeness_pct",
            "policy_compliance",
            "latency_ms",
            "input_tokens",
            "output_tokens",
            "cost_usd",
            "score",
            "status",
            "report_path",
        },
    }
    for name, required in expected.items():
        schema = json.loads((ROOT / f"config/schemas/{name}.schema.json").read_text(encoding="utf-8"))
        with (ROOT / f"data/examples/{name}.example.csv").open(newline="", encoding="utf-8") as handle:
            example_headers = set(next(csv.reader(handle)))
        assert required <= set(schema["required_columns"])
        assert set(schema["required_columns"]) <= example_headers


def test_new_registers_are_snapshot_seeded_and_rebuildable() -> None:
    projection_names = {"case_outcome", "learning_proposal", "model_registry", "agent_evaluation"}
    assert projection_names <= set(PROJECTIONS)
    initialized = {row[0] for row in REGISTER_SPECS}
    assert projection_names <= initialized

    rows = project(
        [
            {
                "event_type": "case_outcome.snapshot_imported",
                "object_type": "case_outcome",
                "object_id": "OUT-1",
                "case_id": "GOV-1",
                "payload": {
                    "row": {
                        "outcome_id": "OUT-1",
                        "case_id": "GOV-1",
                        "workflow_type": "GOV",
                        "outcome_type": "LOST",
                        "verification_status": "VERIFIED",
                    }
                },
            },
            {
                "event_type": "case.outcome_recorded",
                "object_type": "case_outcome",
                "object_id": "OUT-2",
                "case_id": "GOV-1",
                "payload": {
                    "row": {
                        "outcome_id": "OUT-2",
                        "case_id": "GOV-1",
                        "workflow_type": "GOV",
                        "outcome_type": "WON",
                        "verification_status": "VERIFIED",
                    }
                },
            },
            {
                "event_type": "case.status_changed",
                "object_type": "case",
                "object_id": "GOV-HISTORICAL",
                "case_id": "GOV-HISTORICAL",
                "payload": {"new_status": "LOST"},
            },
        ],
        projections=public_example_projections(),
    )["case_outcome"]

    assert [row["outcome_id"] for row in rows] == ["OUT-1", "OUT-2"]
    assert all(row["case_id"] == "GOV-1" for row in rows)
