"""Rule-based tender field extraction from parsed evidence."""

from __future__ import annotations

import re
from typing import Any

try:
    from scripts.source_adapters.base import DeepExtractedFields, SourceOpportunity
except ModuleNotFoundError:  # pragma: no cover
    from source_adapters.base import DeepExtractedFields, SourceOpportunity  # type: ignore

CRITICAL_FIELDS = {
    "bid_end_date": [r"(?:bid\s*end|closing|last\s*date|due\s*date)[:\-\s]+([^\n|]{4,80})"],
    "emd_amount_inr": [r"(?:emd|earnest\s*money)[^\n₹\d]*(₹?\s?(?:Rs\.?|INR)?\s?[\d,]+(?:\.\d+)?)"],
    "tender_value_inr": [r"(?:tender\s*value|estimated\s*value|contract\s*value)[^\n₹\d]*(₹?\s?(?:Rs\.?|INR)?\s?[\d,]+(?:\.\d+)?)"],
    "turnover_requirement": [r"(?:turnover|annual\s*turnover)[:\-\s]+([^\n]{4,160})"],
    "past_experience_requirement": [r"(?:past\s*experience|similar\s*work|experience)[:\-\s]+([^\n]{4,180})"],
    "delivery_location": [r"(?:delivery\s*location|place\s*of\s*delivery|location)[:\-\s]+([^\n]{3,140})"],
    "payment_terms": [r"(?:payment\s*terms|payment)[:\-\s]+([^\n]{4,180})"],
}

DOCUMENT_PATTERNS = [
    r"(?:documents?\s*required|document\s*checklist|forms?\s*required)[:\-\s]+([^\n]{4,260})",
    r"(?:upload|submit)\s+(?:the\s+)?([A-Za-z0-9 ,/()&.-]{4,120}(?:certificate|declaration|undertaking|form|license|licence))",
]
RISK_WORDS = {
    "DSC_REQUIRED": r"\bDSC\b|digital\s*signature",
    "OEM_AUTH_REQUIRED": r"\bOEM\b|manufacturer'?s?\s*authorization|authorisation",
    "PAST_EXPERIENCE_REQUIRED": r"past\s*experience|similar\s*work",
    "PENALTY_CLAUSE": r"penalt(?:y|ies)|liquidated\s*damages",
    "PERFORMANCE_SECURITY": r"performance\s*security|security\s*deposit",
    "STRICT_DEADLINE": r"no\s*extension|late\s*bids?\s*will\s*not",
}


def _first_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return " ".join(match.group(1).split())[:300]
    return ""


def _first_match_with_evidence(parsed_results: list[dict[str, Any]], patterns: list[str]) -> tuple[str, dict[str, Any]]:
    for item in parsed_results:
        text = str(item.get("text", ""))
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.I)
            if match:
                value = " ".join(match.group(1).split())[:300]
                return value, {
                    "value": value,
                    "confidence": 0.82 if item.get("confidence") in {"HIGH", "MEDIUM"} else 0.55,
                    "evidence_file": item.get("source_path", ""),
                    "page": item.get("page", ""),
                    "extraction_method": "regex_text",
                    "review_required": False,
                }
    return "", {}


def _extract_boq_items(tables: list[Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for table in tables:
        rows = table.get("rows", []) if isinstance(table, dict) else table
        if not rows or not isinstance(rows, list):
            continue
        headers = [str(cell).strip().lower() for cell in rows[0]] if rows else []
        has_item = any(word in " ".join(headers) for word in ["item", "description", "qty", "quantity", "unit"])
        if not has_item:
            continue
        for row in rows[1:8]:
            if not isinstance(row, list) or not any(str(cell).strip() for cell in row):
                continue
            item = {}
            for idx, cell in enumerate(row[: len(headers)]):
                key = headers[idx] or f"col_{idx + 1}"
                item[key] = str(cell).strip()
            items.append(item)
    return items[:25]


def extract_fields(
    opportunity: SourceOpportunity,
    parsed_results: list[dict[str, Any]],
    source_portal: str = "",
) -> DeepExtractedFields:
    text = "\n".join(str(item.get("text", "")) for item in parsed_results)
    tables: list[Any] = []
    for item in parsed_results:
        tables.extend(item.get("tables", []) or [])

    fields = DeepExtractedFields(
        buyer_organisation=opportunity.buyer_name,
        tender_id=opportunity.external_reference,
        bid_number=opportunity.external_reference,
        title=opportunity.opportunity_title,
        workflow_type=opportunity.workflow_type,
        source_portal=source_portal or opportunity.source_name,
        source_url=opportunity.source_url,
        product_or_service=opportunity.product_or_service,
        tender_value_inr=opportunity.estimated_value_inr,
        bid_end_date=opportunity.deadline_date,
    )

    for field, patterns in CRITICAL_FIELDS.items():
        if getattr(fields, field):
            fields.field_evidence[field] = {
                "value": getattr(fields, field),
                "confidence": 0.6,
                "evidence_file": opportunity.source_url,
                "page": "",
                "extraction_method": "listing",
                "review_required": True,
            }
            continue
        value, evidence = _first_match_with_evidence(parsed_results, patterns)
        setattr(fields, field, value)
        if evidence:
            fields.field_evidence[field] = evidence

    documents: list[str] = []
    for pattern in DOCUMENT_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.I):
            candidate = " ".join(match.group(1).split())[:160]
            if candidate and candidate not in documents:
                documents.append(candidate)
    fields.documents_required = documents[:20]
    fields.boq_items = _extract_boq_items(tables)
    if fields.boq_items:
        fields.field_evidence["boq_items"] = {
            "value": f"{len(fields.boq_items)} item(s)",
            "confidence": 0.86,
            "evidence_file": next((item.get("source_path", "") for item in parsed_results if item.get("tables")), ""),
            "page": "",
            "extraction_method": "table_classifier",
            "review_required": False,
        }

    important_clauses = []
    for label, pattern in {
        "penalty": r"(.{0,40}(?:penalt(?:y|ies)|liquidated damages).{0,160})",
        "payment": r"(.{0,40}payment.{0,160})",
        "delivery": r"(.{0,40}delivery.{0,160})",
    }.items():
        match = re.search(pattern, text, flags=re.I | re.S)
        if match:
            important_clauses.append({"type": label, "text": " ".join(match.group(1).split())[:240]})
    fields.important_clauses = important_clauses

    fields.risk_flags = [label for label, pattern in RISK_WORDS.items() if re.search(pattern, text, flags=re.I)]
    missing = []
    for field in [
        "bid_end_date",
        "emd_amount_inr",
        "tender_value_inr",
        "turnover_requirement",
        "past_experience_requirement",
        "buyer_organisation",
        "delivery_location",
        "payment_terms",
    ]:
        value = getattr(fields, field)
        if not value:
            missing.append(field)
    if not fields.boq_items:
        missing.append("boq_items")
    if not fields.documents_required:
        missing.append("documents_required")
    fields.missing_fields = missing

    total = 10
    present = total - len(set(missing))
    fields.confidence_score = max(0, min(95, int((present / total) * 100)))
    return fields
