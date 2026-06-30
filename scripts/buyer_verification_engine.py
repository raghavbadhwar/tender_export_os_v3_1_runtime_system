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
    if not evidence.get("buyer_name") or evidence.get("marketplace_only"):
        missing.append("buyer legal identity")
    if not evidence.get("company_website") and not evidence.get("registration_profile"):
        missing.append("company website or registration profile")
    if not evidence.get("contact_path"):
        missing.append("contact path")
    if not evidence.get("rfq_source_url"):
        missing.append("buyer-specific RFQ proof")
    if not evidence.get("payment_terms"):
        missing.append("payment terms")
    if evidence.get("destination_risk") == "high":
        return {"stage": "RISKY", "ready": False, "missing_evidence": missing + ["destination risk high"]}
    if evidence.get("marketplace_only"):
        return {"stage": "RAW_LEAD", "ready": False, "missing_evidence": missing}
    if missing:
        if "buyer-specific RFQ proof" in missing:
            stage = "CONTACT_VERIFIED" if evidence.get("contact_path") else "BUYER_VISIBLE"
        elif "payment terms" in missing:
            stage = "RFQ_VERIFIED"
        else:
            stage = "COMPANY_VERIFIED" if evidence.get("company_website") or evidence.get("registration_profile") else "BUYER_VISIBLE"
        return {"stage": stage, "ready": False, "missing_evidence": missing}
    return {"stage": "READY_FOR_APPROVAL", "ready": True, "missing_evidence": []}
