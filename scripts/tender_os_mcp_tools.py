#!/usr/bin/env python3
"""Typed, bounded Tender Export OS tools exposed to Hermes through MCP."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from scripts.score_opportunity import (
    evaluate_trader_specific_kills,
    score_export_opportunity,
    score_gov_opportunity,
)
from scripts.gov_fast_kill import evaluate_gov_fast_kill
from scripts.execution_receipt_status import dispositions_by_approval
from scripts.event_ledger import append_event
from scripts.source_runtime.document_intelligence import run_document_intelligence_bundle, sha256_file
from scripts.tender_os_policy import PROJECT_ROOT, TenderPolicyEngine, display_path, load_csv
from scripts.update_master_case import validate_status_transition


MASTER_CASES = PROJECT_ROOT / "data" / "master_cases.csv"
SOURCE_HEALTH = PROJECT_ROOT / "data" / "source_health.csv"
APPROVALS = PROJECT_ROOT / "data" / "approvals_receipts.csv"
INTERNAL_WRITE_RECEIPT_DIR = "receipts/internal_mcp_writes"
ALLOWED_DOCUMENT_SUFFIXES = {
    ".csv",
    ".docx",
    ".htm",
    ".html",
    ".json",
    ".md",
    ".pdf",
    ".txt",
    ".xls",
    ".xlsx",
    ".xml",
    ".yaml",
    ".yml",
}


class MCPToolResult(BaseModel):
    """Stable response contract for every Tender OS MCP tool."""

    status: Literal["success", "partial", "blocked", "failed"]
    evidence_ids: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    source_hashes: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    missing_information: list[str] = Field(default_factory=list)
    recommended_next_action: str
    approval_required: bool
    policy_decision_id: str
    policy_receipt_path: str = ""
    external_side_effects: Literal[False] = False
    data: dict[str, Any] = Field(default_factory=dict)


class InternalCaseTransitionRequest(BaseModel):
    case_id: str = Field(min_length=1)
    from_status: str = Field(min_length=1)
    to_status: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    citations: list[str] = Field(min_length=1)
    actor_profile: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=8)
    reason: str = Field(min_length=1)


class InternalEvidenceAttachmentRequest(BaseModel):
    case_id: str = Field(min_length=1)
    evidence_path: str = Field(min_length=1)
    evidence_type: str = Field(min_length=1)
    actor_profile: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=8)
    citations: list[str] = Field(min_length=1)


class InternalSupplierCandidateRequest(BaseModel):
    case_id: str = Field(min_length=1)
    supplier_id: str = Field(min_length=1)
    supplier_name: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    evidence_path: str = Field(min_length=1)
    actor_profile: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=8)
    citations: list[str] = Field(min_length=1)


class InternalQuoteProofRequest(BaseModel):
    case_id: str = Field(min_length=1)
    supplier_id: str = Field(min_length=1)
    quote_id: str = Field(min_length=1)
    proof_status: Literal["VALID", "REJECTED"]
    quote_proof_path: str = ""
    reason: str = Field(min_length=1)
    actor_profile: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=8)
    citations: list[str] = Field(min_length=1)


class InternalApprovalCardRequest(BaseModel):
    case_id: str = Field(min_length=1)
    proposed_action: str = Field(min_length=1)
    scope_hash: str = Field(min_length=64, max_length=64)
    card_path: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    actor_profile: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=8)
    citations: list[str] = Field(min_length=1)


class InternalCaseOutcomeRequest(BaseModel):
    case_id: str = Field(min_length=1)
    outcome_id: str = Field(min_length=1)
    outcome_status: str = Field(min_length=1)
    evidence_path: str = Field(min_length=1)
    actor_profile: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=8)
    citations: list[str] = Field(min_length=1)


class InternalLearningProposalRequest(BaseModel):
    proposal_id: str = Field(min_length=1)
    case_ids: list[str] = Field(min_length=1)
    proposal_type: Literal["memory", "skill", "rule", "prompt", "model", "source_adapter", "test"]
    summary: str = Field(min_length=1)
    evidence: list[str] = Field(min_length=1)
    tests: list[str] = Field(min_length=1)
    rollback: str = Field(min_length=1)
    actor_profile: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=8)
    citations: list[str] = Field(min_length=1)


class InternalProjectionReconciliationRequest(BaseModel):
    case_id: str = Field(min_length=1)
    receipt_path: str = Field(min_length=1)
    receipt_sha256: str = ""
    projection_name: str = Field(min_length=1)
    actor_profile: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=8)
    citations: list[str] = Field(min_length=1)



def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def file_hash(path: Path) -> list[str]:
    return [sha256_file(path)] if path.is_file() else []


class TenderOSTools:
    """Small MCP-facing façade over existing deterministic Tender OS modules."""

    def __init__(
        self,
        *,
        policy: TenderPolicyEngine | None = None,
        record_decisions: bool = True,
        project_root: Path = PROJECT_ROOT,
    ) -> None:
        self.policy = policy or TenderPolicyEngine()
        self.record_decisions = record_decisions
        self.project_root = project_root.resolve()

    def _authorize(self, action: str, *, case_id: str = "", approval_id: str = "") -> dict[str, Any]:
        return self.policy.evaluate(
            action,
            case_id=case_id,
            approval_id=approval_id,
            actor="hermes_mcp",
            record=self.record_decisions,
        )

    @staticmethod
    def _blocked(decision: dict[str, Any], next_action: str = "Request or repair the required approval evidence.") -> MCPToolResult:
        return MCPToolResult(
            status="blocked",
            confidence=1.0,
            missing_information=[str(decision.get("reason", "Policy denied the action."))],
            recommended_next_action=next_action,
            approval_required=bool(decision.get("approval_required", False)),
            policy_decision_id=str(decision.get("decision_id", "POLICY-DECISION-MISSING")),
            policy_receipt_path=str(decision.get("receipt_path", "")),
            data={
                "reason_code": decision.get("reason_code", "POLICY_DENIED"),
                "action": decision.get("action", ""),
                "tier": decision.get("tier", 5),
            },
        )

    @staticmethod
    def _base(
        decision: dict[str, Any],
        *,
        status: Literal["success", "partial", "failed"] = "success",
        confidence: float = 1.0,
        evidence_ids: list[str] | None = None,
        source_urls: list[str] | None = None,
        source_hashes: list[str] | None = None,
        missing_information: list[str] | None = None,
        recommended_next_action: str,
        data: dict[str, Any] | None = None,
    ) -> MCPToolResult:
        return MCPToolResult(
            status=status,
            evidence_ids=evidence_ids or [],
            source_urls=source_urls or [],
            source_hashes=source_hashes or [],
            confidence=confidence,
            missing_information=missing_information or [],
            recommended_next_action=recommended_next_action,
            approval_required=bool(decision.get("approval_required", False)),
            policy_decision_id=str(decision["decision_id"]),
            policy_receipt_path=str(decision.get("receipt_path", "")),
            data=data or {},
        )

    def _internal_failure(self, decision: dict[str, Any], messages: list[str]) -> MCPToolResult:
        return self._base(
            decision,
            status="failed",
            confidence=1.0,
            missing_information=messages,
            recommended_next_action="Correct the typed internal-write request and retry with fresh evidence.",
            data={"external_actions_executed": False},
        )

    def _internal_receipt_path(self, idempotency_key: str) -> Path:
        key_hash = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
        return self.policy.receipt_root.parent / "internal_mcp_writes" / f"{key_hash}.json"

    def _write_internal_event_receipt(
        self,
        *,
        event_type: str,
        case_id: str,
        object_type: str,
        object_id: str,
        payload: dict[str, Any],
        citations: list[str],
        idempotency_key: str,
        action: str,
        actor_profile: str,
        policy_decision_id: str,
    ) -> tuple[dict[str, Any], Path]:
        event = append_event(
            event_type,
            "hermes_mcp",
            case_id=case_id,
            object_type=object_type,
            object_id=object_id,
            source="mcp_internal_write",
            payload=payload,
            citations=citations,
            idempotency_key=idempotency_key,
            events_file=self.policy.events_file,
        )
        receipt_path = self._internal_receipt_path(idempotency_key)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        if not receipt_path.exists():
            receipt = {
                "schema_version": 1,
                "receipt_type": "internal_mcp_write",
                "action": action,
                "case_id": case_id,
                "actor_profile": actor_profile,
                "idempotency_key": idempotency_key,
                "event_id": event["event_id"],
                "event_type": event_type,
                "payload": payload,
                "citations": citations,
                "external_actions_executed": False,
                "policy_decision_id": policy_decision_id,
            }
            receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return event, receipt_path

    def _internal_success(
        self,
        decision: dict[str, Any],
        *,
        event: dict[str, Any],
        receipt_path: Path,
        idempotency_key: str,
        data: dict[str, Any] | None = None,
        approval_required_override: bool | None = None,
    ) -> MCPToolResult:
        output = {
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "receipt_path": display_path(receipt_path, root=self.project_root),
            "idempotency_key": idempotency_key,
            "external_actions_executed": False,
        }
        output.update(data or {})
        result = self._base(
            decision,
            confidence=1.0,
            evidence_ids=[str(event["event_id"])],
            source_hashes=file_hash(receipt_path),
            recommended_next_action="Use the receipt and canonical event for the next internal graph step; no external action was executed.",
            data=output,
        )
        if approval_required_override is not None:
            result.approval_required = approval_required_override
        return result

    def _case_exists(self, case_id: str) -> bool:
        return any(item.get("case_id") == case_id for item in read_csv(self.project_root / "data" / "master_cases.csv"))

    def _workspace_file(self, raw_path: str, *, label: str) -> tuple[Path | None, str | None, list[str]]:
        path = Path(raw_path).expanduser()
        path = path if path.is_absolute() else self.project_root / path
        path = path.resolve()
        try:
            path.relative_to(self.project_root)
        except ValueError:
            return None, None, [f"{label} escapes the Tender OS workspace"]
        if not path.is_file() or path.stat().st_size == 0:
            return None, None, [f"{label} is missing or empty: {raw_path}"]
        return path, sha256_file(path), []

    def _stage_structured_event(
        self,
        decision: dict[str, Any],
        *,
        event_type: str,
        case_id: str,
        object_type: str,
        object_id: str,
        payload: dict[str, Any],
        citations: list[str],
        idempotency_key: str,
        actor_profile: str,
        action: str,
        data: dict[str, Any] | None = None,
        approval_required: bool | None = None,
    ) -> MCPToolResult:
        try:
            event, receipt_path = self._write_internal_event_receipt(
                event_type=event_type,
                case_id=case_id,
                object_type=object_type,
                object_id=object_id,
                payload=payload,
                citations=citations,
                idempotency_key=idempotency_key,
                action=action,
                actor_profile=actor_profile,
                policy_decision_id=str(decision["decision_id"]),
            )
        except (OSError, ValueError) as exc:
            return self._internal_failure(decision, [str(exc)])
        return self._internal_success(
            decision,
            event=event,
            receipt_path=receipt_path,
            idempotency_key=idempotency_key,
            data=data,
            approval_required_override=approval_required,
        )

    def stage_case_transition(
        self,
        *,
        case_id: str,
        from_status: str,
        to_status: str,
        evidence_ids: list[str],
        citations: list[str],
        actor_profile: str,
        idempotency_key: str,
        reason: str,
    ) -> MCPToolResult:
        decision = self._authorize("mcp.stage_case_transition", case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        try:
            request = InternalCaseTransitionRequest(
                case_id=case_id,
                from_status=from_status,
                to_status=to_status,
                evidence_ids=evidence_ids,
                citations=citations,
                actor_profile=actor_profile,
                idempotency_key=idempotency_key,
                reason=reason,
            )
        except ValidationError as exc:
            return self._internal_failure(decision, [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()])
        cases_path = self.project_root / "data" / "master_cases.csv"
        row = next((item for item in read_csv(cases_path) if item.get("case_id") == request.case_id), None)
        if row is None:
            return self._internal_failure(decision, [f"case_id does not exist: {request.case_id}"])
        if row.get("status") != request.from_status:
            return self._internal_failure(
                decision,
                [f"from_status does not match canonical case status: {row.get('status')}"],
            )
        if not validate_status_transition(request.from_status, request.to_status):
            return self._internal_failure(
                decision,
                [f"invalid status transition: {request.from_status} -> {request.to_status}"],
            )
        payload = {
            "previous_status": request.from_status,
            "new_status": request.to_status,
            "reason": request.reason,
            "evidence_ids": request.evidence_ids,
            "actor_profile": request.actor_profile,
        }
        try:
            event, receipt_path = self._write_internal_event_receipt(
                event_type="case.status_changed",
                case_id=request.case_id,
                object_type="case",
                object_id=request.case_id,
                payload=payload,
                citations=request.citations,
                idempotency_key=request.idempotency_key,
                action="mcp.stage_case_transition",
                actor_profile=request.actor_profile,
                policy_decision_id=str(decision["decision_id"]),
            )
        except (OSError, ValueError) as exc:
            return self._internal_failure(decision, [str(exc)])
        return self._internal_success(
            decision,
            event=event,
            receipt_path=receipt_path,
            idempotency_key=request.idempotency_key,
            data={"case_id": request.case_id, "from_status": request.from_status, "to_status": request.to_status},
        )

    def attach_case_evidence(
        self,
        *,
        case_id: str,
        evidence_path: str,
        evidence_type: str,
        actor_profile: str,
        idempotency_key: str,
        citations: list[str],
    ) -> MCPToolResult:
        decision = self._authorize("mcp.attach_case_evidence", case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        try:
            request = InternalEvidenceAttachmentRequest(
                case_id=case_id,
                evidence_path=evidence_path,
                evidence_type=evidence_type,
                actor_profile=actor_profile,
                idempotency_key=idempotency_key,
                citations=citations,
            )
        except ValidationError as exc:
            return self._internal_failure(decision, [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()])
        cases_path = self.project_root / "data" / "master_cases.csv"
        if not any(item.get("case_id") == request.case_id for item in read_csv(cases_path)):
            return self._internal_failure(decision, [f"case_id does not exist: {request.case_id}"])
        path = Path(request.evidence_path).expanduser()
        path = path if path.is_absolute() else self.project_root / path
        path = path.resolve()
        try:
            path.relative_to(self.project_root)
        except ValueError:
            return self._internal_failure(decision, ["evidence_path escapes the Tender OS workspace"])
        if not path.is_file() or path.stat().st_size == 0:
            return self._internal_failure(decision, [f"evidence_path is missing or empty: {request.evidence_path}"])
        digest = sha256_file(path)
        payload = {
            "evidence_path": display_path(path, root=self.project_root),
            "evidence_type": request.evidence_type,
            "sha256": digest,
            "actor_profile": request.actor_profile,
        }
        try:
            event, receipt_path = self._write_internal_event_receipt(
                event_type="evidence.bundle_created",
                case_id=request.case_id,
                object_type="evidence",
                object_id=digest,
                payload=payload,
                citations=request.citations + [payload["evidence_path"]],
                idempotency_key=request.idempotency_key,
                action="mcp.attach_case_evidence",
                actor_profile=request.actor_profile,
                policy_decision_id=str(decision["decision_id"]),
            )
        except (OSError, ValueError) as exc:
            return self._internal_failure(decision, [str(exc)])
        return self._internal_success(
            decision,
            event=event,
            receipt_path=receipt_path,
            idempotency_key=request.idempotency_key,
            data={"case_id": request.case_id, "evidence_path": payload["evidence_path"], "sha256": digest},
        )

    def stage_supplier_candidate(
        self,
        *,
        case_id: str,
        supplier_id: str,
        supplier_name: str,
        source_type: str,
        evidence_path: str,
        actor_profile: str,
        idempotency_key: str,
        citations: list[str],
    ) -> MCPToolResult:
        action = "mcp.stage_supplier_candidate"
        decision = self._authorize(action, case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        try:
            request = InternalSupplierCandidateRequest(
                case_id=case_id,
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                source_type=source_type,
                evidence_path=evidence_path,
                actor_profile=actor_profile,
                idempotency_key=idempotency_key,
                citations=citations,
            )
        except ValidationError as exc:
            return self._internal_failure(decision, [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()])
        if not self._case_exists(request.case_id):
            return self._internal_failure(decision, [f"case_id does not exist: {request.case_id}"])
        path, digest, errors = self._workspace_file(request.evidence_path, label="evidence_path")
        if errors:
            return self._internal_failure(decision, errors)
        payload = {
            "case_id": request.case_id,
            "candidates": [{
                "supplier_id": request.supplier_id,
                "supplier_name": request.supplier_name,
                "source_type": request.source_type,
                "evidence_path": display_path(path, root=self.project_root),
                "evidence_sha256": digest,
            }],
            "actor_profile": request.actor_profile,
        }
        return self._stage_structured_event(
            decision,
            event_type="supplier.match_candidates_created",
            case_id=request.case_id,
            object_type="supplier_match",
            object_id=request.supplier_id,
            payload=payload,
            citations=request.citations + [payload["candidates"][0]["evidence_path"]],
            idempotency_key=request.idempotency_key,
            actor_profile=request.actor_profile,
            action=action,
            data={"case_id": request.case_id, "supplier_id": request.supplier_id, "evidence_sha256": digest},
        )

    def record_quote_proof_review(
        self,
        *,
        case_id: str,
        supplier_id: str,
        quote_id: str,
        proof_status: str,
        quote_proof_path: str = "",
        reason: str,
        actor_profile: str,
        idempotency_key: str,
        citations: list[str],
    ) -> MCPToolResult:
        action = "mcp.record_quote_proof_review"
        decision = self._authorize(action, case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        try:
            request = InternalQuoteProofRequest(
                case_id=case_id,
                supplier_id=supplier_id,
                quote_id=quote_id,
                proof_status=proof_status,
                quote_proof_path=quote_proof_path,
                reason=reason,
                actor_profile=actor_profile,
                idempotency_key=idempotency_key,
                citations=citations,
            )
        except ValidationError as exc:
            return self._internal_failure(decision, [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()])
        if not self._case_exists(request.case_id):
            return self._internal_failure(decision, [f"case_id does not exist: {request.case_id}"])
        event_type = "supplier.quote_proof_validated" if request.proof_status == "VALID" else "supplier.quote_proof_rejected"
        payload: dict[str, Any] = {
            "case_id": request.case_id,
            "supplier_id": request.supplier_id,
            "quote_id": request.quote_id,
            "reason": request.reason,
            "actor_profile": request.actor_profile,
        }
        citations_out = list(request.citations)
        digest = ""
        if request.proof_status == "VALID":
            if not request.quote_proof_path:
                return self._internal_failure(decision, ["quote_proof_path is required for a VALID review"])
            path, digest, errors = self._workspace_file(request.quote_proof_path, label="quote_proof_path")
            if errors:
                return self._internal_failure(decision, errors)
            payload["quote_proof_path"] = display_path(path, root=self.project_root)
            payload["quote_proof_sha256"] = digest
            citations_out.append(payload["quote_proof_path"])
        return self._stage_structured_event(
            decision,
            event_type=event_type,
            case_id=request.case_id,
            object_type="supplier",
            object_id=request.supplier_id,
            payload=payload,
            citations=citations_out,
            idempotency_key=request.idempotency_key,
            actor_profile=request.actor_profile,
            action=action,
            data={"case_id": request.case_id, "quote_id": request.quote_id, "proof_status": request.proof_status, "sha256": digest},
        )

    def create_internal_approval_card(
        self,
        *,
        case_id: str,
        proposed_action: str,
        scope_hash: str,
        card_path: str,
        evidence_ids: list[str],
        actor_profile: str,
        idempotency_key: str,
        citations: list[str],
    ) -> MCPToolResult:
        action = "mcp.create_internal_approval_card"
        decision = self._authorize(action, case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        try:
            request = InternalApprovalCardRequest(
                case_id=case_id,
                proposed_action=proposed_action,
                scope_hash=scope_hash,
                card_path=card_path,
                evidence_ids=evidence_ids,
                actor_profile=actor_profile,
                idempotency_key=idempotency_key,
                citations=citations,
            )
        except ValidationError as exc:
            return self._internal_failure(decision, [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()])
        if not self._case_exists(request.case_id):
            return self._internal_failure(decision, [f"case_id does not exist: {request.case_id}"])
        path, digest, errors = self._workspace_file(request.card_path, label="card_path")
        if errors:
            return self._internal_failure(decision, errors)
        payload = {
            "row": {
                "case_id": request.case_id,
                "proposed_action": request.proposed_action,
                "scope_hash": request.scope_hash,
                "approval_card_path": display_path(path, root=self.project_root),
                "card_sha256": digest,
                "evidence_ids": request.evidence_ids,
                "approval_status": "PENDING_OWNER_DECISION",
            },
            "actor_profile": request.actor_profile,
        }
        return self._stage_structured_event(
            decision,
            event_type="approval.card_created",
            case_id=request.case_id,
            object_type="approval",
            object_id=request.scope_hash,
            payload=payload,
            citations=request.citations + [payload["row"]["approval_card_path"]],
            idempotency_key=request.idempotency_key,
            actor_profile=request.actor_profile,
            action=action,
            data={"case_id": request.case_id, "scope_hash": request.scope_hash, "approval_status": "PENDING_OWNER_DECISION"},
            approval_required=True,
        )

    def record_case_outcome(
        self,
        *,
        case_id: str,
        outcome_id: str,
        outcome_status: str,
        evidence_path: str,
        actor_profile: str,
        idempotency_key: str,
        citations: list[str],
    ) -> MCPToolResult:
        action = "mcp.record_case_outcome"
        decision = self._authorize(action, case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        try:
            request = InternalCaseOutcomeRequest(
                case_id=case_id,
                outcome_id=outcome_id,
                outcome_status=outcome_status,
                evidence_path=evidence_path,
                actor_profile=actor_profile,
                idempotency_key=idempotency_key,
                citations=citations,
            )
        except ValidationError as exc:
            return self._internal_failure(decision, [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()])
        if not self._case_exists(request.case_id):
            return self._internal_failure(decision, [f"case_id does not exist: {request.case_id}"])
        path, digest, errors = self._workspace_file(request.evidence_path, label="evidence_path")
        if errors:
            return self._internal_failure(decision, errors)
        payload = {
            "row": {
                "outcome_id": request.outcome_id,
                "case_id": request.case_id,
                "outcome_status": request.outcome_status,
                "evidence_path": display_path(path, root=self.project_root),
                "evidence_sha256": digest,
                "verification_status": "VERIFIED",
            },
            "actor_profile": request.actor_profile,
        }
        return self._stage_structured_event(
            decision,
            event_type="case.outcome_recorded",
            case_id=request.case_id,
            object_type="case_outcome",
            object_id=request.outcome_id,
            payload=payload,
            citations=request.citations + [payload["row"]["evidence_path"]],
            idempotency_key=request.idempotency_key,
            actor_profile=request.actor_profile,
            action=action,
            data={"case_id": request.case_id, "outcome_id": request.outcome_id, "evidence_sha256": digest},
        )

    def stage_learning_proposal(
        self,
        *,
        proposal_id: str,
        case_ids: list[str],
        proposal_type: str,
        summary: str,
        evidence: list[str],
        tests: list[str],
        rollback: str,
        actor_profile: str,
        idempotency_key: str,
        citations: list[str],
    ) -> MCPToolResult:
        action = "mcp.stage_learning_proposal"
        decision = self._authorize(action)
        if not decision.get("allow"):
            return self._blocked(decision)
        try:
            request = InternalLearningProposalRequest(
                proposal_id=proposal_id,
                case_ids=case_ids,
                proposal_type=proposal_type,
                summary=summary,
                evidence=evidence,
                tests=tests,
                rollback=rollback,
                actor_profile=actor_profile,
                idempotency_key=idempotency_key,
                citations=citations,
            )
        except ValidationError as exc:
            return self._internal_failure(decision, [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()])
        if any(not self._case_exists(case) for case in request.case_ids):
            return self._internal_failure(decision, ["every case_id in a learning proposal must exist in the canonical case register"])
        payload = {
            "row": request.model_dump(mode="json", exclude={"citations"}),
            "actor_profile": request.actor_profile,
        }
        return self._stage_structured_event(
            decision,
            event_type="learning.proposal_staged",
            case_id=request.case_ids[0],
            object_type="learning_proposal",
            object_id=request.proposal_id,
            payload=payload,
            citations=request.citations,
            idempotency_key=request.idempotency_key,
            actor_profile=request.actor_profile,
            action=action,
            data={"proposal_id": request.proposal_id, "proposal_type": request.proposal_type},
        )

    def reconcile_projection_from_receipt(
        self,
        *,
        case_id: str,
        receipt_path: str,
        receipt_sha256: str,
        projection_name: str,
        actor_profile: str,
        idempotency_key: str,
        citations: list[str],
    ) -> MCPToolResult:
        action = "mcp.reconcile_projection_from_receipt"
        decision = self._authorize(action, case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        try:
            request = InternalProjectionReconciliationRequest(
                case_id=case_id,
                receipt_path=receipt_path,
                receipt_sha256=receipt_sha256,
                projection_name=projection_name,
                actor_profile=actor_profile,
                idempotency_key=idempotency_key,
                citations=citations,
            )
        except ValidationError as exc:
            return self._internal_failure(decision, [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()])
        if not self._case_exists(request.case_id):
            return self._internal_failure(decision, [f"case_id does not exist: {request.case_id}"])
        path, digest, errors = self._workspace_file(request.receipt_path, label="receipt_path")
        if errors:
            return self._internal_failure(decision, errors)
        if request.receipt_sha256 and request.receipt_sha256.lower() != digest.lower():
            return self._internal_failure(decision, ["receipt_sha256 does not match the retained receipt"])
        payload = {
            "case_id": request.case_id,
            "projection_name": request.projection_name,
            "receipt_path": display_path(path, root=self.project_root),
            "receipt_sha256": digest,
            "status": "RECONCILIATION_STAGED",
            "actor_profile": request.actor_profile,
        }
        return self._stage_structured_event(
            decision,
            event_type="kanban.reconciliation_applied",
            case_id=request.case_id,
            object_type="kanban_reconciliation",
            object_id=f"{request.case_id}:{request.projection_name}",
            payload=payload,
            citations=request.citations + [payload["receipt_path"]],
            idempotency_key=request.idempotency_key,
            actor_profile=request.actor_profile,
            action=action,
            data={"case_id": request.case_id, "projection_name": request.projection_name, "receipt_sha256": digest},
        )

    def capability_status(self) -> MCPToolResult:
        decision = self._authorize("mcp.capability_status")
        if not decision.get("allow"):
            return self._blocked(decision)
        opa_version = "missing"
        opa = shutil.which("opa")
        if opa:
            completed = subprocess.run(
                [opa, "version"], capture_output=True, text=True, timeout=5, check=False
            )
            first_line = (completed.stdout or completed.stderr).splitlines()
            opa_version = first_line[0].replace("Version:", "").strip() if first_line else "unknown"
        disk = shutil.disk_usage(self.project_root)
        active = {
            "fastmcp": package_version("fastmcp"),
            "opa": opa_version,
            "playwright": package_version("playwright"),
            "rapidfuzz": package_version("rapidfuzz"),
            "event_ledger": "available" if (self.project_root / "data" / "events.jsonl").is_file() else "missing",
            "document_intelligence": "available",
            "public_web_evidence": "available",
            "repeated_behavioral_evaluation": "available",
        }
        available_not_activated = {
            "promptfoo": (
                "installed, but the existing repeated structured Hermes evaluator already covers the current "
                "critical contracts without another test runtime"
                if shutil.which("promptfoo")
                else "not installed; existing repeated structured evaluator remains active"
            )
        }
        deliberately_excluded = {
            "temporal": "current cron/job supervisor and event ledger already cover present workflow volume",
            "postgres_pgvector": "current ledgers are small and rebuildable; no measured query bottleneck",
            "langfuse": "local events, receipts, and repeated behavioral evaluations already cover current observability",
            "browsertrix": "existing hashed HTML/screenshots provide adequate proof without a large archive stack",
            "docling_paddleocr": "deferred until scan/layout failures justify heavyweight local models",
        }
        return self._base(
            decision,
            confidence=1.0,
            source_hashes=file_hash(self.policy.rego_path) + file_hash(self.policy.config_path),
            recommended_next_action="Use the bounded tools; add another service only after a measured failure or scale threshold.",
            data={
                "active": active,
                "available_not_activated": available_not_activated,
                "deliberately_excluded": deliberately_excluded,
                "disk_free_bytes": disk.free,
                "mcp_external_execution_tools_exposed": False,
            },
        )

    def get_case(self, case_id: str) -> MCPToolResult:
        decision = self._authorize("mcp.get_case", case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        row = next((item for item in read_csv(MASTER_CASES) if item.get("case_id") == case_id), None)
        if row is None:
            return self._base(
                decision,
                status="failed",
                confidence=1.0,
                missing_information=[f"Case {case_id} does not exist in data/master_cases.csv."],
                recommended_next_action="Use search_cases to locate the canonical case ID.",
                source_hashes=file_hash(MASTER_CASES),
                data={"case_id": case_id},
            )
        return self._base(
            decision,
            confidence=1.0,
            evidence_ids=[case_id],
            source_urls=[row["source_url"]] if row.get("source_url") else [],
            source_hashes=file_hash(MASTER_CASES),
            recommended_next_action="Use assess_opportunity for an advisory Fast Kill and score review.",
            data={"case": row},
        )

    def search_cases(self, status: str = "", workflow_type: str = "", limit: int = 20) -> MCPToolResult:
        decision = self._authorize("mcp.search_cases")
        if not decision.get("allow"):
            return self._blocked(decision)
        bounded_limit = max(1, min(int(limit), 50))
        status_filter = status.strip().upper()
        workflow_filter = workflow_type.strip().upper()
        rows = []
        for row in read_csv(MASTER_CASES):
            if status_filter and row.get("status", "").upper() != status_filter:
                continue
            if workflow_filter and row.get("workflow_type", "").upper() != workflow_filter:
                continue
            rows.append(
                {
                    key: row.get(key, "")
                    for key in (
                        "case_id",
                        "workflow_type",
                        "status",
                        "opportunity_title",
                        "buyer_name",
                        "deadline_date",
                        "score_gov",
                        "score_export",
                        "evidence_level",
                        "source_url",
                    )
                }
            )
            if len(rows) >= bounded_limit:
                break
        return self._base(
            decision,
            confidence=1.0,
            evidence_ids=[row["case_id"] for row in rows],
            source_urls=[row["source_url"] for row in rows if row.get("source_url")],
            source_hashes=file_hash(MASTER_CASES),
            missing_information=[] if rows else ["No case matched the supplied filters."],
            recommended_next_action="Open a matching case or adjust the filters; do not invent a case ID.",
            data={"count": len(rows), "cases": rows, "limit": bounded_limit},
        )

    def assess_opportunity(self, case_id: str) -> MCPToolResult:
        decision = self._authorize("mcp.assess_opportunity", case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        row = next((item for item in read_csv(MASTER_CASES) if item.get("case_id") == case_id), None)
        if row is None:
            return self._base(
                decision,
                status="failed",
                confidence=1.0,
                missing_information=[f"Case {case_id} is absent from the canonical master register."],
                recommended_next_action="Locate or stage the case before scoring it.",
                source_hashes=file_hash(MASTER_CASES),
                data={"case_id": case_id},
            )
        workflow = row.get("workflow_type", "GOV").upper()
        if workflow == "GOV":
            # The advisory MCP has only the case projection, not a page-level
            # evidence packet, so an apparent hard kill remains WATCHLIST until
            # the deterministic stage receives cited proof.
            fast_kill = evaluate_gov_fast_kill(row, {})
            score = fast_kill["score"]
            kill_status = fast_kill["decision"]
            missing = [str(value) for value in fast_kill.get("missing_evidence", [])]
        else:
            score = score_export_opportunity(row)
            fast_kill = evaluate_trader_specific_kills(row)
            kill_status = fast_kill["status"]
            missing = [str(value) for value in fast_kill.get("missing_evidence", [])]
        if kill_status == "REJECTED":
            recommendation = "Keep the case rejected unless new evidence directly resolves the hard failure."
        elif kill_status == "WATCHLIST" or score["total"] < 60:
            recommendation = "Keep the case on WATCHLIST and obtain the listed missing evidence before Deep Read."
        else:
            recommendation = "Route the evidenced case to Deep Read; this score is advisory, not approval to bid."
        confidence = 0.9 if not missing else 0.65
        return self._base(
            decision,
            confidence=confidence,
            evidence_ids=[case_id],
            source_urls=[row["source_url"]] if row.get("source_url") else [],
            source_hashes=file_hash(MASTER_CASES),
            missing_information=missing,
            recommended_next_action=recommendation,
            data={
                "case_id": case_id,
                "workflow_type": workflow,
                "score": score,
                "fast_kill": fast_kill,
                "advisory_only": True,
            },
        )

    def get_source_health(self, source_name: str = "", limit: int = 20) -> MCPToolResult:
        decision = self._authorize("mcp.get_source_health")
        if not decision.get("allow"):
            return self._blocked(decision)
        needle = source_name.strip().lower()
        rows = [
            row
            for row in read_csv(SOURCE_HEALTH)
            if not needle or needle in row.get("source_name", "").lower()
        ][: max(1, min(int(limit), 50))]
        return self._base(
            decision,
            confidence=1.0,
            source_urls=[row["url"] for row in rows if row.get("url")],
            source_hashes=file_hash(SOURCE_HEALTH),
            missing_information=[] if rows else ["No source-health row matched the requested name."],
            recommended_next_action="Use only sources marked Working; route login/CAPTCHA/paywall blockers to manual review.",
            data={"count": len(rows), "sources": rows},
        )

    def parse_local_documents(
        self,
        paths: list[str],
        case_id: str = "",
        workflow: str = "GENERAL",
        enable_ocr: bool = False,
    ) -> MCPToolResult:
        decision = self._authorize("mcp.parse_local_documents", case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        if not paths or len(paths) > 20:
            return self._base(
                decision,
                status="failed",
                confidence=1.0,
                missing_information=["Provide between 1 and 20 local document paths."],
                recommended_next_action="Place the documents inside the Tender OS workspace and retry.",
                data={},
            )
        resolved: list[Path] = []
        errors: list[str] = []
        for raw in paths:
            candidate = Path(raw).expanduser()
            candidate = candidate if candidate.is_absolute() else self.project_root / candidate
            candidate = candidate.resolve()
            try:
                candidate.relative_to(self.project_root)
            except ValueError:
                errors.append(f"Path escapes the Tender OS workspace: {raw}")
                continue
            if not candidate.is_file():
                errors.append(f"Document does not exist: {raw}")
                continue
            if candidate.suffix.lower() not in ALLOWED_DOCUMENT_SUFFIXES:
                errors.append(f"Unsupported document type: {candidate.suffix or '(none)'}")
                continue
            if candidate.stat().st_size > 100 * 1024 * 1024:
                errors.append(f"Document exceeds 100 MB: {raw}")
                continue
            resolved.append(candidate)
        if errors:
            return self._base(
                decision,
                status="failed",
                confidence=1.0,
                missing_information=errors,
                recommended_next_action="Correct the bounded local paths; no external or arbitrary filesystem path is accepted.",
                data={},
            )
        bundle = run_document_intelligence_bundle(
            [str(path) for path in resolved],
            workflow=workflow,
            case_id=case_id,
            archive_inputs=True,
            enable_ocr=enable_ocr,
        )
        blockers = [
            f"{item.get('source_filename', '')}: {item.get('reason', '')}"
            for item in bundle.get("blockers", [])
        ]
        status: Literal["success", "partial", "failed"] = "success" if not blockers else "partial"
        return self._base(
            decision,
            status=status,
            confidence=1.0 if not blockers else 0.7,
            evidence_ids=[str(bundle["run_id"])],
            source_hashes=[str(doc["sha256"]) for doc in bundle.get("documents", [])],
            missing_information=blockers,
            recommended_next_action=(
                "Use the page/file-cited evidence bundle for Deep Read; do not treat extraction as final compliance proof."
                if not blockers
                else "Resolve OCR/manual-review blockers before using the extraction for a case decision."
            ),
            data={
                "run_id": bundle["run_id"],
                "manifest_path": display_path(Path(bundle["manifest_path"])),
                "report_path": display_path(Path(bundle["report_path"])),
                "summary": bundle["summary"],
                "tool_statuses": bundle["tool_statuses"],
            },
        )

    def capture_public_web(
        self,
        urls: list[str],
        source_name: str,
        case_id: str = "",
        follow_links: bool = False,
        max_pages: int = 5,
        max_depth: int = 1,
    ) -> MCPToolResult:
        decision = self._authorize("mcp.capture_public_web", case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        if not source_name.strip() or not urls or len(urls) > 10:
            return self._base(
                decision,
                status="failed",
                confidence=1.0,
                missing_information=["A source name and between 1 and 10 public HTTPS URLs are required."],
                recommended_next_action="Provide bounded public source URLs; authenticated/private targets are not accepted.",
                data={},
            )
        from scripts.public_web_evidence_scraper import scrape

        try:
            receipt, receipt_path = scrape(
                urls,
                source_name=source_name,
                case_id=case_id,
                follow_links=bool(follow_links),
                max_pages=max(1, min(int(max_pages), 10)),
                max_depth=max(0, min(int(max_depth), 1)),
            )
        except (OSError, ValueError) as exc:
            return self._base(
                decision,
                status="failed",
                confidence=1.0,
                source_urls=urls,
                missing_information=[str(exc)],
                recommended_next_action="Use an allowed public HTTPS source or route a login/CAPTCHA case to manual review.",
                data={},
            )
        hashes = sorted(
            {
                str(value)
                for page in receipt.get("pages", [])
                for value in (page.get("sha256", {}) or {}).values()
                if value
            }
        )
        status_map = {"COMPLETED": "success", "PARTIAL": "partial", "FAILED": "failed"}
        tool_status = status_map.get(str(receipt.get("status")), "failed")
        return self._base(
            decision,
            status=tool_status,  # type: ignore[arg-type]
            confidence=1.0 if tool_status == "success" else 0.6,
            evidence_ids=[str(receipt["run_id"])],
            source_urls=list(receipt.get("seed_urls", urls)),
            source_hashes=hashes,
            missing_information=[
                f"robots_blocked={receipt['summary']['robots_blocked']}",
                f"failed={receipt['summary']['failed']}",
            ]
            if tool_status != "success"
            else [],
            recommended_next_action="Review the receipt and source hashes; public catalogue fit remains a lead, not confirmed demand.",
            data={
                "run_id": receipt["run_id"],
                "receipt_path": display_path(receipt_path),
                "summary": receipt["summary"],
                "safety": receipt["safety"],
            },
        )

    def get_approval_status(self, case_id: str = "", approval_id: str = "") -> MCPToolResult:
        decision = self._authorize("mcp.get_approval_status", case_id=case_id)
        if not decision.get("allow"):
            return self._blocked(decision)
        approvals = load_csv(APPROVALS)
        dispositions = dispositions_by_approval(approvals)
        rows = []
        for row in approvals:
            if case_id and row.get("case_id") != case_id:
                continue
            if approval_id and row.get("approval_id") != approval_id:
                continue
            projected = {
                key: row.get(key, "")
                for key in (
                    "approval_id",
                    "case_id",
                    "workflow_type",
                    "action_approved",
                    "approval_status",
                    "approved_by",
                    "approved_at",
                    "requested_at",
                    "approval_timeout_at",
                    "scope_hash",
                    "receipt_id",
                    "receipt_path",
                    "approval_card_path",
                    "external_effect",
                )
            }
            disposition = dispositions.get(row.get("approval_id", ""), {})
            projected["approval_external_effect"] = projected["external_effect"]
            projected["external_effect"] = disposition.get("external_effect", projected["external_effect"])
            projected["execution_receipt_count"] = disposition.get("execution_receipt_count", 0)
            projected["execution_receipt_ids"] = disposition.get("execution_receipt_ids", [])
            projected["execution_receipt_paths"] = disposition.get("execution_receipt_paths", [])
            rows.append(projected)
        return self._base(
            decision,
            confidence=1.0,
            evidence_ids=[row["approval_id"] for row in rows],
            source_hashes=file_hash(APPROVALS),
            missing_information=[] if rows else ["No approval matched the supplied scope."],
            recommended_next_action="Evaluate the exact business action before execution; APPROVED text alone is not sufficient.",
            data={"count": len(rows), "approvals": rows},
        )

    def evaluate_business_action(
        self,
        action: str,
        case_id: str = "",
        approval_id: str = "",
    ) -> MCPToolResult:
        invocation = self._authorize("mcp.evaluate_business_action", case_id=case_id)
        if not invocation.get("allow"):
            return self._blocked(invocation)
        target = self.policy.evaluate(
            action,
            case_id=case_id,
            approval_id=approval_id,
            actor="hermes_mcp_policy_probe",
            record=self.record_decisions,
        )
        result_status: Literal["success", "blocked"] = "success" if target.get("allow") else "blocked"
        return MCPToolResult(
            status=result_status,
            evidence_ids=[value for value in [target.get("approval", {}).get("receipt_id", "")] if value],
            source_urls=[],
            source_hashes=[target["policy_sha256"], target["config_sha256"]],
            confidence=1.0,
            missing_information=[] if target.get("allow") else [str(target.get("reason", "Policy denied."))],
            recommended_next_action=(
                "The policy evidence is valid, but execute only through a separately registered, owner-authorized tool."
                if target.get("allow")
                else "Create or refresh the exact scoped approval evidence; never infer permission from conversation text."
            ),
            approval_required=bool(target.get("approval_required", False)),
            policy_decision_id=str(target["decision_id"]),
            policy_receipt_path=str(target.get("receipt_path", "")),
            data={
                "allow": target.get("allow", False),
                "status": target.get("status", "blocked"),
                "reason_code": target.get("reason_code", ""),
                "reason": target.get("reason", ""),
                "action": target.get("action", action),
                "tier": target.get("tier", 5),
                "approval": target.get("approval", {}),
                "required_controls": target.get("required_controls", {}),
                "invocation_policy_decision_id": invocation["decision_id"],
                "execution_tool_exposed": False,
            },
        )


def result_json(result: MCPToolResult) -> str:
    return json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False)
