#!/usr/bin/env python3
"""Search the preserved Ares/Hermes v0.14 session archive safely.

The legacy database is deliberately kept separate from the live Hermes profile.
This reader opens it in immutable, read-only mode, returns only bounded snippets,
and excludes tool messages unless the operator opts in explicitly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote


DEFAULT_ARCHIVE_DB = (
    Path.home()
    / ".hermes"
    / "profiles"
    / "tender-export-os"
    / "recovered-context"
    / "ares-v014"
    / "state.db"
)
LEGACY_DB_FALLBACK = Path.home() / ".ares" / "state.db"

TENDER_SCOPE_TERMS = (
    "tender",
    "rfq",
    "buyer",
    "procurement",
    "cppp",
    "ungm",
    "export quote",
    "export rfq",
    "owner brief",
)
TENDER_SCOPE_EXCLUSIONS = (
    "demo-wholesaler",
    "demo wholesale",
    "mock gstr",
)

SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]{16,}"),
    re.compile(
        r"(?i)\b(api[_ -]?key|token|password|secret)\s*[:=]\s*"
        r"['\"]?[A-Za-z0-9._~+/=-]{8,}"
    ),
)


def _default_db() -> Path:
    return DEFAULT_ARCHIVE_DB if DEFAULT_ARCHIVE_DB.exists() else LEGACY_DB_FALLBACK


def _readonly_connection(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{quote(str(db_path.resolve()), safe='/')}?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _validate_schema(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('sessions', 'messages')"
    ).fetchall()
    names = {row["name"] for row in rows}
    if names != {"sessions", "messages"}:
        raise ValueError("Archive does not contain the expected Hermes sessions/messages schema")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        if pattern.pattern.lower().startswith("(?i)\\b(bearer"):
            redacted = pattern.sub(r"\1<redacted>", redacted)
        else:
            redacted = pattern.sub("<redacted>", redacted)
    return redacted


def _snippet(content: str, max_chars: int) -> str:
    normalized = re.sub(r"\s+", " ", content or "").strip()
    normalized = _redact(normalized)
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1].rstrip() + "…"


def _iso_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()


def _eligible_session_ids(connection: sqlite3.Connection, scope: str) -> set[str] | None:
    if scope == "all":
        return None
    clauses = " OR ".join("lower(coalesce(content, '')) LIKE ?" for _ in TENDER_SCOPE_TERMS)
    params = [f"%{term}%" for term in TENDER_SCOPE_TERMS]
    rows = connection.execute(
        f"SELECT DISTINCT session_id FROM messages WHERE {clauses}",  # noqa: S608
        params,
    ).fetchall()
    candidates = {row["session_id"] for row in rows}
    if not candidates:
        return candidates
    exclusion_clauses = " OR ".join(
        "lower(coalesce(content, '')) LIKE ?" for _ in TENDER_SCOPE_EXCLUSIONS
    )
    excluded_rows = connection.execute(
        f"SELECT DISTINCT session_id FROM messages WHERE {exclusion_clauses}",  # noqa: S608
        [f"%{term}%" for term in TENDER_SCOPE_EXCLUSIONS],
    ).fetchall()
    excluded = {row["session_id"] for row in excluded_rows}
    return candidates - excluded


def search_archive(
    db_path: Path,
    query: str,
    *,
    scope: str = "tender",
    limit: int = 20,
    max_chars: int = 800,
    include_tools: bool = False,
) -> dict[str, Any]:
    if not db_path.is_file():
        raise FileNotFoundError(f"Recovered Hermes archive not found: {db_path}")
    terms = [term.lower() for term in re.findall(r"[\w.-]+", query, flags=re.UNICODE)]
    if not terms:
        raise ValueError("Query must contain at least one searchable word")

    roles = ("user", "assistant", "tool") if include_tools else ("user", "assistant")
    with _readonly_connection(db_path) as connection:
        _validate_schema(connection)
        eligible = _eligible_session_ids(connection, scope)
        where = [f"m.role IN ({','.join('?' for _ in roles)})"]
        params: list[Any] = list(roles)
        for term in terms:
            where.append("lower(coalesce(m.content, '')) LIKE ?")
            params.append(f"%{term}%")
        if eligible is not None:
            if not eligible:
                rows: list[sqlite3.Row] = []
            else:
                where.append(f"m.session_id IN ({','.join('?' for _ in eligible)})")
                params.extend(sorted(eligible))
                params.append(limit)
                rows = connection.execute(
                    "SELECT m.session_id, m.role, m.content, m.timestamp, "
                    "s.source, s.model, s.title "
                    "FROM messages AS m JOIN sessions AS s ON s.id = m.session_id "
                    f"WHERE {' AND '.join(where)} "  # noqa: S608
                    "ORDER BY m.timestamp DESC LIMIT ?",
                    params,
                ).fetchall()
        else:
            params.append(limit)
            rows = connection.execute(
                "SELECT m.session_id, m.role, m.content, m.timestamp, "
                "s.source, s.model, s.title "
                "FROM messages AS m JOIN sessions AS s ON s.id = m.session_id "
                f"WHERE {' AND '.join(where)} "  # noqa: S608
                "ORDER BY m.timestamp DESC LIMIT ?",
                params,
            ).fetchall()

    results = [
        {
            "session_id": row["session_id"],
            "timestamp_utc": _iso_timestamp(row["timestamp"]),
            "role": row["role"],
            "source": row["source"],
            "model": row["model"],
            "title": row["title"] or "",
            "snippet": _snippet(row["content"] or "", max_chars),
        }
        for row in rows
    ]
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_db": str(db_path.resolve()),
        "archive_sha256": _sha256(db_path),
        "scope": scope,
        "query": query,
        "include_tool_messages": include_tools,
        "match_count": len(results),
        "results": results,
    }


def _render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"Recovered Ares context: {payload['match_count']} match(es)",
        f"Archive: {payload['archive_db']}",
        f"Scope: {payload['scope']} | Query: {payload['query']}",
    ]
    for item in payload["results"]:
        title = f" | {item['title']}" if item["title"] else ""
        lines.extend(
            [
                "",
                f"[{item['timestamp_utc']}] {item['session_id']} | {item['role']} | {item['source']}{title}",
                item["snippet"],
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search the preserved Ares/Hermes v0.14 session archive"
    )
    parser.add_argument("--query", required=True, help="Case-insensitive words to require")
    parser.add_argument("--db", type=Path, default=_default_db(), help="Recovered state.db path")
    parser.add_argument("--scope", choices=("tender", "all"), default="tender")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--max-chars", type=int, default=800)
    parser.add_argument(
        "--include-tool-messages",
        action="store_true",
        help="Include legacy tool outputs; off by default to reduce secret/raw-data exposure",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = search_archive(
            args.db,
            args.query,
            scope=args.scope,
            limit=max(1, min(args.limit, 100)),
            max_chars=max(80, min(args.max_chars, 4000)),
            include_tools=args.include_tool_messages,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2

    if args.format == "text":
        print(_render_text(payload))
    else:
        print(json.dumps({"ok": True, **payload}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
