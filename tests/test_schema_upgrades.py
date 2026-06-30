import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_schema(name: str) -> dict:
    return json.loads((PROJECT_ROOT / "config" / "schemas" / name).read_text(encoding="utf-8"))


def test_master_case_schema_has_evidence_and_execution_fields() -> None:
    schema = load_schema("master_cases.schema.json")
    required = set(schema["required_columns"])
    assert {"evidence_level", "execution_sub_status"}.issubset(required)
    assert "BLOCKED_CAPTCHA" in schema["enums"]["evidence_level"]
    assert "PAYMENT_RECEIVED" in schema["enums"]["execution_sub_status"]


def test_quote_schema_blocks_indicative_selected_pricing() -> None:
    schema = load_schema("quote_master.schema.json")
    rules = {rule["rule"]: rule for rule in schema["cross_field_rules"]}
    assert "selected_for_pricing_not_indicative" in rules
    assert "indicative_price_only" in schema["required_columns"]


def test_live_projection_headers_include_mandate_columns() -> None:
    with (PROJECT_ROOT / "data" / "master_cases.csv").open(newline="", encoding="utf-8") as f:
        headers = next(csv.reader(f))
    assert "emd_opportunity_cost" in headers
    assert "buyer_repeat_score" in headers


def test_event_schema_includes_current_runtime_events() -> None:
    schema = load_schema("event.schema.json")
    assert "source_adapter.scan_started" in schema["event_types"]
    assert "pricing.draft_created" in schema["event_types"]
    assert "pricing_draft" in schema["object_types"]
