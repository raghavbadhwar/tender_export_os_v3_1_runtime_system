"""Detect forbidden browser actions in portal pages."""

from __future__ import annotations

import re
from typing import Any

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

FORBIDDEN_ACTION_RE = re.compile(
    r"\b("
    r"submit\s+bid|final\s+submit|upload\s+bid|upload\s+document|"
    r"pay|payment|dsc|digital\s+signature|accept\s+declaration|"
    r"place\s+order|send\s+quote|send\s+message"
    r")\b",
    re.I,
)


def detect_forbidden_actions(html: str) -> list[dict[str, Any]]:
    if BeautifulSoup is None:
        match = FORBIDDEN_ACTION_RE.search(html or "")
        return [{"tag": "unknown", "label": match.group(0)[:160]}] if match else []
    soup = BeautifulSoup(html or "", "html.parser")
    elements = soup.find_all(["button", "a", "input", "textarea", "select"])
    hits: list[dict[str, Any]] = []
    for element in elements:
        label = " ".join(
            [
                str(element.get("value") or ""),
                str(element.get("aria-label") or ""),
                str(element.get("title") or ""),
                element.get_text(" ", strip=True),
            ]
        ).strip()
        if not label:
            continue
        if FORBIDDEN_ACTION_RE.search(label):
            hits.append({"tag": element.name, "label": " ".join(label.split())[:160]})
    return hits


def assert_no_forbidden_action(html: str) -> None:
    hits = detect_forbidden_actions(html)
    if hits:
        labels = ", ".join(item["label"] for item in hits)
        raise ValueError(f"Forbidden browser action element present: {labels}")
