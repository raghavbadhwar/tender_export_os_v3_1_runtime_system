"""Opportunity deduplication for deep source results."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

try:
    from scripts.source_adapters.base import DeepSourceOpportunity, SourceOpportunity
except ModuleNotFoundError:  # pragma: no cover
    from source_adapters.base import DeepSourceOpportunity, SourceOpportunity  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = PROJECT_ROOT / "data" / "master_cases.csv"


def stable_hash(parts: list[str]) -> str:
    value = "|".join(part.strip().lower() for part in parts if part)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def opportunity_fingerprints(opportunity: SourceOpportunity) -> set[str]:
    fingerprints = set()
    for value in [opportunity.external_reference, opportunity.source_url]:
        if value:
            fingerprints.add(stable_hash([value]))
    if opportunity.opportunity_title or opportunity.buyer_name or opportunity.deadline_date:
        fingerprints.add(stable_hash([opportunity.opportunity_title, opportunity.buyer_name, opportunity.deadline_date]))
    return fingerprints


class DedupeEngine:
    def __init__(self, case_register: Path = DEFAULT_CASES) -> None:
        self.case_register = case_register
        self.existing: dict[str, str] = {}
        self._load_cases()

    def _load_cases(self) -> None:
        if not self.case_register.exists():
            return
        with self.case_register.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                case_id = row.get("case_id", "")
                if not case_id:
                    continue
                opportunity = SourceOpportunity(
                    source_name=row.get("source_name", ""),
                    source_type="",
                    workflow_type=row.get("workflow_type", ""),
                    source_url=row.get("source_url", ""),
                    external_reference=row.get("case_id", ""),
                    opportunity_title=row.get("opportunity_title", ""),
                    buyer_name=row.get("buyer_name", ""),
                    product_or_service=row.get("product_or_service", ""),
                    deadline_date=row.get("deadline_date", ""),
                )
                for fingerprint in opportunity_fingerprints(opportunity):
                    self.existing[fingerprint] = case_id

    def find_duplicate(self, result: DeepSourceOpportunity | SourceOpportunity) -> str:
        opportunity = result.shallow if hasattr(result, "shallow") else result
        for fingerprint in opportunity_fingerprints(opportunity):
            if fingerprint in self.existing:
                return self.existing[fingerprint]
        if hasattr(result, "documents"):
            for document in result.documents:
                if document.sha256:
                    fingerprint = stable_hash([document.sha256])
                    if fingerprint in self.existing:
                        return self.existing[fingerprint]
        return ""

    def add_candidate(self, case_id: str, opportunity: SourceOpportunity, documents: list[Any] | None = None) -> None:
        for fingerprint in opportunity_fingerprints(opportunity):
            self.existing[fingerprint] = case_id
        for document in documents or []:
            sha = document.sha256 if hasattr(document, "sha256") else document.get("sha256", "")
            if sha:
                self.existing[stable_hash([sha])] = case_id
