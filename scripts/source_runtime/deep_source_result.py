"""Serialization helpers for deep source results."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def to_plain_dict(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [to_plain_dict(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_plain_dict(item) for key, item in value.items()}
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_plain_dict(value), indent=2, ensure_ascii=False), encoding="utf-8")
