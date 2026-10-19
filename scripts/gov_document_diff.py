#!/usr/bin/env python3
"""Diff two cited GOV deep-read reports and safely hold stale readiness.

The helper is deliberately internal-only.  It compares structured reports that
already passed the GOV deep-read contract, materializes a human-readable
document/corrigendum diff, and can append an event-ledger-backed readiness
hold.  It never contacts a portal, supplier, buyer, or any external service.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

try:
    from scripts.event_ledger import append_event
    from scripts.gov_deep_read_contract import clean_text, validate_report
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from event_ledger import append_event  # type: ignore
    from gov_deep_read_contract import clean_text, validate_report  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE_REPORT_ROOT = PROJECT_ROOT / "outputs" / "case_reports"
DEFAULT_MASTER_CASES_PATH = PROJECT_ROOT / "data" / "master_cases.csv"
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"


# Keep the stage order aligned with the GOV DAG rather than relying on
# alphabetical ordering in owner-facing artifacts.
STAGE_ORDER = [
    "fast_kill",
    "fast_kill_critic",
    "deep_read",
    "supplier",
    "pricing",
    "compliance",
    "artifacts",
    "approval",
    "execution",
    "evaluation_award",
    "delivery_payment",
    "learning",
]

ALL_DOWNSTREAM = STAGE_ORDER[2:]
INVALIDATION_BY_CATEGORY = {
    "deadline": STAGE_ORDER,
    "eligibility": STAGE_ORDER,
    "boq": ALL_DOWNSTREAM,
    "price": ["supplier", "pricing", "compliance", "artifacts", "approval", "execution"],
    "delivery": ["supplier", "pricing", "compliance", "artifacts", "approval", "execution"],
    "financial_security": ["pricing", "artifacts", "approval", "execution"],
    "submission": ["artifacts", "approval", "execution"],
    "contractual": ["pricing", "compliance", "artifacts", "approval", "execution"],
    "corrigenda": ALL_DOWNSTREAM,
    "source_document": ALL_DOWNSTREAM,
    "other": ["deep_read", "supplier", "pricing", "compliance", "artifacts", "approval", "execution"],
}

FACT_CATEGORY = {
    "deadline_date": "deadline",
    "eligibility": "eligibility",
    "turnover": "eligibility",
    "experience": "eligibility",
    "oem": "eligibility",
    "emd": "financial_security",
    "pbg": "financial_security",
    "delivery": "delivery",
    "payment": "delivery",
    "required_documents": "submission",
    "bid_number": "submission",
    "penalties": "contractual",
    "evaluation_method": "contractual",
    "reverse_auction": "contractual",
    "inspection": "contractual",
    "warranty": "contractual",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def today_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _canonical(value: Any) -> str:
    """Make comparison stable without treating whitespace as a clause change."""
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, dict):
        return json.dumps(
            {str(key): _canonical(child) for key, child in value.items()},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    if isinstance(value, list):
        return json.dumps([_canonical(child) for child in value], ensure_ascii=False, separators=(",", ":"))
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fact_semantics(fact: Any) -> dict[str, Any]:
    if not isinstance(fact, dict):
        return {"status": "NOT_RECORDED", "value": "", "reason": ""}
    return {
        "status": clean_text(fact.get("status")).upper(),
        "value": fact.get("value", ""),
        "reason": fact.get("reason", ""),
    }


def _citation_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _unique_citations(*values: Any) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for value in values:
        for citation in _citation_list(value):
            stable = _canonical(citation)
            if stable not in seen:
                seen.add(stable)
                result.append(citation)
    return result


def _category_for_fact(key: str) -> str:
    normalized = key.casefold().replace("-", "_").replace(" ", "_")
    if normalized in FACT_CATEGORY:
        return FACT_CATEGORY[normalized]
    if any(token in normalized for token in ("price", "rate", "cost", "value")):
        return "price"
    if any(token in normalized for token in ("submit", "document", "bid_", "portal")):
        return "submission"
    if any(token in normalized for token in ("delivery", "dispatch", "payment", "supply")):
        return "delivery"
    if any(token in normalized for token in ("eligib", "turnover", "experience", "oem", "certif")):
        return "eligibility"
    return "other"


def _change(field: str, category: str, before: Any, after: Any, citations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "field": field,
        "category": category,
        "before": before,
        "after": after,
        "citations": citations,
    }


def _source_fingerprints(report: dict[str, Any]) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for document in report.get("source_documents", []):
        if not isinstance(document, dict):
            continue
        values.append(
            {
                "document_type": clean_text(document.get("document_type")),
                "sha256": clean_text(document.get("sha256")).lower(),
                "source_path": clean_text(document.get("source_path")),
                "source_url": clean_text(document.get("source_url")),
            }
        )
    return sorted(values, key=lambda item: (item["document_type"], item["sha256"], item["source_path"]))


def _report_citations(report: dict[str, Any]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for document in report.get("source_documents", []):
        if isinstance(document, dict):
            citations.append(
                {
                    "source_path": clean_text(document.get("source_path")),
                    "source_url": clean_text(document.get("source_url")),
                    "page": 1,
                    "section": clean_text(document.get("document_type")) or "source document",
                }
            )
    return citations


def _semantic_after_digest(report: dict[str, Any]) -> str:
    payload = {
        "case_id": report.get("case_id"),
        "facts": {key: _fact_semantics(value) for key, value in sorted((report.get("facts") or {}).items())},
        "boq_lines": report.get("boq_lines", []),
        "corrigenda": report.get("corrigenda", []),
        "source_documents": _source_fingerprints(report),
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _validate_input_reports(before: dict[str, Any], after: dict[str, Any]) -> None:
    before_errors = validate_report(before)
    after_errors = validate_report(after)
    if before_errors:
        raise ValueError("Invalid before GOV deep read: " + "; ".join(before_errors))
    if after_errors:
        raise ValueError("Invalid after GOV deep read: " + "; ".join(after_errors))
    if clean_text(before.get("case_id")) != clean_text(after.get("case_id")):
        raise ValueError("Before and after GOV deep reads must use the same case_id")


def compare_reports(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Return only substantive report differences and their safe hold scope."""
    _validate_input_reports(before, after)
    changes: list[dict[str, Any]] = []
    before_facts = before.get("facts", {})
    after_facts = after.get("facts", {})
    for key in sorted(set(before_facts) | set(after_facts)):
        old_fact = before_facts.get(key)
        new_fact = after_facts.get(key)
        old_semantics = _fact_semantics(old_fact)
        new_semantics = _fact_semantics(new_fact)
        if _canonical(old_semantics) != _canonical(new_semantics):
            changes.append(
                _change(
                    key,
                    _category_for_fact(key),
                    old_semantics,
                    new_semantics,
                    _unique_citations(
                        old_fact.get("citations") if isinstance(old_fact, dict) else [],
                        new_fact.get("citations") if isinstance(new_fact, dict) else [],
                    ),
                )
            )

    if _canonical(before.get("boq_lines", [])) != _canonical(after.get("boq_lines", [])):
        changes.append(
            _change(
                "boq_lines",
                "boq",
                before.get("boq_lines", []),
                after.get("boq_lines", []),
                _unique_citations(
                    *[line.get("citations", []) for line in before.get("boq_lines", []) if isinstance(line, dict)],
                    *[line.get("citations", []) for line in after.get("boq_lines", []) if isinstance(line, dict)],
                ),
            )
        )

    if _canonical(before.get("corrigenda", [])) != _canonical(after.get("corrigenda", [])):
        changes.append(
            _change(
                "corrigenda",
                "corrigenda",
                before.get("corrigenda", []),
                after.get("corrigenda", []),
                _unique_citations(
                    *[item.get("citations", []) for item in before.get("corrigenda", []) if isinstance(item, dict)],
                    *[item.get("citations", []) for item in after.get("corrigenda", []) if isinstance(item, dict)],
                ),
            )
        )

    before_sources = _source_fingerprints(before)
    after_sources = _source_fingerprints(after)
    if _canonical(before_sources) != _canonical(after_sources):
        changes.append(
            _change(
                "source_documents",
                "source_document",
                before_sources,
                after_sources,
                _unique_citations(_report_citations(before), _report_citations(after)),
            )
        )

    categories = {str(change["category"]) for change in changes}
    invalidated = {
        stage
        for category in categories
        for stage in INVALIDATION_BY_CATEGORY.get(category, INVALIDATION_BY_CATEGORY["other"])
    }
    invalidate_stages = [stage for stage in STAGE_ORDER if stage in invalidated]
    changed_fields = [str(change["field"]) for change in changes]
    corr_hash = _semantic_after_digest(after)
    citations = _unique_citations(*[change["citations"] for change in changes], _report_citations(after))
    summary = (
        "No substantive clause change detected."
        if not changed_fields
        else "Changed tender/corrigendum fields: " + ", ".join(changed_fields) + "."
    )
    return {
        "schema_version": "gov_document_diff.v1",
        "case_id": clean_text(after["case_id"]),
        "workflow_type": "GOV",
        "generated_at": now_iso(),
        "corrigendum_hash": corr_hash,
        "changes": changes,
        "changed_fields": changed_fields,
        "invalidate_stages": invalidate_stages,
        "case_updates": {
            "corrigenda_status": "CHANGED_REVIEW_REQUIRED" if changes else "",
            "corrigenda_summary": summary,
            "deep_read_done": "FALSE" if changes else "",
            "supplier_search_done": "FALSE" if changes else "",
            "pricing_done": "FALSE" if changes else "",
        },
        "citations": citations,
        "review_required": bool(changes),
        "external_actions_executed": False,
    }


