#!/usr/bin/env python3
"""Buyer verification stage engine for export RFQ leads."""

from __future__ import annotations

from typing import Any

STAGES = [
    "RAW_LEAD",
    "BUYER_VISIBLE",
    "COMPANY_VERIFIED",
    "IMPORT_HISTORY_VERIFIED",
    "CONTACT_VERIFIED",
    "RFQ_VERIFIED",
    "PAYMENT_TERMS_KNOWN",
    "READY_FOR_APPROVAL",
    "RISKY",
]


def verify_buyer_stage(evidence: dict[str, Any]) -> dict[str, Any]:
    missing = []
    marketplace_only = bool(evidence.get("marketplace_only"))
    identity_present = bool(evidence.get("buyer_name")) and not marketplace_only
    company_proof_present = bool(evidence.get("company_website") or evidence.get("registration_profile"))
    contact_path_present = bool(evidence.get("contact_path"))
    rfq_present = bool(evidence.get("rfq_source_url"))
    payment_terms_present = bool(evidence.get("payment_terms"))
    if not identity_present:
        missing.append("buyer legal identity")
    if not company_proof_present:
        missing.append("company website or registration profile")
    if not contact_path_present:
        missing.append("contact path")
    if not rfq_present:
        missing.append("buyer-specific RFQ proof")
    if not payment_terms_present:
        missing.append("payment terms")
    if evidence.get("destination_risk") == "high":
        return {
            "stage": "RISKY",
            "ready": False,
            "contact_ready": False,
            "rfq_ready": False,
            "demand_status": "BLOCKED_RISK",
            "missing_evidence": missing + ["destination risk high"],
        }
    if marketplace_only:
        return {
            "stage": "RAW_LEAD",
            "ready": False,
            "contact_ready": False,
            "rfq_ready": False,
            "demand_status": "MARKETPLACE_LEAD_ONLY",
            "missing_evidence": missing,
        }
    contact_ready = identity_present and company_proof_present and contact_path_present
    rfq_ready = contact_ready and rfq_present and payment_terms_present
    if not rfq_ready:
        if "buyer-specific RFQ proof" in missing:
            stage = "CONTACT_VERIFIED" if contact_ready else "BUYER_VISIBLE"
        elif "payment terms" in missing:
            stage = "RFQ_VERIFIED"
        else:
            stage = "COMPANY_VERIFIED" if company_proof_present else "BUYER_VISIBLE"
        return {
            "stage": stage,
            "ready": False,
            "contact_ready": contact_ready,
            "rfq_ready": False,
            "demand_status": "CATALOGUE_HYPOTHESIS" if not rfq_present else "RFQ_PARTIAL",
            "missing_evidence": missing,
        }
    return {
        "stage": "READY_FOR_APPROVAL",
        "ready": True,
        "contact_ready": True,
        "rfq_ready": True,
        "demand_status": "RFQ_VERIFIED",
        "missing_evidence": [],
    }
