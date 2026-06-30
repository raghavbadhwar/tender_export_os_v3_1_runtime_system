"""Shared idempotency key helpers for Tender Export OS workflows."""

from __future__ import annotations

import hashlib
import re
from typing import Iterable


def normalize_part(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def build_idempotency_key(prefix: str, *parts: object) -> str:
    normalized = [normalize_part(part) for part in parts if normalize_part(part)]
    return f"{prefix}:{':'.join(normalized)}"


def hash_key(prefix: str, parts: Iterable[object], length: int = 16) -> str:
    raw = build_idempotency_key(prefix, *list(parts))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}:{digest}"


def source_adapter_key(source: str, external_reference: str, run_date: str) -> str:
    return build_idempotency_key("source_adapter", source, external_reference, run_date)


def case_create_key(source: str, tender_id_or_url: str) -> str:
    return build_idempotency_key("case_create", source, tender_id_or_url)


def approval_card_key(case_id: str, proposed_action: str) -> str:
    return build_idempotency_key("approval_card", case_id, proposed_action)


def supplier_request_key(case_id: str, supplier_id: str, request_type: str) -> str:
    return build_idempotency_key("supplier_request", case_id, supplier_id, request_type)


def chatgpt_return_key(content_hash: str) -> str:
    return build_idempotency_key("chatgpt_return", content_hash)


def corrigendum_key(case_id: str, corrigendum_hash: str) -> str:
    return build_idempotency_key("corrigendum", case_id, corrigendum_hash)
