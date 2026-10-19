from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.enqueue_agentic_reviews import (
    CREATED_BY,
    TENANT,
    comment_command,
    enqueue_exceptions,
    enqueue_morning_review,
    enqueue_weekly_learning,
    hermes_command,
    latest_existing,
    matching_unresolved_task,
    packet_update_already_attached,
    run_cards,
)


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
    assert len(card["packet_sha256"]) == 64
    assert card["route_via"] == "teos-orchestrator"
    assert card["max_in_progress_per_profile"] == 1
    command = hermes_command(card)
    assert "--idempotency-key" in command
    assert "--body" in command
    assert "--status" not in command
    assert command[command.index("--priority") + 1] == "50"


def test_run_cards_is_dry_run_by_default(tmp_path: Path) -> None:
    packet = tmp_path / "exception.json"
    packet.write_text('{"trigger_type":"failed_job"}', encoding="utf-8")
    cards = [enqueue_exceptions(packet)]
    cards = [card for card in cards if card]

    result = run_cards(cards, write=False)

    assert result["kanban_mutated"] is False
    assert result["card_count"] == 1
    assert result["model_runs_executed"] is False
    assert result["outcome_counts"]["skipped"] == 1


def test_exception_review_routes_to_packet_capable_chief_operator(tmp_path: Path) -> None:
    packet = tmp_path / "exception.json"
    packet.write_text('{"trigger_type":"deadline"}', encoding="utf-8")

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
    assert result["outcome_counts"]["failed"] == 1


def test_exception_review_rejects_unproven_packet(tmp_path: Path) -> None:
    packet = tmp_path / "exception.json"
    packet.write_text("{}", encoding="utf-8")

    assert enqueue_exceptions(packet) is None


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


def test_matching_unresolved_task_uses_review_stream_not_packet_path(tmp_path: Path) -> None:
    packet = tmp_path / "morning-new.json"
    packet.write_text("{}", encoding="utf-8")
    card = enqueue_morning_review(packet)
    assert card is not None
    tasks = [
        {
            "id": "t_old",
            "title": card["title"],
            "body": "TEOS_AGENTIC_REVIEW_V1\nKind: morning_review\nPacket: old.json",
            "tenant": TENANT,
            "created_by": CREATED_BY,
            "status": "blocked",
            "created_at": 1,
        }
    ]

    assert matching_unresolved_task(card, tasks) == tasks[0]


def test_run_cards_reuses_unresolved_stream_and_adds_bounded_comment(tmp_path: Path) -> None:
    packet = tmp_path / "morning-new.json"
    packet.write_text("{}", encoding="utf-8")
    card = enqueue_morning_review(packet)
    assert card is not None
    calls: list[list[str]] = []

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "list" in command:
            stdout = (
                '[{"id":"t_existing","title":"Morning Chief Operator Review",'
                '"body":"TEOS_AGENTIC_REVIEW_V1\\nKind: morning_review\\nPacket: old.json",'
                '"tenant":"agentic-review","created_by":"enqueue_agentic_reviews",'
                '"status":"blocked","created_at":1}]'
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
        if "show" in command:
            return subprocess.CompletedProcess(command, 0, stdout='{"comments":[]}', stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = run_cards([card], write=True, runner=runner)

    assert result["status"] == "PASS"
    assert result["outcome_counts"]["created"] == 0
    assert result["outcome_counts"]["reused"] == 1
    assert result["outcome_counts"]["commented"] == 1
    assert result["results"][0]["task_id"] == "t_existing"
    assert "show" in calls[1]
    assert "comment" in calls[2]
    assert calls[2] == comment_command(card, "t_existing")


def test_run_cards_creates_new_cycle_after_prior_task_is_done(tmp_path: Path) -> None:
    packet = tmp_path / "weekly.json"
    packet.write_text("{}", encoding="utf-8")
    card = enqueue_weekly_learning(packet)
    assert card is not None
    calls: list[list[str]] = []

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if "list" in command:
            stdout = (
                '[{"id":"t_done","title":"Weekly Learning Council",'
                '"body":"TEOS_AGENTIC_REVIEW_V1\\nKind: weekly_learning\\nPacket: weekly.json",'
                '"tenant":"agentic-review","created_by":"enqueue_agentic_reviews",'
                '"status":"done","created_at":1}]'
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
        return subprocess.CompletedProcess(command, 0, stdout='{"id":"t_new"}', stderr="")

    result = run_cards([card], write=True, runner=runner)

    assert result["outcome_counts"]["created"] == 1
    assert result["results"][0]["task_id"] == "t_new"
    assert "create" in calls[1]


def test_repeated_identical_packet_reuses_without_duplicate_comment(tmp_path: Path) -> None:
    packet = tmp_path / "morning.json"
    packet.write_text("{}", encoding="utf-8")
    card = enqueue_morning_review(packet)
    assert card is not None
    comment = (
        '{"schema":"TEOS_AGENTIC_REVIEW_UPDATE_V1",'
        f'"packet_path":"{card["packet_path"]}",'
        f'"packet_sha256":"{card["packet_sha256"]}"'
        "}"
    )
    assert packet_update_already_attached(card, {"comments": [{"body": comment}]})

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "list" in command:
            stdout = (
                '[{"id":"t_existing","title":"Morning Chief Operator Review",'
                '"body":"TEOS_AGENTIC_REVIEW_V1\\nKind: morning_review\\nPacket: old.json",'
                '"tenant":"agentic-review","created_by":"enqueue_agentic_reviews",'
                '"status":"blocked","created_at":1}]'
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
        if "show" in command:
            return subprocess.CompletedProcess(command, 0, stdout='{"comments":[{"body":' + repr(comment).replace("'", '"') + "}]} ", stderr="")
        raise AssertionError(f"unexpected mutation command: {command}")

    # Build valid show JSON without relying on shell/string escaping.
    def valid_runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "show" in command:
            import json

            return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"comments": [{"body": comment}]}), stderr="")
        return runner(command, **kwargs)

    result = run_cards([card], write=True, runner=valid_runner)

    assert result["outcome_counts"]["reused"] == 1
    assert result["outcome_counts"]["commented"] == 0
    assert result["kanban_mutated"] is False
