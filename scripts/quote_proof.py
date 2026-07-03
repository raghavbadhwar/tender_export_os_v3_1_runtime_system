#!/usr/bin/env python3
"""Strict supplier quote-proof classification for Tender Export OS."""

from __future__ import annotations

from typing import Any


ACCEPTED_SUPPLIER_QUOTE_PROOF_TYPES = {
    "supplier_specific_response",
    "supplier_written_quote",
    "supplier_quote_pdf",
    "proforma",
    "proforma_invoice",
    "email_quote",
    "quotation_pdf",
    "verified_portal_quote",
    "signed_quote",
}

INDICATIVE_OR_MARKETPLACE_PROOF_TYPES = {
    "marketplace_listing",
    "public_listing",
    "public_catalog",
    "public_price_list",
    "catalogue_price",
    "catalog_price",
    "tradeindia_listing",
    "indiamart_listing",
    "alibaba_listing",
    "generic_benchmark",
    "comparable_price",
}

TRUE_VALUES = {"1", "true", "yes", "y", "approved", "done"}
FALSE_VALUES = {"0", "false", "no", "n"}


def norm(value: Any) -> str:
    return str(value or "").strip()


def norm_lower(value: Any) -> str:
    return norm(value).lower().replace(" ", "_").replace("-", "_")


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return norm_lower(value) in TRUE_VALUES


def explicit_false(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    return norm_lower(value) in FALSE_VALUES


def supplier_identity(row: dict[str, Any]) -> str:
    return norm(row.get("supplier_id")) or norm(row.get("supplier_name"))


def is_indicative_signal(row: dict[str, Any]) -> bool:
    proof_type = norm_lower(row.get("quote_proof_type"))
    return (
        proof_type in INDICATIVE_OR_MARKETPLACE_PROOF_TYPES
        or as_bool(row.get("indicative_price_only"))
        or as_bool(row.get("marketplace_listing_price"))
        or as_bool(row.get("not_a_quote_warning"))
    )


def is_supplier_specific_proof_asset(row: dict[str, Any]) -> bool:
    """Return true for a supplier-specific proof asset, independent of case row completeness."""
    proof_type = norm_lower(row.get("quote_proof_type"))
    proof_path = norm(row.get("quote_proof_path"))
    return bool(proof_path and proof_type in ACCEPTED_SUPPLIER_QUOTE_PROOF_TYPES and not is_indicative_signal(row))


def classify_quote_proof(row: dict[str, Any]) -> dict[str, Any]:
    """Classify one quote row under strict supplier-specific proof semantics."""
    blockers: list[str] = []
    warnings: list[str] = []
    proof_type = norm_lower(row.get("quote_proof_type"))

    if not norm(row.get("case_id")):
        blockers.append("missing case_id")
    if not supplier_identity(row):
        blockers.append("missing supplier_id or supplier_name")
    if not norm(row.get("quote_received_at")):
        blockers.append("missing quote_received_at")
    if is_indicative_signal(row):
        blockers.append("indicative marketplace/public listing signals are not quote proof")
    if proof_type not in ACCEPTED_SUPPLIER_QUOTE_PROOF_TYPES:
        blockers.append(f"quote_proof_type {proof_type or '<blank>'} is not supplier-specific")

    proof_path = norm(row.get("quote_proof_path"))
    supplier_specific_flag = as_bool(row.get("supplier_specific_quote"))
    if explicit_false(row.get("supplier_specific_quote")):
        blockers.append("supplier_specific_quote is false")
    if not proof_path and not supplier_specific_flag:
        blockers.append("missing quote_proof_path or supplier_specific_quote=TRUE")
    if supplier_specific_flag and not proof_path:
        warnings.append("supplier_specific_quote=TRUE used without quote_proof_path")

    is_strict = not blockers
    return {
        "is_strict_quote_proof": is_strict,
        "classification": "SUPPLIER_SPECIFIC_QUOTE_PROOF" if is_strict else (
            "INDICATIVE_SIGNAL" if is_indicative_signal(row) else "INSUFFICIENT_QUOTE_PROOF"
        ),
        "quote_id": norm(row.get("quote_id")),
        "case_id": norm(row.get("case_id")),
        "supplier_identity": supplier_identity(row),
        "quote_proof_type": proof_type,
        "blockers": blockers,
        "warnings": warnings,
    }


def strict_quote_proofs(case_id: str, quotes: list[dict[str, Any]], *, unique_suppliers: bool = True) -> list[dict[str, Any]]:
    """Return quote rows that satisfy strict proof semantics, deduped by supplier by default."""
    accepted: list[dict[str, Any]] = []
    seen_suppliers: set[str] = set()
    for quote in quotes:
        if norm(quote.get("case_id")) != case_id:
            continue
        classification = classify_quote_proof(quote)
        if not classification["is_strict_quote_proof"]:
            continue
        supplier = classification["supplier_identity"].lower()
        if unique_suppliers and supplier in seen_suppliers:
            continue
        seen_suppliers.add(supplier)
        accepted.append(quote)
    return accepted
