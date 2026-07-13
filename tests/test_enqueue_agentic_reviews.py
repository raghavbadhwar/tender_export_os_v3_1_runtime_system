from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.enqueue_agentic_reviews import enqueue_exceptions, enqueue_morning_review, enqueue_weekly_learning, hermes_command, latest_existing, run_cards


def test_enqueuer_skips_missing_packets(tmp_path: Path) -> None:
    assert enqueue_morning_review(tmp_path / "missing.json") is None


def test_enqueuer_creates_idempotent_cards_without_model_or_external_action(tmp_path: Path) -> None:
    packet = tmp_path / "weekly.json"
    packet.write_text("{}", encoding="utf-8")

    card = enqueue_weekly_learning(packet)
    assert card is not None
    assert card["assignee"] == "learning-evaluation"
    assert card["external_actions_allowed"] is False
    assert card["model_runs_executed_by_enqueuer"] is False
    assert card["idempotency_key"].startswith("agentic-review:weekly_learning:")
    command = hermes_command(card)
    assert "--idempotency-key" in command
    assert "--body" in command
    assert "--status" not in command
    assert command[command.index("--priority") + 1] == "50"


def test_run_cards_is_dry_run_by_default(tmp_path: Path) -> None:
    packet = tmp_path / "exception.json"
    packet.write_text("{}", encoding="utf-8")
    cards = [enqueue_exceptions(packet)]
    cards = [card for card in cards if card]

    result = run_cards(cards, write=False)

    assert result["kanban_mutated"] is False
    assert result["card_count"] == 1
    assert result["model_runs_executed"] is False


def test_exception_review_routes_to_packet_capable_chief_operator(tmp_path: Path) -> None:
    packet = tmp_path / "exception.json"
    packet.write_text("{}", encoding="utf-8")

    card = enqueue_exceptions(packet)

    assert card is not None
    assert card["assignee"] == "tender-export-os"


def test_run_cards_reports_kanban_failure_truthfully(tmp_path: Path) -> None:
    packet = tmp_path / "morning.json"
    packet.write_text("{}", encoding="utf-8")
    card = enqueue_morning_review(packet)
    assert card is not None

    def failing_runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="invalid arguments")

    result = run_cards([card], write=True, runner=failing_runner)

    assert result["status"] == "FAIL"
    assert result["failure_count"] == 1
    assert result["kanban_mutated"] is False


def test_latest_existing_selects_newest_packet(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "outputs"
    out.mkdir()
    older = out / "packet_1.json"
    newer = out / "packet_2.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")

    selected = latest_existing("outputs/packet_*.json")

    assert selected == newer
