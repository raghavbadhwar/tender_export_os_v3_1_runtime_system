from __future__ import annotations

import datetime as dt

from scripts.check_corrigenda import detect_corrigenda
from scripts.retender_corrigenda_watch import build_change_actions, build_report


def test_corrigendum_detects_evidenced_deadline_change() -> None:
    result = detect_corrigenda(
        "GOV-1",
        "",
        [
            {
                "title": "Corrigendum: bid date extended",
                "url": "https://example.test/corrigendum/1",
                "previous_deadline": "2099-01-10",
                "new_deadline": "2099-01-20",
            }
        ],
    )

    assert result["changed"] is True
    assert result["deadline_change"] == {
        "previous_deadline": "2099-01-10",
        "new_deadline": "2099-01-20",
    }


def test_daily_report_and_actions_are_deterministic_and_idempotent() -> None:
    match = {
        "old_case_id": "GOV-1",
        "new_possible_case_or_source_url": "https://example.test/tender/1",
        "old_deadline": "2099-01-10",
        "new_deadline": "2099-01-20",
        "change_type": "DATE_EXTENSION",
        "matched_keywords": ["date extension"],
    }
    as_of = dt.date(2099, 1, 5)

    first_report = build_report([match], 1, as_of=as_of)
    second_report = build_report([match], 1, as_of=as_of)
    first = build_change_actions([match], report_path="outputs/report.json")
    second = build_change_actions([match], report_path="outputs/report.json")

    assert first_report["run_id"] == second_report["run_id"] == "RUN-20990105-RETENDER-CORRIGENDA"
    assert first == second
    assert len(first) == 1
    action = first[0]
    assert action["event"]["event_type"] == "tender.deadline_changed"
    assert action["event"]["payload"]["previous_deadline"] == "2099-01-10"
    assert action["event"]["payload"]["new_deadline"] == "2099-01-20"
    assert action["task"]["assignee"] == "gov-tender-intelligence"
    assert action["task"]["idempotency_key"].startswith("teos:GOV-1:document-diff:")
    assert {"deep_read", "supplier", "pricing", "compliance", "artifacts"} <= set(action["invalidate_stages"])


def test_change_without_old_and_new_deadline_creates_diff_task_but_no_deadline_event() -> None:
    actions = build_change_actions(
        [
            {
                "old_case_id": "GOV-2",
                "new_possible_case_or_source_url": "https://example.test/tender/2",
                "old_deadline": "",
                "new_deadline": "",
                "change_type": "REVISED_BOQ",
                "matched_keywords": ["revised boq"],
            }
        ],
        report_path="outputs/report.json",
    )

    assert actions[0]["event"] is None
    assert actions[0]["task"]["assignee"] == "gov-tender-intelligence"
    assert actions[0]["task"]["external_effect"] is False
