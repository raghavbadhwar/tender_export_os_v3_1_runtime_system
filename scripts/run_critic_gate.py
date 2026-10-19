#!/usr/bin/env python3
"""Deterministic critic gate before high-confidence or approval-facing states."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    from scripts.quote_proof import classify_quote_proof, strict_quote_proofs
    from scripts.validate_case_readiness import evaluate_case
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from quote_proof import classify_quote_proof, strict_quote_proofs
    from validate_case_readiness import evaluate_case


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "critic_gate"

TARGET_STATUSES = {
    "PRICING_READY",
    "ARTIFACT_PRODUCTION",
    "APPROVAL_REQUIRED",
    "APPROVED",
}
FOUNDER_RECOMMENDED_MARKERS = {"FOUNDER_RECOMMENDED", "FOUNDER RECOMMENDED", "A+", "A_PLUS", "GRADE_A", "GRADE A"}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def safe_float(value: Any) -> float:
    try:
        return float(str(value or "").replace(",", ""))
    except ValueError:
        return 0.0


def norm(value: Any) -> str:
    return str(value or "").strip()


def norm_upper(value: Any) -> str:
    return norm(value).upper()


def case_grade(case: dict[str, Any]) -> str:
    score = max(safe_float(case.get("score_gov")), safe_float(case.get("score_export")))
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    return ""


def is_target_case(case: dict[str, Any]) -> bool:
    status = norm_upper(case.get("status"))
    text = norm_upper(" ".join(str(case.get(key, "")) for key in ("notes", "execution_sub_status", "approval_status")))
    return status in TARGET_STATUSES or bool(case_grade(case)) or any(marker in text for marker in FOUNDER_RECOMMENDED_MARKERS)


def by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row.get(key, ""): row for row in rows if row.get(key)}


def rfq_for_case(case_id: str, rfqs: list[dict[str, str]]) -> dict[str, str]:
    for rfq in rfqs:
        if rfq.get("case_id") == case_id:
            return rfq
    return {}


def approvals_for_case(case_id: str, approvals: list[dict[str, str]]) -> list[dict[str, str]]:
    return [approval for approval in approvals if approval.get("case_id") == case_id]


def quote_rows_for_case(case_id: str, quotes: list[dict[str, str]]) -> list[dict[str, str]]:
    return [quote for quote in quotes if quote.get("case_id") == case_id]


def supplier_rows_for_quotes(quote_rows: list[dict[str, str]], suppliers: list[dict[str, str]]) -> list[dict[str, str]]:
    suppliers_by_id = by_key(suppliers, "supplier_id")
    suppliers_by_name = {norm_upper(row.get("supplier_name")): row for row in suppliers if row.get("supplier_name")}
    resolved = []
    for quote in quote_rows:
        supplier = suppliers_by_id.get(quote.get("supplier_id", "")) or suppliers_by_name.get(norm_upper(quote.get("supplier_name")))
        if supplier:
            resolved.append(supplier)
    return resolved


def review_case(
    case: dict[str, str],
    *,
    quotes: list[dict[str, str]],
    suppliers: list[dict[str, str]],
    approvals: list[dict[str, str]],
    rfqs: list[dict[str, str]],
) -> dict[str, Any]:
    case_id = case.get("case_id", "")
    status = norm_upper(case.get("status"))
    blockers: list[str] = []
    warnings: list[str] = []

    readiness = evaluate_case(case, quotes, approvals, rfqs)
    blockers.extend(readiness["blockers"])
    warnings.extend(readiness["warnings"])

    case_quotes = quote_rows_for_case(case_id, quotes)
    classifications = [classify_quote_proof(row) for row in case_quotes]
    strict_proofs = strict_quote_proofs(case_id, quotes)
    advanced = status in TARGET_STATUSES
    if advanced and len(strict_proofs) < 2:
        blockers.append(f"advanced state requires 2 strict supplier-specific quote proofs; found {len(strict_proofs)}")
    indicative_count = sum(1 for item in classifications if item["classification"] == "INDICATIVE_SIGNAL")
    if indicative_count:
        warnings.append(f"{indicative_count} indicative/marketplace quote signal(s) ignored as quote proof")

    proof_suppliers = supplier_rows_for_quotes(strict_proofs, suppliers)
    for supplier in proof_suppliers:
        if norm_upper(supplier.get("blacklisted")) == "TRUE":
            blockers.append(f"strict quote supplier is blacklisted: {supplier.get('supplier_id') or supplier.get('supplier_name')}")
        if norm_upper(supplier.get("watchlisted")) == "TRUE":
            warnings.append(f"strict quote supplier is watchlisted: {supplier.get('supplier_id') or supplier.get('supplier_name')}")

    if norm_upper(case.get("workflow_type")) == "EXPORT":
        rfq = rfq_for_case(case_id, rfqs)
        if advanced:
            if not rfq:
                blockers.append("export advanced state requires linked RFQ row")
            elif rfq.get("evidence_status") != "RFQ_VERIFIED" or rfq.get("rfq_stage") not in {"RFQ_VERIFIED", "READY_FOR_SUPPLIER_PROOF"}:
                blockers.append("export advanced state requires RFQ_VERIFIED buyer/RFQ evidence")
            if not case.get("hsn_itchs_candidate"):
                blockers.append("export advanced state requires draft HSN/ITC-HS candidate")
            if not case.get("export_policy"):
                blockers.append("export advanced state requires draft export policy note")
        if norm_upper(case.get("scomet_flag")) == "TRUE":
            blockers.append("SCOMET suspected; specialist review required before any promotion")

    case_approvals = approvals_for_case(case_id, approvals)
    if status == "APPROVAL_REQUIRED":
        pending = [row for row in case_approvals if norm_upper(row.get("approval_status")) == "PENDING"]
        if not pending:
            blockers.append("APPROVAL_REQUIRED status requires a PENDING approval row")
    if status == "APPROVED" and not any(norm_upper(row.get("approval_status")) == "APPROVED" for row in case_approvals):
        blockers.append("APPROVED status requires an APPROVED approval receipt row")

    return {
        "case_id": case_id,
        "workflow_type": case.get("workflow_type", ""),
        "status": case.get("status", ""),
        "grade": case_grade(case),
        "decision": "PASS" if not blockers else "BLOCKED",
        "strict_quote_proof_count": len(strict_proofs),
        "quote_classifications": classifications,
        "blockers": sorted(dict.fromkeys(blockers)),
        "warnings": sorted(dict.fromkeys(warnings)),
    }


def build_critic_report(
    cases: list[dict[str, str]],
    quotes: list[dict[str, str]],
    suppliers: list[dict[str, str]],
    approvals: list[dict[str, str]],
    rfqs: list[dict[str, str]],
    *,
    case_id: str = "",
    include_all: bool = False,
) -> dict[str, Any]:
    selected = [
        case for case in cases
        if (case_id and case.get("case_id") == case_id) or (include_all and is_target_case(case))
    ]
    reviews = [
        review_case(case, quotes=quotes, suppliers=suppliers, approvals=approvals, rfqs=rfqs)
        for case in selected
    ]
    blocked = [review for review in reviews if review["decision"] == "BLOCKED"]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "target_rule": "A/A+ score or PRICING_READY/ARTIFACT_PRODUCTION/APPROVAL_REQUIRED/APPROVED/founder-recommended markers",
        "case_count": len(reviews),
        "blocked_count": len(blocked),
        "status": "PASS" if not blocked else "BLOCKED",
        "reviews": reviews,
        "safety_note": "Read-only critic gate. No sends, uploads, submissions, payments, DSC use, or final commercial/compliance claims.",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Critic Gate Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Status: **{report['status']}**",
        f"- Cases reviewed: {report['case_count']}",
        f"- Blocked cases: {report['blocked_count']}",
        "",
        report["safety_note"],
        "",
    ]
    for review in report["reviews"]:
        lines.extend(
            [
                f"## {review['case_id']} — {review['decision']}",
                f"- Workflow: {review['workflow_type']}",
                f"- Status: {review['status']}",
                f"- Grade: {review['grade'] or 'n/a'}",
                f"- Strict quote proofs: {review['strict_quote_proof_count']}",
                "",
            ]
        )
        for blocker in review["blockers"]:
            lines.append(f"- BLOCKER: {blocker}")
        for warning in review["warnings"]:
            lines.append(f"- WARN: {warning}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic internal critic gate")
    parser.add_argument("--case-id")
    parser.add_argument("--all", action="store_true", help="Review all targeted high-score/advanced cases")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-blocker", action="store_true")
    args = parser.parse_args()

    if not args.case_id and not args.all:
        print("Provide --case-id or --all.")
        return 2

    report = build_critic_report(
        load_csv(DATA_DIR / "master_cases.csv"),
        load_csv(DATA_DIR / "quote_master.csv"),
        load_csv(DATA_DIR / "supplier_master.csv"),
        load_csv(DATA_DIR / "approvals_receipts.csv"),
        load_csv(DATA_DIR / "rfq_master.csv"),
        case_id=args.case_id or "",
        include_all=args.all,
    )
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"critic_gate_{stamp}.json"
    md_path = output_dir / f"critic_gate_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, report)

    payload = {
        "status": report["status"],
        "case_count": report["case_count"],
        "blocked_count": report["blocked_count"],
        "json": display_path(json_path),
        "markdown": display_path(md_path),
    }
    print(json.dumps(payload, indent=2) if args.json else f"Critic gate {report['status']}: {display_path(md_path)}")
    return 1 if args.fail_on_blocker and report["blocked_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
