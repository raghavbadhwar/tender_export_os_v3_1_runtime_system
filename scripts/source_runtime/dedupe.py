"""Opportunity deduplication for deep source results."""

from __future__ import annotations

import csv
import json
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


def canonical_url(value: str) -> str:
    return (value or "").strip().split("#", 1)[0].rstrip("/")


def opportunity_fingerprints(opportunity: SourceOpportunity) -> set[str]:
    fingerprints = set()
    if opportunity.external_reference:
        fingerprints.add(stable_hash([opportunity.source_name, opportunity.external_reference]))
        fingerprints.add(stable_hash([opportunity.external_reference]))
    if opportunity.source_url:
        fingerprints.add(stable_hash([canonical_url(opportunity.source_url)]))
    if opportunity.opportunity_title or opportunity.buyer_name or opportunity.deadline_date:
        fingerprints.add(stable_hash([opportunity.opportunity_title, opportunity.buyer_name, opportunity.deadline_date]))
    if opportunity.workflow_type == "EXPORT" and (opportunity.buyer_name or opportunity.product_or_service):
        fingerprints.add(stable_hash([opportunity.buyer_name, opportunity.product_or_service, opportunity.deadline_date]))
    return fingerprints


class DedupeEngine:
    def __init__(self, case_register: Path = DEFAULT_CASES) -> None:
        self.case_register = case_register
        self.existing: dict[str, str] = {}
        self._load_cases()
        self._load_events()
        self._load_evidence_manifests()
        self._load_source_runs()

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

    def _remember_opportunity(self, case_id: str, payload: dict[str, Any]) -> None:
        opportunity = SourceOpportunity(
            source_name=str(payload.get("source_name", "") or payload.get("source_portal", "")),
            source_type="",
            workflow_type=str(payload.get("workflow_type", "")),
            source_url=str(payload.get("source_url", "")),
            external_reference=str(payload.get("tender_id", "") or payload.get("bid_number", "") or payload.get("external_reference", "") or payload.get("case_id", "")),
            opportunity_title=str(payload.get("opportunity_title", "") or payload.get("title", "")),
            buyer_name=str(payload.get("buyer_name", "") or payload.get("buyer_organisation", "")),
            product_or_service=str(payload.get("product_or_service", "")),
            deadline_date=str(payload.get("deadline_date", "") or payload.get("bid_end_date", "")),
        )
        for fingerprint in opportunity_fingerprints(opportunity):
            self.existing[fingerprint] = case_id

    def _load_events(self) -> None:
        events_path = PROJECT_ROOT / "data" / "events.jsonl"
        if not events_path.exists():
            return
        with events_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("object_type") != "case":
                    continue
                case_id = event.get("case_id") or event.get("object_id", "")
                payload = event.get("payload", {})
                if isinstance(payload.get("row"), dict):
                    payload = payload["row"]
                if case_id and isinstance(payload, dict):
                    self._remember_opportunity(case_id, payload)

    def _load_evidence_manifests(self) -> None:
        for manifest in (PROJECT_ROOT / "outputs" / "evidence").glob("**/evidence_manifest.json"):
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except Exception:
                continue
            case_id = str(data.get("case_id", ""))
            for item in data.get("downloads", []):
                if isinstance(item, dict) and item.get("sha256") and case_id:
                    self.existing[stable_hash([str(item["sha256"])])] = case_id

    def _load_source_runs(self) -> None:
        for run_path in (PROJECT_ROOT / "outputs" / "source_runs").glob("**/deep_results.json"):
            try:
                data = json.loads(run_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for run in data.get("results", []):
                for result in run.get("deep_results", []):
                    shallow = result.get("shallow", {})
                    case_id = result.get("case_id", "") or shallow.get("case_id", "")
                    if case_id:
                        self._remember_opportunity(case_id, shallow)
                    for document in result.get("documents", []):
                        if document.get("sha256") and case_id:
                            self.existing[stable_hash([str(document["sha256"])])] = case_id

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