def _display(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = clean_text(text).replace("|", "\\|")
    return text[:2000] + ("…" if len(text) > 2000 else "")


def _citation_text(citations: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for citation in citations:
        source = clean_text(citation.get("source_path")) or clean_text(citation.get("source_url"))
        page = clean_text(citation.get("page"))
        section = clean_text(citation.get("section"))
        if not source:
            continue
        item = f"{source}:p.{page}" if page else source
        if section:
            item += f" ({section})"
        parts.append(item)
    return "; ".join(dict.fromkeys(parts)) or "No page/source citation supplied"


def render_markdown(diff: dict[str, Any]) -> str:
    lines = [
        f"# GOV Document / Corrigendum Diff — {diff['case_id']}",
        "",
        f"- Schema: `{diff['schema_version']}`",
        f"- Generated at: `{diff['generated_at']}`",
        f"- Correction fingerprint: `{diff['corrigendum_hash']}`",
        f"- Review required: `{str(diff['review_required']).lower()}`",
        "- External actions executed: `false`",
        "",
        "## Changes",
        "",
    ]
    if not diff["changes"]:
        lines.append("- No substantive structured clause changes were detected.")
    for change in diff["changes"]:
        lines.extend(
            [
                f"### {change['field']} ({change['category']})",
                "",
                f"- Before: {_display(change['before'])}",
                f"- After: {_display(change['after'])}",
                f"- Evidence: {_citation_text(change['citations'])}",
                "",
            ]
        )
    lines.extend(["## Readiness invalidation", ""])
    if diff["invalidate_stages"]:
        lines.append("The following stages are stale until the changed evidence is reviewed and re-run:")
        lines.extend(f"- `{stage}`" for stage in diff["invalidate_stages"])
    else:
        lines.append("- No stage invalidation was generated.")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is an internal evidence diff and readiness hold. It does not certify eligibility, compliance, pricing, origin, delivery, or submission; it does not submit, upload, contact, pay, or use DSC.",
            "",
        ]
    )
    return "\n".join(lines)


