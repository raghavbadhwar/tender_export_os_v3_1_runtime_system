from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from scripts.persist_hermes_insights_summary import parse_insights, write_summary


def _fixture() -> str:
    return """Period: Jul 11, 2026 — Jul 14, 2026

📋 Overview
Sessions:          53            Messages:        679
Tool calls:        407           User messages:   59
Input tokens:      1,657,897     Output tokens:   110,983
Total tokens:      15,508,400

🤖 Models Used
Model                          Sessions       Tokens
  gpt-5.6-terra                        48   14,353,471
  gpt-5.5                               5    1,154,929

🔧 Top Tools
Tool                            Calls        %
  read_file                         135    33.2%
  mcp__tender_os__get_case           14     3.4%

🧠 Top Skills
Skill                          Loads   Edits   Last used
  teos-chief-operator                8       0      Jul 14
  teos-evidence-verifier             7       0      Jul 13
📅 Activity Patterns
"""


def test_parse_insights_keeps_only_aggregate_metrics() -> None:
    summary = parse_insights(_fixture(), profile="tender-export-os", generated_at="2026-07-14T00:00:00+00:00")

    assert summary["schema_version"] == "hermes_insights_summary.v1"
    assert summary["metrics"]["sessions"] == 53
    assert summary["metrics"]["tool_calls"] == 407
    assert summary["metrics"]["models"][0]["name"] == "gpt-5.6-terra"
    assert summary["metrics"]["tools"][0]["name"] == "read_file"
    assert summary["metrics"]["skills"][0]["name"] == "teos-chief-operator"
    assert summary["raw_output_persisted"] is False
    assert "Overview" not in json.dumps(summary)


def test_write_summary_matches_schema(tmp_path: Path) -> None:
    summary = parse_insights(_fixture(), profile="tender-export-os", generated_at="2026-07-14T00:00:00+00:00")
    path = write_summary(summary, tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(Path("config/schemas/hermes_insights_summary.schema.json").read_text(encoding="utf-8"))

    jsonschema.Draft202012Validator(schema).validate(payload)
    assert payload["raw_output_persisted"] is False
