#!/usr/bin/env python3
"""Generate per-case artifact manifests."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import json
from pathlib import Path

from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def existing_files(patterns: list[str]) -> list[str]:
    files: list[str] = []
    for pattern in patterns:
        for match in glob.glob(str(PROJECT_ROOT / pattern), recursive=True):
            path = Path(match)
            if path.is_file():
                files.append(rel(path))
    return sorted(set(files))


def build_manifest(case: dict, approvals: list[dict], quotes: list[dict], suppliers: list[dict]) -> dict:
    case_id = case.get("case_id", "")
    case_quotes = [quote for quote in quotes if quote.get("case_id") == case_id]
    supplier_ids = {quote.get("supplier_id") for quote in case_quotes if quote.get("supplier_id")}
    case_suppliers = [supplier for supplier in suppliers if supplier.get("supplier_id") in supplier_ids]
    case_approvals = [approval for approval in approvals if approval.get("case_id") == case_id]
    approval_cards = [
        approval.get("approval_card_path")
        for approval in case_approvals
        if approval.get("approval_card_path") and (PROJECT_ROOT / approval["approval_card_path"]).exists()
    ]
    receipt_patterns = [
        f"receipts/**/{case_id}*",
        *[f"receipts/**/{approval.get('approval_id')}*" for approval in case_approvals if approval.get("approval_id")],
    ]

    return {
        "case_id": case_id,
        "workflow_type": case.get("workflow_type", ""),
        "status": case.get("status", ""),
        "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "source": {
            "source_name": case.get("source_name", ""),
            "source_url": case.get("source_url", ""),
            "evidence_gap": not bool(case.get("source_url", "")),
        },
        "register_rows": {
            "case": "data/master_cases.csv",
            "approvals": [approval.get("approval_id") for approval in case_approvals],
            "quotes": [quote.get("quote_id") for quote in case_quotes],
            "suppliers": [supplier.get("supplier_id") for supplier in case_suppliers],
        },
        "artifacts": {
            "case_reports": existing_files([f"outputs/case_reports/{case_id}/**"]),
            "bid_packs": existing_files([f"outputs/bid_packs/{case_id}/**"]),
            "export_quote_packs": existing_files([f"outputs/export_quote_packs/{case_id}/**"]),
            "approval_cards": sorted(set(approval_cards)),
            "receipts": existing_files(receipt_patterns),
            "daily_briefs": existing_files(["outputs/daily_briefs/*.html"]),
        },
        "open_gates": {
            "approval_status": case.get("approval_status", ""),
            "pending_approval_ids": [
                approval.get("approval_id")
                for approval in case_approvals
                if approval.get("approval_status") == "PENDING"
            ],
            "quote_proof_count": len([quote for quote in case_quotes if quote.get("quote_received_at")]),
            "compliance_draft_required": case.get("workflow_type") == "EXPORT",
            "scomet_flag": case.get("scomet_flag", ""),
        },
        "sources_used": [
            "data/master_cases.csv",
            "data/approvals_receipts.csv",
            "data/quote_master.csv",
            "data/supplier_master.csv",
        ],
    }


def write_manifest(case: dict, manifest: dict) -> Path:
    case_id = case.get("case_id", "")
    out_dir = PROJECT_ROOT / "outputs" / "case_reports" / case_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "artifact_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate artifact manifests")
    parser.add_argument("--case-id", help="Generate one case manifest")
    parser.add_argument("--all", action="store_true", help="Generate all case manifests")
    parser.add_argument("--record-event", action="store_true", help="Append artifact.manifest_generated events")
    args = parser.parse_args()

    if not args.case_id and not args.all:
        print("Provide --case-id or --all.")
        return 2

    cases = load_csv(DATA_DIR / "master_cases.csv")
    approvals = load_csv(DATA_DIR / "approvals_receipts.csv")
    quotes = load_csv(DATA_DIR / "quote_master.csv")
    suppliers = load_csv(DATA_DIR / "supplier_master.csv")
    selected = [case for case in cases if args.all or case.get("case_id") == args.case_id]
    if not selected:
        print("No matching cases found.")
        return 1

    for case in selected:
        manifest = build_manifest(case, approvals, quotes, suppliers)
        path = write_manifest(case, manifest)
        print(f"Wrote {path}")
        if args.record_event:
            append_event(
                "artifact.manifest_generated",
                "generate_artifact_manifest",
                case_id=case.get("case_id", ""),
                object_type="artifact",
                object_id=rel(path),
                payload={"manifest_path": rel(path)},
                citations=[rel(path), "data/master_cases.csv"],
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