def _safe_timestamp(value: str) -> str:
    compact = re.sub(r"[^0-9]", "", value)
    return compact[:14] or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")


def write_document_diff(diff: dict[str, Any], *, output_dir: Path) -> Path:
    case_id = clean_text(diff.get("case_id"))
    if not case_id:
        raise ValueError("Diff case_id is required")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"document_diff_{_safe_timestamp(str(diff.get('generated_at') or ''))}.md"
    if path.exists():
        path = output_dir / f"document_diff_{_safe_timestamp(str(diff.get('generated_at') or ''))}_{str(diff.get('corrigendum_hash', ''))[:8]}.md"
    path.write_text(render_markdown(diff), encoding="utf-8")
    return path


def _load_case_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(f"Master Case Register not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_case_rows(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in headers} for row in rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _event_citations(diff: dict[str, Any], report_path: Path) -> list[str]:
    citations = [str(report_path)]
    for citation in diff.get("citations", []):
        if not isinstance(citation, dict):
            continue
        for key in ("source_path", "source_url"):
            value = clean_text(citation.get(key))
            if value:
                citations.append(value)
    return list(dict.fromkeys(citations))


def apply_invalidation(
    diff: dict[str, Any],
    *,
    report_path: Path,
    master_cases_path: Path = DEFAULT_MASTER_CASES_PATH,
    events_path: Path = DEFAULT_EVENTS_PATH,
    actor: str = "gov_document_diff",
) -> dict[str, Any]:
    """Append the canonical hold event before changing its CSV projection."""
    if not diff.get("review_required") or not diff.get("changes"):
        raise ValueError("Cannot apply an invalidation when no substantive report change was found")
    case_id = clean_text(diff.get("case_id"))
    if not case_id:
        raise ValueError("Diff case_id is required")
    headers, rows = _load_case_rows(master_cases_path)
    if "case_id" not in headers:
        raise ValueError("Master Case Register requires a case_id column")
    if not all(field in headers for field in diff["case_updates"]):
        missing = sorted(field for field in diff["case_updates"] if field not in headers)
        raise ValueError("Master Case Register lacks required corrigendum fields: " + ", ".join(missing))

    matching = [row for row in rows if row.get("case_id") == case_id]
    if len(matching) != 1:
        raise ValueError(f"Expected exactly one Master Case row for {case_id}; found {len(matching)}")
    updates = {key: str(value) for key, value in diff["case_updates"].items()}
    updates["updated_at"] = today_iso()
    prior_status = clean_text(matching[0].get("status")) or "UNKNOWN"
    updates["corrigenda_summary"] = (
        f"{diff['case_updates']['corrigenda_summary']} Prior stage {prior_status} is held pending re-review. "
        f"Diff: {report_path}."
    )
    payload = {
        "corrigendum_hash": str(diff["corrigendum_hash"]),
        "updates": updates,
        "diff_report_path": str(report_path),
        "changed_fields": list(diff["changed_fields"]),
        "invalidate_stages": list(diff["invalidate_stages"]),
    }
    event = append_event(
        "case.updated_from_corrigendum",
        actor,
        case_id=case_id,
        object_type="case",
        object_id=case_id,
        source="gov_document_diff",
        payload=payload,
        citations=_event_citations(diff, report_path),
        idempotency_key=f"gov-corrigendum-invalidation:{case_id}:{diff['corrigendum_hash']}",
        events_file=events_path,
    )
    for row in rows:
        if row.get("case_id") == case_id:
            row.update(updates)
    _write_case_rows(master_cases_path, headers, rows)
    return {
        "case_id": case_id,
        "event_id": str(event["event_id"]),
        "corrigendum_hash": str(diff["corrigendum_hash"]),
        "projection_updated": True,
        "external_actions_executed": False,
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, help="Prior validated GOV deep-read JSON")
    parser.add_argument("--after", required=True, help="Current validated GOV deep-read JSON")
    parser.add_argument("--output-dir", default="", help="Directory for the internal Markdown diff")
    parser.add_argument("--write", action="store_true", help="Write the internal Markdown diff only")
    parser.add_argument("--apply", action="store_true", help="Write the diff, append the hold event, and update the local projection")
    parser.add_argument("--master-cases", default=str(DEFAULT_MASTER_CASES_PATH))
    parser.add_argument("--events", default=str(DEFAULT_EVENTS_PATH))
    parser.add_argument("--actor", default="gov_document_diff")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    before_path = Path(args.before).expanduser()
    after_path = Path(args.after).expanduser()
    if not before_path.is_absolute():
        before_path = PROJECT_ROOT / before_path
    if not after_path.is_absolute():
        after_path = PROJECT_ROOT / after_path
    diff = compare_reports(_load_json(before_path), _load_json(after_path))
    payload: dict[str, Any] = {
        "status": "CHANGED_REVIEW_REQUIRED" if diff["review_required"] else "NO_SUBSTANTIVE_CHANGE",
        "mode": "apply" if args.apply else "write" if args.write else "dry_run",
        "case_id": diff["case_id"],
        "changed_fields": diff["changed_fields"],
        "invalidate_stages": diff["invalidate_stages"],
        "external_actions_executed": False,
    }
    if args.write or args.apply:
        output_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_CASE_REPORT_ROOT / diff["case_id"]
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        report_path = write_document_diff(diff, output_dir=output_dir)
        payload["report_path"] = str(report_path)
        if args.apply:
            master_cases_path = Path(args.master_cases).expanduser()
            events_path = Path(args.events).expanduser()
            if not master_cases_path.is_absolute():
                master_cases_path = PROJECT_ROOT / master_cases_path
            if not events_path.is_absolute():
                events_path = PROJECT_ROOT / events_path
            payload.update(
                apply_invalidation(
                    diff,
                    report_path=report_path,
                    master_cases_path=master_cases_path,
                    events_path=events_path,
                    actor=args.actor,
                )
            )
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else f"GOV document diff: {payload}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
