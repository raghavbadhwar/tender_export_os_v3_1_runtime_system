"""Safe source adapter contract for Tender Export OS."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol


@dataclass
class SourceOpportunity:
    source_name: str
    source_type: str
    workflow_type: str
    source_url: str
    external_reference: str
    opportunity_title: str
    buyer_name: str = ""
    product_or_service: str = ""
    quantity: str = ""
    unit: str = ""
    deadline_date: str = ""
    estimated_value_inr: str = ""
    estimated_value_usd: str = ""
    blocker_status: str = ""
    citations: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class SourceAdapter(Protocol):
    name: str

    def scan(self) -> list[SourceOpportunity]:
        """Return structured opportunities without deep-reading every lead."""


class SourceBlocked(RuntimeError):
    """Raised when a source is paywalled, login-required, CAPTCHA-blocked, or restricted."""
