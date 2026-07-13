#!/usr/bin/env python3
"""Generate approval card HTML and structured JSON files from the approval register."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
from pathlib import Path

try:
    from approval_lifecycle import approval_timeout_at as calculate_approval_timeout_at
    from codex_bid_pack_contract import verify_bid_pack_approval_ready
    from codex_export_quote_pack_contract import verify_export_quote_pack_approval_ready
    from event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover - package import path used by pytest
    from scripts.approval_lifecycle import approval_timeout_at as calculate_approval_timeout_at
    from scripts.codex_bid_pack_contract import verify_bid_pack_approval_ready
    from scripts.codex_export_quote_pack_contract import verify_export_quote_pack_approval_ready
    from scripts.event_ledger import append_event

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


def text_value(value) -> str:
    return str(value if value is not None else "").strip()


def approval_output_paths(approval: dict, case_id: str) -> tuple[Path, Path]:
    configured = text_value(approval.get("approval_card_path"))
    html_path = PROJECT_ROOT / configured if configured else OUTPUT_DIR / f"{case_id}_approval_card.html"
    try:
        html_path.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"Approval card path escapes project root: {html_path}") from exc
    return html_path, html_path.with_suffix(".json")


def approval_options() -> list[str]:
    return ["Approve", "Reject", "Ask Changes"]


def approval_timing(approval: dict) -> tuple[str, str]:
    requested_at = text_value(approval.get("requested_at")) or text_value(approval.get("created_at"))
    if not requested_at:
        requested_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    timeout_at = text_value(approval.get("approval_timeout_at")) or calculate_approval_timeout_at(requested_at)
    return requested_at, timeout_at


def approval_scope(approval: dict, case: dict) -> dict[str, str]:
    action = get_action(approval)
    return {
        "case_id": text_value(approval.get("case_id") or case.get("case_id")),
        "workflow_type": text_value(approval.get("workflow_type") or case.get("workflow_type") or "UNKNOWN"),
        "proposed_action": action,
        "business_object": text_value(case.get("buyer_name") or case.get("opportunity_title") or action),
        "amount_or_price": get_amount(approval, case),
        "external_party": text_value(case.get("buyer_name")),
    }


def approval_scope_hash(approval: dict, case: dict) -> str:
    serialized = json.dumps(approval_scope(approval, case), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def expected_benefit_text(approval: dict) -> str:
    return (
        text_value(approval.get("expected_benefit"))
        or text_value(approval.get("notes"))
        or "Owner can make a documented approval decision with an audit trail before any gated external action proceeds."
    )


def concrete_risk_text(approval: dict, case: dict) -> str:
    if text_value(approval.get("concrete_risk")):
        return text_value(approval.get("concrete_risk"))

    action = get_action(approval).lower()
    case_id = approval.get("case_id") or case.get("case_id") or "this case"
    if "supplier" in action and ("quote" in action or "rfq" in action or "clarification" in action):
        return (
            f"Supplier outreach for {case_id} is externally visible and may create commercial expectations. "
            "Supplier replies may include price, payment, MOQ, or delivery terms that are not approved, and no PO, "
            "payment, final price, delivery promise, HSN/ITC-HS confirmation, origin claim, buyer message, bid, or submission is authorized by this card."
        )
    if "export_quotation" in action or "buyer_rfq_reply" in action or "quotation" in action:
        return (
            f"A buyer-facing quotation or reply for {case_id} can be treated as a commercial price/delivery signal. "
            "If buyer proof, supplier quote proof, final price, payment terms, delivery terms, HSN/ITC-HS, or origin evidence is incomplete, the external message could be inaccurate or create an unintended commitment."
        )
    if "buyer_introductory_outreach" in action:
        return (
            f"First-contact outreach for {case_id} is externally visible and is based on catalogue fit, not a confirmed RFQ. "
            "The contact may be general rather than a buying contact, and the recipient may decline or opt out. "
            "The message must not imply confirmed demand, supplier availability, price, delivery, certification, classification, or origin."
        )
    if "submit" in action or "upload" in action or "dsc" in action or "emd" in action or "payment" in action or "purchase_order" in action:
        return (
            f"The requested action for {case_id} can create legal, financial, portal, or signature consequences that may be difficult to reverse if evidence, documents, or owner intent are wrong."
        )
    return (
        f"The approval-gated action for {case_id} may create external, financial, legal, or operational consequences if performed on incomplete evidence or beyond the approved scope."
    )


def recovery_rollback_text(approval: dict, case: dict) -> str:
    existing = text_value(approval.get("recovery_rollback_path")) or text_value(approval.get("recovery_path"))
    if existing:
        return existing

    action = get_action(approval).lower()
    case_id = approval.get("case_id") or case.get("case_id") or "this case"
    if "supplier" in action and ("quote" in action or "rfq" in action or "clarification" in action):
        return (
            f"If rejected or ask-changes, keep {case_id} internal-only and do not contact suppliers. "
            "If already sent under a valid approval, stop follow-ups, log the receipt, and require fresh owner approval before any cancellation note, PO, payment, final price, delivery, HSN/ITC-HS, origin, buyer message, bid, or submission."
        )
    if "export_quotation" in action or "buyer_rfq_reply" in action or "quotation" in action:
        return (
            f"If rejected or ask-changes, keep the quotation/reply for {case_id} as an internal draft and mark the card superseded or changes-requested. "
            "If a message was already sent under a valid approval, log a correction/withdrawal plan and obtain fresh owner approval before any external correction, final price, delivery, payment, HSN/ITC-HS, origin, invoice, PO, or follow-up commitment."
        )
    if "buyer_introductory_outreach" in action:
        return (
            f"If rejected or ask-changes, keep {case_id} and its draft internal-only. If sent under valid approval, "
            "log the Gmail-plugin receipt, honor any opt-out immediately, and require fresh approval before any follow-up, "
            "catalogue, sample, price, delivery, payment, certification, classification, or origin response."
        )
    if "submit" in action or "upload" in action or "dsc" in action or "emd" in action or "payment" in action or "purchase_order" in action:
        return (
            f"If rejected or ask-changes, do not execute the gated action for {case_id}; keep artifacts internal and issue a revised card. "
            "If execution has already occurred under valid approval, preserve receipts, notify the owner, and follow the portal/bank/legal rollback path before any further external step."
        )
    return (
        f"If rejected or ask-changes, keep {case_id} internal-only, mark the card superseded or changes-requested, and regenerate a corrected approval card before any external action."
    )


def missing_items_list(approval: dict, case: dict) -> list[str]:
    values = []
    if approval.get("changes_requested"):
        values.append(approval["changes_requested"])
    if not approval.get("approval_card_path"):
        values.append("Approval card path was missing before generation.")
    if not approval.get("expected_benefit"):
        values.append("Expected benefit was derived from approval notes because the register lacks a separate expected_benefit field.")
    if not approval.get("concrete_risk"):
        values.append("Concrete risk was generated from approval action family and case evidence because the register lacks a custom concrete_risk field.")
    if not approval.get("recovery_rollback_path") and not approval.get("recovery_path"):
        values.append("Recovery/rollback path was generated from approval action family because the register lacks a custom recovery_rollback_path field.")
    if case.get("workflow_type") == "EXPORT" and case.get("hsn_itchs_candidate"):
        values.append("HSN/ITC-HS is candidate only until expert approval.")
    return values or ["None recorded in local register."]


def missing_items(approval: dict, case: dict) -> str:
    return "\n".join(f'<div class="missing-item">{esc(item)}</div>' for item in missing_items_list(approval, case))


def gov_bid_pack_ready(approval: dict, case: dict) -> tuple[bool, list[str]]:
    """GOV approval cards require a fresh, recorded internal pack verification."""
    workflow = text_value(approval.get("workflow_type") or case.get("workflow_type")).upper()
    if workflow != "GOV":
        return True, []
    case_id = text_value(approval.get("case_id") or case.get("case_id"))
    if not case_id:
        return False, ["GOV approval requires case_id for bid-pack verification"]
    pack_root = PROJECT_ROOT / "outputs" / "bid_packs" / case_id
    report = verify_bid_pack_approval_ready(
        pack_root / "artifact_manifest.json",
        pack_root / "verification_receipt.json",
        expected_case_id=case_id,
    )
    return report["status"] == "PASS", list(report.get("errors") or [])


def requires_export_quote_pack(approval: dict, case: dict) -> bool:
    """Return whether this card would authorize a buyer-facing commercial quote."""
    workflow = text_value(approval.get("workflow_type") or case.get("workflow_type")).upper()
    if workflow != "EXPORT":
        return False
    action = get_action(approval).casefold().replace(" ", "_")
    return any(marker in action for marker in ("export_quotation", "buyer_rfq_reply", "send_quotation"))


def export_quote_pack_ready(approval: dict, case: dict) -> tuple[bool, list[str]]:
    """Buyer-facing EXPORT quote cards require a fresh internal quote-pack receipt."""
    if not requires_export_quote_pack(approval, case):
        return True, []
    case_id = text_value(approval.get("case_id") or case.get("case_id"))
    if not case_id:
        return False, ["EXPORT quotation approval requires case_id for quote-pack verification"]
    pack_root = PROJECT_ROOT / "outputs" / "export_quote_packs" / case_id
    report = verify_export_quote_pack_approval_ready(
        pack_root / "artifact_manifest.json",
        pack_root / "verification_receipt.json",
        expected_case_id=case_id,
    )
    return report["status"] == "PASS", list(report.get("errors") or [])


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
    workflow = text_value(approval.get("workflow_type") or case.get("workflow_type")).upper()
    case_id = text_value(approval.get("case_id") or case.get("case_id"))
    if workflow == "GOV" and case_id:
        sources.extend(
            [
                f"outputs/bid_packs/{case_id}/artifact_manifest.json",
                f"outputs/bid_packs/{case_id}/verification_receipt.json",
                f"receipts/plugin_runs/{case_id}_bid_pack.json",
            ]
        )
    if workflow == "EXPORT" and case_id and requires_export_quote_pack(approval, case):
        sources.extend(
            [
                f"outputs/export_quote_packs/{case_id}/artifact_manifest.json",
                f"outputs/export_quote_packs/{case_id}/verification_receipt.json",
                f"receipts/plugin_runs/{case_id}_export_quote_pack.json",
            ]
        )
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
    benefit = expected_benefit_text(approval)
    risk = concrete_risk_text(approval, case)
    recovery = recovery_rollback_text(approval, case)
    confidence = approval.get("confidence_score") or "60"
    business_object = case.get("buyer_name") or case.get("opportunity_title") or action
    requested_at, timeout_at = approval_timing(approval)
    scope_hash = approval_scope_hash(approval, case)
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
        "{{REQUESTED_AT}}": esc(requested_at),
        "{{APPROVAL_TIMEOUT_AT}}": esc(timeout_at),
        "{{SCOPE_HASH}}": esc(scope_hash),
    }
    html_text = template
    for placeholder, value in replacements.items():
        html_text = html_text.replace(placeholder, value)
    return html_text


def structured_card(approval: dict, case: dict, html_path: Path, json_path: Path) -> dict:
    workflow = approval.get("workflow_type") or case.get("workflow_type") or "UNKNOWN"
    action = get_action(approval)
    business_object = case.get("buyer_name") or case.get("opportunity_title") or action
    benefit = expected_benefit_text(approval)
    risk = concrete_risk_text(approval, case)
    recovery = recovery_rollback_text(approval, case)
    decisions = approval_options()
    requested_at, timeout_at = approval_timing(approval)
    scope = approval_scope(approval, case)
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
        "expected_benefit": benefit,
        "concrete_risk": risk,
        "recovery_rollback_path": recovery,
        "recovery_path": recovery,
        "documents_sources_used": documents_sources_list(approval, case),
        "confidence_score": max(0, min(100, confidence)),
        "missing_information": missing_items_list(approval, case),
        "approval_options": decisions,
        "allowed_decisions": decisions,
        "approval_status": approval.get("approval_status", ""),
        "requested_at": requested_at,
        "approval_timeout_at": timeout_at,
        "scope": scope,
        "scope_hash": approval_scope_hash(approval, case),
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "created_by": "generate_approval_cards",
        "html_path": rel(html_path),
        "json_path": rel(json_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate approval cards from approvals_receipts.csv")
    parser.add_argument("--case-id", help="Generate one case only")
    parser.add_argument("--approval-id", help="Generate one approval row only")
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
    blocked = 0
    for approval in approvals:
        case_id = approval.get("case_id", "")
        if args.case_id and case_id != args.case_id:
            continue
        if args.approval_id and approval.get("approval_id") != args.approval_id:
            continue
        if not case_id:
            skipped += 1
            continue
        case = cases.get(case_id, {})
        pack_ready, pack_errors = gov_bid_pack_ready(approval, case)
        pack_label = "GOV bid-pack" if text_value(approval.get("workflow_type") or case.get("workflow_type")).upper() == "GOV" else "EXPORT quote-pack"
        if pack_ready:
            pack_ready, pack_errors = export_quote_pack_ready(approval, case)
        if not pack_ready:
            blocked += 1
            print(f"Blocked {pack_label} approval card for {case_id}: {'; '.join(pack_errors)}")
            continue
        path, json_path = approval_output_paths(approval, case_id)
        if path.exists() and (not args.json or json_path.exists()) and not args.overwrite:
            skipped += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
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
    print(f"Blocked by governed pack verification: {blocked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
