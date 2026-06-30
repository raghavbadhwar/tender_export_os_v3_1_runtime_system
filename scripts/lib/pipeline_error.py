"""Structured pipeline error records for safe regressions and agent runs."""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PipelineError:
    code: str
    stage: str
    message: str
    recoverable: bool = True
    safe_status: str = "BLOCKED"
    created_at: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def blocked_error(stage: str, message: str, code: str = "PIPELINE_BLOCKED") -> dict[str, Any]:
    return PipelineError(code=code, stage=stage, message=message).to_dict()
