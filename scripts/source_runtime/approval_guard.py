"""Approval and unsafe-action guardrails for source adapters."""

from __future__ import annotations

import re

from .exceptions import UnsafePortalAction

UNSAFE_ACTION_PATTERNS = [
    r"\bsubmit\b",
    r"\bupload\b",
    r"\bpay(?:ment)?\b",
    r"\bDSC\b",
    r"digital\s*signature",
    r"accept\s+(?:terms|declaration)",
    r"place\s+bid",
    r"send\s+quote",
    r"confirm\s+(?:price|delivery|origin)",
]


def assert_no_external_side_effect(action_label: str) -> None:
    for pattern in UNSAFE_ACTION_PATTERNS:
        if re.search(pattern, action_label, flags=re.I):
            raise UnsafePortalAction(f"Unsafe portal action requires owner approval: {action_label}")
