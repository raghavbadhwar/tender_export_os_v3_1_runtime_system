#!/usr/bin/env python3
"""Source-grounded TenderOS tender/RFQ and supplier quote extraction.

Local-only helper inspired by LangExtract principles: every extracted field keeps
an exact character span back to the source text plus a reviewable HTML artifact.
It does not submit bids, contact suppliers, mutate registers, or approve pricing.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "extraction_reviews"


@dataclass
class SourceSpan:
    start: int
    end: int
    line: int


@dataclass
class ExtractedField:
    value: Any
    source_text: str
    source_span: SourceSpan
    confidence: float
    extraction_method: str = "regex_source_span"
    review_required: bool = False


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset)) + 1


def _clean(value: str) -> str:
    return " ".join(value.strip().split()).rstrip(" .;")


def _match_field(text: str, patterns: Iterable[str], *, group: int = 1, confidence: float = 0.82, review_required: bool = False) -> ExtractedField | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I | re.M)
        if not match:
            continue
        start, end = match.span(group)
        raw = match.group(group)
        return ExtractedField(
            value=_clean(raw),
            source_text=text[start:end],
            source_span=SourceSpan(start=start, end=end, line=_line_for_offset(text, start)),
            confidence=confidence,
            review_required=review_required,
        )
    return None


def _field_dict(field: ExtractedField) -> dict[str, Any]:
    data = asdict(field)
    return data


def _extract_all_documents(text: str) -> ExtractedField | None:
    patterns = [
        r"(?:documents?\s*required|document\s*checklist|forms?\s*required)\s*[:\-]\s*([^\n]{4,260})",
        r"(?:submit|upload)\s+(?:the\s+)?([^\n]{4,180}(?:certificate|declaration|undertaking|form|license|licence))",
    ]
    field = _match_field(text, patterns, confidence=0.78, review_required=True)
    if not field:
        return None
    parts = [p.strip(" .;") for p in re.split(r",|;| and ", str(field.value)) if p.strip()]
    field.value = parts or field.value
    return field


def _extract_risk_flags(text: str) -> list[str]:
    rules = {
        "DSC_REQUIRED": r"\bDSC\b|digital\s*signature",
        "OEM_AUTH_REQUIRED": r"\bOEM\b|manufacturer'?s?\s*authorization|authorisation",
        "PAST_EXPERIENCE_REQUIRED": r"past\s*experience|similar\s*work|experience\s*certificate",
        "PERFORMANCE_SECURITY": r"performance\s*security|security\s*deposit",
        "PENALTY_CLAUSE": r"penalt(?:y|ies)|liquidated\s*damages",
    }
    return [label for label, pattern in rules.items() if re.search(pattern, text, flags=re.I)]


TENDER_PATTERNS: dict[str, list[str]] = {
    "bid_number": [r"(?:bid\s*number|bid\s*no\.?|tender\s*id|tender\s*no\.?)\s*[:\-]\s*([^\n]{3,80})"],
    "buyer_organisation": [r"(?:buyer\s*organisation|buyer\s*organization|buyer|department)\s*[:\-]\s*([^\n]{3,140})"],
    "tender_value": [r"(?:tender\s*value|estimated\s*value|contract\s*value)\s*[:\-]?\s*((?:INR|Rs\.?|₹)\s*[\d,]+(?:\.\d+)?)"],
    "emd_amount": [r"(?:emd|earnest\s*money)\s*[:\-]?\s*((?:INR|Rs\.?|₹)\s*[\d,]+(?:\.\d+)?)"],
    "bid_end_date": [r"(?:bid\s*end\s*date|closing\s*date|last\s*date|due\s*date)\s*[:\-]\s*([^\n]{4,100})"],
    "delivery_location": [r"(?:delivery\s*location|place\s*of\s*delivery|location)\s*[:\-]\s*([^\n]{3,140})"],
    "payment_terms": [r"(?:payment\s*terms|payment)\s*[:\-]\s*([^\n]{4,180})"],
    "boq_summary": [r"(?:boq|bill\s*of\s*quantit(?:y|ies))\s*[:\-]\s*([^\n]{4,220})"],
}


QUOTE_PATTERNS: dict[str, list[str]] = {
    "supplier": [r"(?:supplier|vendor|seller)\s*[:\-]\s*([^\n]{2,140})"],
    "product": [r"(?:product|item|material)\s*[:\-]\s*([^\n]{2,180})"],
    "unit_price": [r"(?:price|unit\s*price|rate)\s*[:\-]?\s*((?:INR|Rs\.?|₹)\s*[\d,]+(?:\.\d+)?)"],
    "moq": [r"(?:moq|minimum\s*order\s*quantity)\s*[:\-]\s*([^\n]{2,80})"],
    "lead_time": [r"(?:lead\s*time|delivery\s*time)\s*[:\-]\s*([^\n]{2,100})"],
    "gst": [r"(?:gst|tax)\s*[:\-]\s*([^\n]{2,80})"],
    "quote_validity": [r"(?:validity|valid\s*until)\s*[:\-]\s*([^\n]{2,100})"],
    "quote_proof": [r"(?:quote\s*proof|source|proof|attachment)\s*[:\-]\s*([^\n]{4,220})"],
}


def _base_result(kind: str, case_id: str, source_name: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "extraction_kind": kind,
        "source_name": source_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fields": {},
        "missing_fields": [],
        "risk_flags": [],
        "approval_gate": "INTERNAL_REVIEW_ONLY",
        "safety_note": "Local extraction only; no external send, bid submission, supplier commitment, final price, HSN/origin claim, payment, DSC use, or register mutation.",
    }


def extract_tender_evidence(text: str, *, case_id: str, source_name: str = "local_text") -> dict[str, Any]:
    result = _base_result("tender", case_id, source_name)
    fields: dict[str, Any] = {}
    for name, patterns in TENDER_PATTERNS.items():
        field = _match_field(text, patterns, review_required=name in {"payment_terms", "boq_summary"})
        if field:
            fields[name] = _field_dict(field)
    documents = _extract_all_documents(text)
    if documents:
        fields["documents_required"] = _field_dict(documents)
    required = ["bid_number", "buyer_organisation", "bid_end_date", "delivery_location", "payment_terms", "documents_required"]
    missing = [name for name in required if name not in fields]
    result["fields"] = fields
    result["missing_fields"] = missing
    result["risk_flags"] = _extract_risk_flags(text)
    result["confidence_score"] = int(max(0, min(95, (len(required) - len(missing)) / len(required) * 100)))
    result["evidence_level"] = "SOURCE_GROUNDED" if result["confidence_score"] >= 65 else "PARTIAL_SOURCE_GROUNDED"
    result["approval_gate"] = "DEEP_READ_REVIEW_REQUIRED" if missing or result["risk_flags"] else "READY_FOR_INTERNAL_DEEP_READ"
    return result


def _classify_quote(text: str, fields: dict[str, Any]) -> tuple[str, str]:
    lowered = text.lower()
    proof_text = str(fields.get("quote_proof", {}).get("value", "")).lower()
    combined = lowered + " " + proof_text
    indicative = any(term in combined for term in ["public listing", "listing only", "indiamart", "tradeindia", "marketplace", "catalog", "not a written quote", "indicative"])
    supplier_specific = any(term in combined for term in ["written quote", "quotation pdf", "email quote", "proforma", "supplier response", "signed quote"])
    if indicative:
        return "INDICATIVE_SIGNAL", "DO_NOT_USE_FOR_FINAL_PRICING"
    if supplier_specific and "quote_proof" in fields:
        return "SUPPLIER_SPECIFIC_QUOTE_PROOF", "INTERNAL_PRICING_REVIEW_ALLOWED"
    return "INSUFFICIENT_QUOTE_PROOF", "DO_NOT_USE_FOR_FINAL_PRICING"


def extract_quote_evidence(text: str, *, case_id: str, source_name: str = "local_text") -> dict[str, Any]:
    result = _base_result("quote", case_id, source_name)
    fields: dict[str, Any] = {}
    for name, patterns in QUOTE_PATTERNS.items():
        field = _match_field(text, patterns, review_required=name in {"unit_price", "quote_proof"})
        if field:
            fields[name] = _field_dict(field)
    required = ["supplier", "product", "unit_price", "moq", "lead_time", "quote_proof"]
    missing = [name for name in required if name not in fields]
    classification, gate = _classify_quote(text, fields)
    result["fields"] = fields
    result["missing_fields"] = missing
    result["quote_proof_classification"] = classification
    result["approval_gate"] = gate
    result["confidence_score"] = int(max(0, min(95, (len(required) - len(missing)) / len(required) * 100)))
    result["evidence_level"] = "SOURCE_GROUNDED" if result["confidence_score"] >= 65 else "PARTIAL_SOURCE_GROUNDED"
    return result


def _highlighted_source(text: str, spans: list[tuple[int, int]]) -> str:
    spans = sorted((max(0, a), min(len(text), b)) for a, b in spans if a < b)
    out: list[str] = []
    cursor = 0
    for start, end in spans:
        if start < cursor:
            continue
        out.append(html.escape(text[cursor:start]))
        out.append(f'<mark class="source-highlight">{html.escape(text[start:end])}</mark>')
        cursor = end
    out.append(html.escape(text[cursor:]))
    return "".join(out)


def render_review_html(result: dict[str, Any], source_text: str) -> str:
    spans: list[tuple[int, int]] = []
    for field in result.get("fields", {}).values():
        span = field.get("source_span", {}) if isinstance(field, dict) else {}
        if "start" in span and "end" in span:
            spans.append((int(span["start"]), int(span["end"])))
    highlighted = _highlighted_source(source_text, spans)
    rows = []
    for name, field in result.get("fields", {}).items():
        value = html.escape(json.dumps(field.get("value"), ensure_ascii=False) if not isinstance(field.get("value"), str) else field.get("value", ""))
        span = field.get("source_span", {})
        rows.append(f"<tr><td>{html.escape(name)}</td><td>{value}</td><td>line {span.get('line', '')}</td><td>{field.get('confidence', '')}</td><td>{field.get('review_required', '')}</td></tr>")
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>{html.escape(result.get('case_id', 'extraction'))} extraction review</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;line-height:1.45}}pre{{white-space:pre-wrap;background:#0f172a;color:#e2e8f0;padding:16px;border-radius:12px}}.source-highlight{{background:#fde68a;color:#111827;padding:1px 2px;border-radius:3px}}table{{border-collapse:collapse;width:100%;margin:16px 0}}td,th{{border:1px solid #cbd5e1;padding:8px;text-align:left}}.gate{{padding:10px;border-radius:8px;background:#eef2ff}}</style>
</head><body>
<h1>Extraction review — {html.escape(result.get('case_id', ''))}</h1>
<p class='gate'><strong>Kind:</strong> {html.escape(result.get('extraction_kind', ''))} · <strong>Gate:</strong> {html.escape(result.get('approval_gate', ''))} · <strong>Evidence:</strong> {html.escape(result.get('evidence_level', ''))}</p>
<h2>Fields</h2><table><thead><tr><th>Field</th><th>Value</th><th>Source</th><th>Confidence</th><th>Review?</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Highlighted source</h2><pre>{highlighted}</pre>
<h2>Raw JSON</h2><pre>{html.escape(json.dumps(result, indent=2, ensure_ascii=False))}</pre>
</body></html>"""


def write_outputs(result: dict[str, Any], source_text: str, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{result['case_id']}_{result['extraction_kind']}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    json_path = output_dir / f"{stem}.json"
    html_path = output_dir / f"{stem}.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path.write_text(render_review_html(result, source_text), encoding="utf-8")
    return {"json": str(json_path), "html": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract source-grounded TenderOS case evidence from local text")
    parser.add_argument("--input", required=True, help="Local text/markdown file to extract from")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--kind", choices=["tender", "quote"], required=True)
    parser.add_argument("--source-name", default="local_text")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    source_path = Path(args.input)
    text = source_path.read_text(encoding="utf-8", errors="replace")
    if args.kind == "tender":
        result = extract_tender_evidence(text, case_id=args.case_id, source_name=args.source_name or source_path.name)
    else:
        result = extract_quote_evidence(text, case_id=args.case_id, source_name=args.source_name or source_path.name)
    outputs = write_outputs(result, text, Path(args.output_dir))
    result["output_files"] = outputs
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Extraction {result['evidence_level']} {result['approval_gate']}")
        print(f"JSON: {outputs['json']}")
        print(f"HTML: {outputs['html']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
