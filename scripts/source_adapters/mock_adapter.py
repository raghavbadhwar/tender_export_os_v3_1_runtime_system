"""Fixture-backed source adapter used for safe tests."""

from __future__ import annotations

import json
from pathlib import Path

from base import SourceOpportunity


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "sources" / "mock_opportunities.json"


class MockSourceAdapter:
    name = "mock"

    def __init__(self, fixture: Path = DEFAULT_FIXTURE) -> None:
        self.fixture = fixture

    def scan(self) -> list[SourceOpportunity]:
        rows = json.loads(self.fixture.read_text(encoding="utf-8"))
        return [SourceOpportunity(**row) for row in rows]
