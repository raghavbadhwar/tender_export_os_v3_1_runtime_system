#!/usr/bin/env python3
"""Strict supplier quote-proof classification for Tender Export OS."""

from __future__ import annotations

import datetime as dt
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
REQUIRED_VERIFICATION_STATUS = "VERIFIED"
REQUIRED_SPEC_MATCH = "TRUE"
SHA256_LENGTH = 64


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


def positive_number(value: Any) -> bool:
    try:
        return float(str(value).replace(",", "")) > 0
    except (TypeError, ValueError):
        return False


def parse_iso_datetime(value: Any) -> dt.datetime | None:
    try:
        parsed = dt.datetime.fromisoformat(norm(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def parse_iso_date(value: Any) -> dt.date | None:
    try:
        return dt.date.fromisoformat(norm(value)[:10])
    except ValueError:
        return None


def as_of_date(value: dt.date | dt.datetime | str | None = None) -> dt.date:
    if value is None:
        return dt.datetime.now(dt.timezone.utc).date()
    if isinstance(value, dt.datetime):
        return value.astimezone(dt.timezone.utc).date() if value.tzinfo else value.date()
    if isinstance(value, dt.date):
        return value
    parsed = parse_iso_date(value)
    if parsed is None:
        raise ValueError("as_of must be an ISO date or datetime")
    return parsed


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


def classify_quote_proof(row: dict[str, Any], *, as_of: dt.date | dt.datetime | str | None = None) -> dict[str, Any]:
    """Classify one quote row under strict supplier-specific proof semantics."""
    blockers: list[str] = []
    warnings: list[str] = []
    proof_type = norm_lower(row.get("quote_proof_type"))

    if not norm(row.get("case_id")):
        blockers.append("missing case_id")
    if not norm(row.get("supplier_id")) or not norm(row.get("supplier_name")):
        blockers.append("supplier identity requires supplier_id and supplier_name")
    quote_received_at = parse_iso_datetime(row.get("quote_received_at"))
    if quote_received_at is None:
        blockers.append("quote_received_at must be an ISO-8601 timestamp with timezone")
    if is_indicative_signal(row):
        blockers.append("indicative marketplace/public listing signals are not quote proof")
    if proof_type not in ACCEPTED_SUPPLIER_QUOTE_PROOF_TYPES:
        blockers.append(f"quote_proof_type {proof_type or '<blank>'} is not supplier-specific")

    proof_path = norm(row.get("quote_proof_path"))
    supplier_specific_flag = as_bool(row.get("supplier_specific_quote"))
    if explicit_false(row.get("supplier_specific_quote")):
        blockers.append("supplier_specific_quote is false")
    if not proof_path:
        blockers.append("missing quote_proof_path")
    if supplier_specific_flag and not proof_path:
        warnings.append("supplier_specific_quote=TRUE does not replace a retained quote proof asset")

    if norm(row.get("quote_verification_status")).upper() != REQUIRED_VERIFICATION_STATUS:
        blockers.append("quote_verification_status must be VERIFIED")
    proof_hash = norm(row.get("quote_proof_sha256")).lower()
    if len(proof_hash) != SHA256_LENGTH or any(char not in "0123456789abcdef" for char in proof_hash):
        blockers.append("quote_proof_sha256 must be a 64-character SHA-256 hash")
    if norm(row.get("case_spec_match")).upper() != REQUIRED_SPEC_MATCH:
        blockers.append("case_spec_match must be TRUE")
    if not norm(row.get("product_description")):
        blockers.append("missing product_description for case/spec match")
    if not positive_number(row.get("quantity")) and not positive_number(row.get("min_order_qty")):
        blockers.append("quote requires a positive quoted quantity or MOQ")
    if not norm(row.get("currency")):
        blockers.append("missing currency")
    if not (norm(row.get("tax_treatment")) or norm(row.get("gst_rate_pct")) or norm(row.get("price_basis"))):
        blockers.append("missing tax treatment or price basis")
    if not (positive_number(row.get("unit_price_inr")) or positive_number(row.get("unit_price_usd")) or positive_number(row.get("total_price_inr")) or positive_number(row.get("total_price_usd"))):
        blockers.append("missing positive quoted price")
    if not positive_number(row.get("lead_time_days")):
        blockers.append("missing positive lead_time_days")
    if not norm(row.get("delivery_terms")):
        blockers.append("missing delivery_terms")
    if not norm(row.get("payment_terms_offered")):
        blockers.append("missing payment_terms_offered")

    validity_date = parse_iso_date(row.get("quote_validity_date"))
    validity_days = row.get("validity_days")
    if validity_date is None and not positive_number(validity_days):
        blockers.append("quote requires quote_validity_date or positive validity_days")
    elif quote_received_at is not None:
        expiry = validity_date
        if expiry is None:
            expiry = quote_received_at.date() + dt.timedelta(days=int(float(str(validity_days))))
        if expiry < as_of_date(as_of):
            blockers.append("quote is expired as of readiness check")

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


def strict_quote_proofs(
    case_id: str,
    quotes: list[dict[str, Any]],
    *,
    unique_suppliers: bool = True,
    as_of: dt.date | dt.datetime | str | None = None,
) -> list[dict[str, Any]]:
    """Return quote rows that satisfy strict proof semantics, deduped by supplier by default."""
    accepted: list[dict[str, Any]] = []
    seen_suppliers: set[str] = set()
    for quote in quotes:
        if norm(quote.get("case_id")) != case_id:
            continue
        classification = classify_quote_proof(quote, as_of=as_of)
        if not classification["is_strict_quote_proof"]:
            continue
        supplier = classification["supplier_identity"].lower()
        if unique_suppliers and supplier in seen_suppliers:
            continue
        seen_suppliers.add(supplier)
        accepted.append(quote)
    return accepted
