#!/usr/bin/env python3
"""Generate approval card HTML and structured JSON files from the approval register."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
from pathlib import Path

from event_ledger import append_event

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATE = PROJECT_ROOT / "templates" / "approval_card.html"
APPROVALS = DATA_DIR / "approvals_receipts.csv"
MASTER_CASES = DATA_DIR / "master_cases.csv"
OUTPUT_DIR = PROJECT_ROOT / "receipts" / "approvals"


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def get_action(approval: dict) -> str:
    return approval.get("proposed_action") or approval.get("action_approved") or "Approval required"


def get_amount(approval: dict, case: dict) -> str:
    workflow = approval.get("workflow_type") or case.get("workflow_type")
    if approval.get("amount_or_price"):
        return approval["amount_or_price"]
    if workflow == "EXPORT" and approval.get("amount_usd"):
        return f"${approval['amount_usd']}"
    if approval.get("amount_inr"):
        return f"₹{approval['amount_inr']}"
    if approval.get("amount_usd"):
        return f"${approval['amount_usd']}"
    if workflow == "EXPORT" and case.get("estimated_value_usd"):
        return f"${case['estimated_value_usd']}"
    if case.get("estimated_value_inr"):
        return f"₹{case['estimated_value_inr']}"
    if case.get("estimated_value_usd"):
        return f"${case['estimated_value_usd']}"
    return "N/A"


def days_left(case: dict) -> str:
    deadline = case.get("deadline_date", "")
    if not deadline:
        return "?"
    try:
        return str((dt.date.fromisoformat(deadline) - dt.date.today()).days)
    except ValueError:
        return "?"


def missing_items_list(approval: dict, case: dict) -> list[str]:
    values = []
    if approval.get("changes_requested"):
        values.append(approval["changes_requested"])
    if not approval.get("approval_card_path"):
        values.append("Approval card path was missing before generation.")
    if not approval.get("expected_benefit"):
        values.append("Expected benefit not fully quantified in approval register.")
    if not approval.get("concrete_risk"):
        values.append("Concrete risk not fully specified in approval register.")
    if case.get("workflow_type") == "EXPORT" and case.get("hsn_itchs_candidate"):
        values.append("HSN/ITC-HS is candidate only until expert approval.")
    return values or ["None recorded in local register."]


def missing_items(approval: dict, case: dict) -> str:
    return "\n".join(f'<div class="missing-item">{esc(item)}</div>' for item in missing_items_list(approval, case))


def documents_sources_list(approval: dict, case: dict) -> list[str]:
    sources = [
        "data/approvals_receipts.csv",
        "data/master_cases.csv",
        "config/approval_policy.yaml",
    ]
    if approval.get("approval_card_path"):
        sources.append(approval["approval_card_path"])
    if case.get("source_url"):
        sources.append(case["source_url"])
    return sources


def documents_sources(approval: dict, case: dict) -> str:
    return "<br>\n".join(esc(source) for source in documents_sources_list(approval, case))


def render_card(template: str, approval: dict, case: dict) -> str:
    case_id = approval.get("case_id", "")
    workflow = approval.get("workflow_type") or case.get("workflow_type") or "UNKNOWN"
    action = get_action(approval)
    amount = get_amount(approval, case)
    deadline = case.get("deadline_date") or "N/A"
    days = days_left(case) if deadline != "N/A" else "N/A"
    days_suffix = f" [{days} days]" if days != "N/A" else ""
    benefit = approval.get("expected_benefit") or approval.get("notes") or "Benefit not fully quantified in approval register."
    risk = approval.get("concrete_risk") or "Risk note missing; ask changes before approving if this matters."
    recovery = approval.get("recovery_rollback_path") or "Recovery path missing; ask changes before approving if this matters."
    confidence = approval.get("confidence_score") or "60"
    business_object = case.get("buyer_name") or case.get("opportunity_title") or action
    replacements = {
        "{{CASE_ID}}": esc(case_id),
        "{{WORKFLOW_TYPE}}": esc(workflow),
        "{{DATE}}": esc(dt.date.today().isoformat()),
        "{{PROPOSED_ACTION}}": esc(action),
        "{{PROPOSED_ACTION_SHORT}}": esc(action.replace("_", " ")),
        "{{BUSINESS_OBJECT}}": esc(business_object),
        "{{AMOUNT}}": esc(amount),
        "{{DEADLINE}}": esc(deadline),
        "{{DAYS_LEFT}}": esc(days_left(case)),
        "{{DAYS_LEFT_SUFFIX}}": esc(days_suffix),
        "{{EXPECTED_BENEFIT}}": esc(benefit),
        "{{CONCRETE_RISK}}": esc(risk),
        "{{RECOVERY_PATH}}": esc(recovery),
        "{{CONFIDENCE_SCORE}}": esc(confidence),
        "{{MISSING_ITEMS}}": missing_items(approval, case),
        "{{DOCUMENTS_SOURCES}}": documents_sources(approval, case),
    }
    html_text = template
    for placeholder, value in replacements.items():
        html_text = html_text.replace(placeholder, value)
    return html_text


def structured_card(approval: dict, case: dict, html_path: Path, json_path: Path) -> dict:
    workflow = approval.get("workflow_type") or case.get("workflow_type") or "UNKNOWN"
    action = get_action(approval)
    business_object = case.get("buyer_name") or case.get("opportunity_title") or action
    try:
        confidence = int(float(approval.get("confidence_score") or 60))
    except ValueError:
        confidence = 60
    return {
        "approval_id": approval.get("approval_id", ""),
        "case_id": approval.get("case_id", ""),
        "workflow_type": workflow,
        "proposed_action": action,
        "business_object": business_object,
        "amount_or_price": get_amount(approval, case),
        "external_party": case.get("buyer_name", ""),
        "expected_benefit": approval.get("expected_benefit") or approval.get("notes") or "Benefit not fully quantified in approval register.",
        "concrete_risk": approval.get("concrete_risk") or "Risk note missing; ask changes before approving if this matters.",
        "recovery_path": approval.get("recovery_rollback_path") or "Recovery path missing; ask changes before approving if this matters.",
        "documents_sources_used": documents_sources_list(approval, case),
        "confidence_score": max(0, min(100, confidence)),
        "missing_information": missing_items_list(approval, case),
        "allowed_decisions": ["Approve", "Reject", "Ask Changes"],
        "approval_status": approval.get("approval_status", ""),
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "created_by": "generate_approval_cards",
        "html_path": rel(html_path),
        "json_path": rel(json_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate approval cards from approvals_receipts.csv")
    parser.add_argument("--case-id", help="Generate one case only")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing cards")
    parser.add_argument("--json", action="store_true", help="Also write structured JSON approval cards")
    parser.add_argument("--record-event", action="store_true", help="Append approval.card_created events for generated cards")
    args = parser.parse_args()

    approvals = load_csv(APPROVALS)
    cases = {row.get("case_id"): row for row in load_csv(MASTER_CASES)}
    template = TEMPLATE.read_text(encoding="utf-8")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated = 0
    skipped = 0
    for approval in approvals:
        case_id = approval.get("case_id", "")
        if args.case_id and case_id != args.case_id:
            continue
        if not case_id:
            skipped += 1
            continue
        path = OUTPUT_DIR / f"{case_id}_approval_card.html"
        json_path = OUTPUT_DIR / f"{case_id}_approval_card.json"
        if path.exists() and (not args.json or json_path.exists()) and not args.overwrite:
            skipped += 1
            continue
        case = cases.get(case_id, {})
        path.write_text(render_card(template, approval, case), encoding="utf-8")
        citations = [rel(path), "data/approvals_receipts.csv", "data/master_cases.csv"]
        if args.json:
            card = structured_card(approval, case, path, json_path)
            json_path.write_text(json.dumps(card, indent=2), encoding="utf-8")
            citations.append(rel(json_path))
        if args.record_event:
            append_event(
                "approval.card_created",
                "generate_approval_cards",
                case_id=case_id,
                object_type="approval",
                object_id=approval.get("approval_id", case_id),
                payload={"html_path": rel(path), "json_path": rel(json_path) if args.json else ""},
                citations=citations,
            )
        generated += 1

    print(f"Generated: {generated}")
    print(f"Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
