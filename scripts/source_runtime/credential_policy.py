"""Credential and secret-safety helpers for source runtime outputs."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

SECRET_KEY_PATTERN = re.compile(r"(password|passwd|secret|token|api[_-]?key|cookie|otp|mfa|session)", re.I)
SECRET_VALUE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.I),
    re.compile(r"(?:password|otp|token)\s*[:=]\s*\S+", re.I),
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern in SECRET_VALUE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def sanitize_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            if SECRET_KEY_PATTERN.search(str(key)):
                clean[str(key)] = "[REDACTED]"
            else:
                clean[str(key)] = sanitize_payload(item)
        return clean
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [sanitize_payload(item) for item in value]
    return value


def assert_no_secret_values(value: Any) -> None:
    serialized = str(sanitize_payload(value))
    if any(pattern.search(serialized) for pattern in SECRET_VALUE_PATTERNS):
        raise ValueError("Secret-like value detected in source runtime output")
