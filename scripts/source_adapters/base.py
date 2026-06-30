"""Safe source adapter contracts for Tender Export OS."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


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


@dataclass
class SourceDocument:
    document_id: str
    document_type: str
    document_name: str
    source_url: str
    local_path: str
    sha256: str
    downloaded_at: str
    parse_status: str = ""
    page_count: int | None = None
    extracted_text_path: str = ""
    extraction_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeepExtractedFields:
    buyer_department: str = ""
    buyer_organisation: str = ""
    ministry_or_parent_body: str = ""
    tender_id: str = ""
    bid_number: str = ""
    title: str = ""
    workflow_type: str = ""
    source_portal: str = ""
    source_url: str = ""
    state: str = ""
    city: str = ""
    delivery_location: str = ""
    product_or_service: str = ""
    category: str = ""
    tender_value_inr: str = ""
    emd_amount_inr: str = ""
    tender_fee_inr: str = ""
    bid_start_date: str = ""
    bid_end_date: str = ""
    opening_date: str = ""
    pre_bid_meeting_date: str = ""
    clarification_deadline: str = ""
    contract_period: str = ""
    delivery_period: str = ""
    payment_terms: str = ""
    turnover_requirement: str = ""
    past_experience_requirement: str = ""
    certification_requirement: str = ""
    oem_authorization_required: str = ""
    msme_exemption: str = ""
    startup_exemption: str = ""
    make_in_india_requirement: str = ""
    local_content_requirement: str = ""
    documents_required: list[str] = field(default_factory=list)
    boq_items: list[dict] = field(default_factory=list)
    important_clauses: list[dict] = field(default_factory=list)
    field_evidence: dict[str, dict[str, Any]] = field(default_factory=dict)
    risk_flags: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    confidence_score: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeepSourceOpportunity:
    shallow: SourceOpportunity
    extracted: DeepExtractedFields
    documents: list[SourceDocument] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    raw_html_paths: list[str] = field(default_factory=list)
    evidence_dir: str = ""
    extraction_status: str = ""
    blocker_status: str = ""
    citations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceAdapter(Protocol):
    name: str

    def scan(self) -> list[SourceOpportunity]:
        """Return structured opportunities without deep-reading every lead."""


class DeepSourceAdapter(Protocol):
    name: str

    def scan(self) -> list[SourceOpportunity]:
        """Return listing-level opportunities."""

    def deep_read(self, opportunity: SourceOpportunity) -> DeepSourceOpportunity:
        """Open detail pages, download docs, parse evidence, and extract deep fields."""


class SourceBlocked(RuntimeError):
    """Raised when a source is paywalled, login-required, CAPTCHA-blocked, or restricted."""

    def __init__(self, source: str, reason: str, human_action_required: bool = True, details: str = "") -> None:
        self.source = source
        self.reason = reason
        self.human_action_required = human_action_required
        self.details = details
        message = f"{source} blocked: {reason}"
        if details:
            message = f"{message} ({details})"
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "reason": self.reason,
            "human_action_required": self.human_action_required,
            "details": self.details,
        }
