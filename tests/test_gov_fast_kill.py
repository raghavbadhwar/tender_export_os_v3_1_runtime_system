from __future__ import annotations

import json
from pathlib import Path

from scripts.gov_fast_kill import build_critic_handoff, evaluate_gov_fast_kill, write_decision


def evidence(*fields: str) -> dict[str, list[dict[str, str | int]]]:
    return {
        field: [
            {
                "source_path": "outputs/evidence/private/GOV-1/tender.pdf",
                "page": 1,
                "section": "fixture",
            }
        ]
        for field in fields
    }


def test_missing_governance_evidence_becomes_watchlist_not_hard_rejection() -> None:
    result = evaluate_gov_fast_kill({"case_id": "GOV-1", "workflow_type": "GOV"}, {})

    assert result["decision"] == "WATCHLIST"
    assert result["hard_rejection_proven"] is False
    assert result["stage2_critic_required"] is True
    assert result["missing_evidence"]


def test_cited_hard_kill_rejects_but_uncited_hard_kill_stays_watchlist() -> None:
    case = {"case_id": "GOV-2", "workflow_type": "GOV", "days_to_deadline": "2", "estimated_value_inr": "100000"}

    uncited = evaluate_gov_fast_kill(case, {})
    cited = evaluate_gov_fast_kill(case, evidence("days_to_deadline"))

    assert uncited["decision"] == "WATCHLIST"
    assert "GOV-KILL-01" in uncited["unproven_hard_rules"]
    assert cited["decision"] == "REJECTED"
    assert cited["hard_rejection_proven"] is True
    assert cited["stage2_critic_required"] is False


def test_high_value_hard_kill_requires_critic_exception_review_even_when_cited() -> None:
    result = evaluate_gov_fast_kill(
        {
            "case_id": "GOV-3",
            "workflow_type": "GOV",
            "days_to_deadline": "2",
            "estimated_value_inr": "6000000",
        },
        evidence("days_to_deadline"),
    )

    assert result["decision"] == "WATCHLIST"
    assert result["stage2_critic_required"] is True
    assert "high_value_exception" in result["review_reasons"]
    handoff = build_critic_handoff(result)
    assert handoff["next_profile"] == "gov-tender-intelligence"
    assert handoff["approval_required"] is False


def test_fast_kill_write_is_event_backed_but_does_not_mutate_case_register(tmp_path: Path) -> None:
    decision = evaluate_gov_fast_kill(
        {"case_id": "GOV-4", "workflow_type": "GOV", "days_to_deadline": "2", "estimated_value_inr": "100000"},
        evidence("days_to_deadline"),
    )
    events = tmp_path / "events.jsonl"

    result = write_decision(decision, output_dir=tmp_path, events_path=events, actor="pytest")

    assert result["report_path"].is_file()
    event = json.loads(events.read_text(encoding="utf-8").strip())
    assert event["event_type"] == "case.fast_kill_completed"
    assert event["payload"]["decision"] == "REJECTED"
