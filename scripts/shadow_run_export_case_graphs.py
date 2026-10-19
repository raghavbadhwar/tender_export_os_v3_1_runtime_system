#!/usr/bin/env python3
"""Build safe export-DAG shadow reports for current catalogue targets and verified RFQs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    from scripts.create_case_task_graph import build_graph
except ModuleNotFoundError:  # pragma: no cover - direct execution
    from create_case_task_graph import build_graph  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "kanban_task_graphs" / "shadow"
CATALOGUE_PREFIX = "EXP-TA-"
COMMERCIAL_STAGES = {
    "supplier", "compliance", "pricing", "quote_pack", "quote_approval", "quote_delivery",
    "negotiation_drafts", "order_capture", "shipment_invoice_payment", "repeat_buyer_learning",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def select_cases(cases: list[dict[str, str]], rfqs: list[dict[str, str]]) -> list[tuple[str, dict[str, str], dict[str, str]]]:
    """Select exactly four catalogue targets and two separately RFQ-verified cases."""
    export_cases = {row.get("case_id", ""): row for row in cases if row.get("workflow_type", "").upper() == "EXPORT"}
    rfq_by_case = {row.get("case_id", ""): row for row in rfqs if row.get("case_id")}
    catalogue_ids = sorted(case_id for case_id in export_cases if case_id.startswith(CATALOGUE_PREFIX))
    if len(catalogue_ids) != 4:
        raise ValueError(f"Expected exactly four current catalogue targets, found {len(catalogue_ids)}: {catalogue_ids}")
    rfq_ids = sorted(
        row.get("case_id", "")
        for row in rfqs
        if row.get("case_id") in export_cases
        and row.get("case_id") not in catalogue_ids
        and row.get("rfq_stage") == "RFQ_VERIFIED"
        and row.get("evidence_status") == "RFQ_VERIFIED"
    )
    if len(rfq_ids) < 2:
        raise ValueError(f"Expected at least two RFQ-verified export cases, found {len(rfq_ids)}: {rfq_ids}")
    selected: list[tuple[str, dict[str, str], dict[str, str]]] = []
    for case_id in catalogue_ids:
        selected.append(("CATALOGUE_TARGET", export_cases[case_id], rfq_by_case.get(case_id, {})))
    for case_id in rfq_ids[:2]:
        selected.append(("RFQ_VERIFIED", export_cases[case_id], rfq_by_case[case_id]))
    return selected


def classify_case(track: str, case: dict[str, str], rfq: dict[str, str]) -> dict[str, Any]:
    case_id = case["case_id"]
    graph = build_graph(case)
    task_keys = [str(task["key"]) for task in graph["tasks"]]
    external_effect_tasks = [key for key, task in zip(task_keys, graph["tasks"]) if task.get("external_effect")]
    if track == "CATALOGUE_TARGET":
        state = "CATALOGUE_HYPOTHESIS_ONLY"
        barrier = "RFQ_VERIFICATION_REQUIRED"
        reason = (
            "Catalogue fit or public retailer presence is not buyer-specific demand. The shadow run blocks commercial stages "
            "until an evidenced buyer RFQ is verified."
        )
        commercial_allowed = False
        blocked_stages = sorted(COMMERCIAL_STAGES)
    else:
        state = "RFQ_VERIFIED_COMMERCIAL_CANDIDATE"
        barrier = "EVIDENCE_AND_OWNER_GATES_REMAIN"
        reason = (
            "Buyer-specific RFQ evidence exists, so the supplier/compliance/pricing branch may be evaluated. "
            "It remains blocked from external outreach, quote delivery, order acceptance, and any final commercial claim without the required evidence and owner approvals."
        )
        commercial_allowed = True
        blocked_stages = []
    return {
        "case_id": case_id,
        "track": track,
        "case_status": case.get("status", ""),
        "buyer_name": case.get("buyer_name", ""),
        "rfq_stage": rfq.get("rfq_stage", "MISSING"),
        "rfq_evidence_status": rfq.get("evidence_status", "MISSING"),
        "classification": state,
        "barrier": barrier,
        "reason": reason,
        "commercial_path_allowed_for_internal_evaluation": commercial_allowed,
        "commercial_stages_forced_blocked": blocked_stages,
        "graph_sha256": graph["graph_sha256"],
        "task_count": len(graph["tasks"]),
        "task_keys": task_keys,
        "external_effect_task_keys": external_effect_tasks,
        "external_actions_executed": False,
    }


def build_shadow_report(cases: list[dict[str, str]], rfqs: list[dict[str, str]]) -> dict[str, Any]:
    records = [classify_case(track, case, rfq) for track, case, rfq in select_cases(cases, rfqs)]
    catalogue = [record for record in records if record["track"] == "CATALOGUE_TARGET"]
    verified = [record for record in records if record["track"] == "RFQ_VERIFIED"]
    errors: list[str] = []
    if len(catalogue) != 4 or len(verified) != 2:
        errors.append("shadow selection did not retain four catalogue targets and two RFQ-verified cases")
    if any(record["commercial_path_allowed_for_internal_evaluation"] for record in catalogue):
        errors.append("catalogue targets were incorrectly allowed into the commercial path")
    if any(not record["commercial_path_allowed_for_internal_evaluation"] for record in verified):
        errors.append("RFQ-verified cases were incorrectly treated as catalogue-only")
    if any(record["external_effect_task_keys"] for record in records):
        errors.append("export graph exposed an external-effect task during shadow execution")
    return {
        "schema_version": "export_case_graph_shadow_run.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "SHADOW_ONLY",
        "records": records,
        "summary": {
            "catalogue_target_count": len(catalogue),
            "rfq_verified_count": len(verified),
            "catalogue_targets_blocked_from_commercial_path": sum(not item["commercial_path_allowed_for_internal_evaluation"] for item in catalogue),
            "rfq_cases_allowed_to_internal_commercial_evaluation": sum(item["commercial_path_allowed_for_internal_evaluation"] for item in verified),
        },
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "external_actions_executed": False,
    }


def write_report(report: dict[str, Any], *, output_root: Path = OUTPUT_ROOT) -> list[str]:
    paths: list[str] = []
    for record in report["records"]:
        target = output_root / record["case_id"] / "export_vertical_shadow.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        paths.append(str(target.relative_to(PROJECT_ROOT)))
    summary_path = output_root / "export_vertical_shadow_summary.json"
    summary_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths.append(str(summary_path.relative_to(PROJECT_ROOT)))
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write local shadow reports; never contacts or executes anything")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_shadow_report(load_csv(DATA_DIR / "master_cases.csv"), load_csv(DATA_DIR / "rfq_master.csv"))
    if args.write:
        report["output_paths"] = write_report(report)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"EXPORT shadow run: {report['status']} ({report['summary']['catalogue_target_count']} catalogue targets, {report['summary']['rfq_verified_count']} RFQ-verified cases)")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
