from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.generate_approval_cards import structured_card
from scripts.validate_authority_matrix import validate_authority_matrix


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def test_authority_matrix_matches_live_policy_and_profile_registry() -> None:
    matrix = load_yaml(PROJECT_ROOT / "config" / "agent_authority_matrix.yaml")
    tool_policy = load_yaml(PROJECT_ROOT / "config" / "tender_tool_policy.yaml")
    approval_policy = load_yaml(PROJECT_ROOT / "config" / "approval_policy.yaml")
    profiles = load_yaml(PROJECT_ROOT / "config" / "hermes_specialist_profiles.yaml")

    errors = validate_authority_matrix(matrix, tool_policy, approval_policy, profiles)

    assert errors == [], "\n".join(errors)


def test_authority_matrix_rejects_an_unapproved_external_action() -> None:
    matrix = load_yaml(PROJECT_ROOT / "config" / "agent_authority_matrix.yaml")
    tool_policy = load_yaml(PROJECT_ROOT / "config" / "tender_tool_policy.yaml")
    approval_policy = load_yaml(PROJECT_ROOT / "config" / "approval_policy.yaml")
    profiles = load_yaml(PROJECT_ROOT / "config" / "hermes_specialist_profiles.yaml")

    matrix["action_classes"]["external_message"]["approval_mode"] = "not_required"

    errors = validate_authority_matrix(matrix, tool_policy, approval_policy, profiles)

    assert any("external_message" in error and "approval" in error for error in errors)


def test_authority_matrix_rejects_missing_hard_limit_mapping() -> None:
    matrix = load_yaml(PROJECT_ROOT / "config" / "agent_authority_matrix.yaml")
    tool_policy = load_yaml(PROJECT_ROOT / "config" / "tender_tool_policy.yaml")
    approval_policy = load_yaml(PROJECT_ROOT / "config" / "approval_policy.yaml")
    profiles = load_yaml(PROJECT_ROOT / "config" / "hermes_specialist_profiles.yaml")

    matrix["policy_action_classes"].pop("submit_tender_bid")

    errors = validate_authority_matrix(matrix, tool_policy, approval_policy, profiles)

    assert any("submit_tender_bid" in error and "mapping" in error for error in errors)


def test_authority_matrix_json_schema_accepts_declared_matrix() -> None:
    matrix = load_yaml(PROJECT_ROOT / "config" / "agent_authority_matrix.yaml")
    schema = json.loads((PROJECT_ROOT / "config" / "schemas" / "agent_authority_matrix.schema.json").read_text(encoding="utf-8"))

    errors = sorted(Draft202012Validator(schema).iter_errors(matrix), key=lambda error: error.path)

    assert errors == [], [error.message for error in errors]


def test_generated_approval_card_carries_constitutional_receipt_fields(tmp_path: Path) -> None:
    approval = {
        "approval_id": "APR-LEVEL6-001",
        "case_id": "EXP-LEVEL6-001",
        "workflow_type": "EXPORT",
        "proposed_action": "send_buyer_introductory_outreach",
        "approval_status": "PENDING",
        "requested_at": "2026-07-12T06:00:00+00:00",
    }
    case = {
        "case_id": "EXP-LEVEL6-001",
        "workflow_type": "EXPORT",
        "buyer_name": "Example Buyer",
    }
    card = structured_card(approval, case, tmp_path / "card.html", tmp_path / "card.json")
    schema = json.loads((PROJECT_ROOT / "config" / "schemas" / "approval_card.schema.json").read_text(encoding="utf-8"))

    errors = sorted(Draft202012Validator(schema).iter_errors(card), key=lambda error: error.path)

    assert errors == [], [error.message for error in errors]
    assert card["authority_class"] == "external_message"
    assert card["external_actions_executed"] is False
    assert card["approval_boundary"] == "owner_decision_required_before_external_action"


def test_authority_matrix_cli_report_is_json_serializable() -> None:
    matrix = load_yaml(PROJECT_ROOT / "config" / "agent_authority_matrix.yaml")
    tool_policy = load_yaml(PROJECT_ROOT / "config" / "tender_tool_policy.yaml")
    approval_policy = load_yaml(PROJECT_ROOT / "config" / "approval_policy.yaml")
    profiles = load_yaml(PROJECT_ROOT / "config" / "hermes_specialist_profiles.yaml")

    report = {
        "status": "PASS" if not validate_authority_matrix(matrix, tool_policy, approval_policy, profiles) else "FAIL",
        "external_actions_executed": False,
    }

    assert json.loads(json.dumps(report))["external_actions_executed"] is False
