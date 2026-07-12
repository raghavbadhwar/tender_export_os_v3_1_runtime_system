from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.search_recovered_ares_context import search_archive


def build_archive(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            model TEXT,
            title TEXT
        );
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            timestamp REAL NOT NULL
        );
        """
    )
    connection.execute(
        "INSERT INTO sessions(id, source, model, title) VALUES (?, ?, ?, ?)",
        ("tender-session", "telegram", "gpt-test", "Tender owner brief"),
    )
    connection.execute(
        "INSERT INTO sessions(id, source, model, title) VALUES (?, ?, ?, ?)",
        ("fitness-session", "cron", "gpt-test", "Meal plan"),
    )
    connection.execute(
        "INSERT INTO sessions(id, source, model, title) VALUES (?, ?, ?, ?)",
        ("demo-session", "dashboard", "gpt-test", "Demo Wholesale"),
    )
    connection.executemany(
        "INSERT INTO messages(session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        [
            ("tender-session", "assistant", "Tender owner brief is ready", 10.0),
            ("tender-session", "user", "Show the approval status", 11.0),
            ("tender-session", "tool", "token=super-secret-tool-value", 12.0),
            ("fitness-session", "assistant", "Approval for tomorrow's meal plan", 13.0),
            ("demo-session", "assistant", "Demo-wholesaler RFQ owner brief", 14.0),
        ],
    )
    connection.commit()
    connection.close()


def test_tender_scope_uses_session_context_and_excludes_tool_messages(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    build_archive(db)

    payload = search_archive(db, "approval", scope="tender")

    assert payload["match_count"] == 1
    assert payload["results"][0]["session_id"] == "tender-session"
    assert payload["results"][0]["role"] == "user"


def test_all_scope_can_find_unrelated_legacy_context(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    build_archive(db)

    payload = search_archive(db, "meal", scope="all")

    assert payload["match_count"] == 1
    assert payload["results"][0]["session_id"] == "fitness-session"


def test_tender_scope_excludes_demo_wholesaler_sessions(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    build_archive(db)

    payload = search_archive(db, "owner brief", scope="tender")

    assert payload["match_count"] == 1
    assert {item["session_id"] for item in payload["results"]} == {"tender-session"}


def test_tool_messages_require_explicit_opt_in_and_are_redacted(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    build_archive(db)

    hidden = search_archive(db, "super-secret", scope="all")
    shown = search_archive(db, "super-secret", scope="all", include_tools=True)

    assert hidden["match_count"] == 0
    assert shown["match_count"] == 1
    assert "super-secret-tool-value" not in shown["results"][0]["snippet"]
    assert "<redacted>" in shown["results"][0]["snippet"]
