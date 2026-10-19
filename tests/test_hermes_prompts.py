from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_morning_chief_operator_prompt_preserves_approval_and_evidence_gates() -> None:
    text = (ROOT / "prompts/hermes/morning_chief_operator.md").read_text(encoding="utf-8")

    assert "Top three evidenced opportunities" in text
    assert "One primary owner action" in text
    assert "do not infer readiness" in text
    assert "Do not browse, send, submit" in text


def test_intraday_exception_officer_prompt_is_trigger_bounded() -> None:
    text = (ROOT / "prompts/hermes/intraday_exception_officer.md").read_text(encoding="utf-8")

    assert "Wake only" in text
    assert "deadline threshold" in text
    assert "quote contradiction" in text
    assert "NO_ACTION_UNPROVEN" in text
