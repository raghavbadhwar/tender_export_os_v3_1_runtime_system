#!/usr/bin/env python3
"""Shadow-evaluate six complete GOV/EXPORT case DAGs without side effects."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "kanban_task_graphs" / "shadow"
TERMINAL_CASE_STATUSES = {"REJECTED", "WON", "LOST", "ARCHIVED"}
TYPED_BLOCK_KINDS = {"needs_input", "dependency", "capability"}


from scripts.create_case_task_graph import build_graph, get_live_profiles, load_cases
from scripts.quote_proof import strict_quote_proofs
from scripts.validate_kanban_handoff import validate_task_input


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _resolve(path: str, project_root: Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else project_root / candidate


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def select_shadow_cases(cases: Iterable[dict[str, Any]], *, per_workflow: int = 3) -> list[dict[str, Any]]:
    """Select a stable, non-terminal three-case sample for each workflow."""
    if per_workflow <= 0:
        raise ValueError("per_workflow must be positive")
    rows = [dict(row) for row in cases if isinstance(row, dict)]
    selected: list[dict[str, Any]] = []
    for workflow in ("GOV", "EXPORT"):
        candidates = sorted(
            (
                row
                for row in rows
                if str(row.get("workflow_type") or "").upper() == workflow
                and str(row.get("status") or "").upper() not in TERMINAL_CASE_STATUSES
                and row.get("case_id")
            ),
            key=lambda row: str(row.get("case_id") or ""),
        )
        if len(candidates) < per_workflow:
            raise ValueError(
                f"Need {per_workflow} non-terminal {workflow} cases for shadow run; found {len(candidates)}"
            )
        selected.extend(candidates[:per_workflow])
    return selected


def _blocked(
    task: dict[str, Any],
    *,
    kind: str,
    reason: str,
    detail: str,
    missing_inputs: list[str] | None = None,
    parent_states: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "stage": task["key"],
        "assignee": task["assignee"],
        "state": "BLOCKED",
        "block_kind": kind,
        "block_reason": reason,
        "block_detail": detail,
        "missing_inputs": missing_inputs or [],
        "parent_states": parent_states or {},
        "approval_required": bool(task.get("handoff", {}).get("approval_required")),
        "external_effect": bool(task.get("external_effect")),
    }


def _ready(task: dict[str, Any], parent_states: dict[str, str]) -> dict[str, Any]:
    return {
        "stage": task["key"],
        "assignee": task["assignee"],
        "state": "READY",
        "block_kind": "",
        "block_reason": "",
        "block_detail": "All current input artifacts and structural gates needed to start this stage are present.",
        "missing_inputs": [],
        "parent_states": parent_states,
        "approval_required": bool(task.get("handoff", {}).get("approval_required")),
        "external_effect": bool(task.get("external_effect")),
    }


def evaluate_shadow_graph(
    case: dict[str, Any],
    graph: dict[str, Any],
    *,
    live_profiles: set[str],
    quote_rows: list[dict[str, Any]],
    project_root: Path = PROJECT_ROOT,
    as_of: dt.datetime | None = None,
) -> dict[str, Any]:
    """Evaluate the current readiness of every graph stage without running it."""
    current_time = (as_of or _utc_now()).astimezone(dt.timezone.utc)
    case_id = str(case.get("case_id") or "")
    local_ids = {str(task.get("local_id") or "") for task in graph.get("tasks") or []}
    structural_errors: list[str] = []
    stage_rows: list[dict[str, Any]] = []
    state_by_local_id: dict[str, str] = {}
    strict_quotes = strict_quote_proofs(case_id, quote_rows)

    for task in graph.get("tasks") or []:
        local_id = str(task.get("local_id") or "")
        stage = str(task.get("key") or "")
        input_validation = validate_task_input(
            task,
            known_case_ids={case_id},
            project_root=project_root,
            check_input_files=False,
        )
        if not input_validation["ok"]:
            structural_errors.extend(f"{stage}: {error}" for error in input_validation["errors"])
        if task.get("assignee") not in live_profiles:
            structural_errors.append(f"{stage}: unknown live assignee {task.get('assignee')}")
        unknown_parents = sorted(set(task.get("parents") or []) - local_ids)
        if unknown_parents:
            structural_errors.append(f"{stage}: unknown parents {', '.join(unknown_parents)}")

        parent_states = {
            parent: state_by_local_id.get(parent, "NOT_EVALUATED")
            for parent in task.get("parents") or []
        }
        required_inputs = list(task.get("handoff", {}).get("input_artifacts") or [])
        missing_inputs = [path for path in required_inputs if not _resolve(str(path), project_root).exists()]

        if not input_validation["ok"] or task.get("assignee") not in live_profiles or unknown_parents:
            row = _blocked(
                task,
                kind="capability",
                reason="invalid_task_contract",
                detail="The typed task, live assignee, or parent contract is invalid; do not dispatch it.",
                missing_inputs=missing_inputs,
                parent_states=parent_states,
            )
        elif task.get("initial_status") == "blocked" or task.get("block_kind") == "needs_input":
            row = _blocked(
                task,
                kind="needs_input",
                reason=str(task.get("block_reason") or "owner_approval"),
                detail="The graph defines an explicit human approval boundary; shadow mode cannot satisfy it.",
                missing_inputs=missing_inputs,
                parent_states=parent_states,
            )
        elif bool(task.get("external_effect")):
            row = _blocked(
                task,
                kind="needs_input",
                reason="owner_approval",
                detail="External-effect tracking is never executed in a shadow run and requires a fresh exact-scope owner command.",
                missing_inputs=missing_inputs,
                parent_states=parent_states,
            )
        elif missing_inputs:
            row = _blocked(
                task,
                kind="needs_input",
                reason="missing_documents",
                detail="One or more declared stage input artifacts are absent from the current private workspace.",
                missing_inputs=missing_inputs,
                parent_states=parent_states,
            )
        elif stage == "pricing" and len(strict_quotes) < 2:
            row = _blocked(
                task,
                kind="needs_input",
                reason="missing_documents",
                detail=f"Pricing requires two strict supplier-specific quote proofs; found {len(strict_quotes)}.",
                parent_states=parent_states,
            )
            row["strict_quote_proofs"] = len(strict_quotes)
        elif any(state != "READY" for state in parent_states.values()):
            row = _blocked(
                task,
                kind="dependency",
                reason="parent_not_ready",
                detail="At least one parent stage is not currently ready; no downstream promotion is simulated.",
                parent_states=parent_states,
            )
        else:
            row = _ready(task, parent_states)

        stage_rows.append(row)
        state_by_local_id[local_id] = row["state"]

    all_typed = all(
        row.get("state") == "READY"
        or (row.get("state") == "BLOCKED" and row.get("block_kind") in TYPED_BLOCK_KINDS and row.get("block_reason"))
        for row in stage_rows
    )
    stable_payload = {
        "case_id": case_id,
        "workflow_type": graph.get("workflow_type"),
        "graph_sha256": graph.get("graph_sha256"),
        "stages": stage_rows,
        "structural_errors": structural_errors,
    }
    receipt_sha = hashlib.sha256(
        json.dumps(stable_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    blockers = [row for row in stage_rows if row["state"] == "BLOCKED"]
    return {
        "schema_version": 1,
        "generated_at": current_time.replace(microsecond=0).isoformat(),
        "mode": "shadow_readiness_only",
        "status": "PASS" if not structural_errors and all_typed else "FAIL",
        "case_id": case_id,
        "workflow_type": graph.get("workflow_type"),
        "case_status": str(case.get("status") or ""),
        "graph_sha256": graph.get("graph_sha256"),
        "receipt_sha256": receipt_sha,
        "stage_count": len(stage_rows),
        "ready_stage_count": sum(row["state"] == "READY" for row in stage_rows),
        "blocked_stage_count": len(blockers),
        "end_state": stage_rows[-1]["state"] if stage_rows else "INVALID",
        "all_stages_ready_or_typed_blocked": all_typed,
        "structural_errors": structural_errors,
        "stages": stage_rows,
        "strict_quote_proof_count": len(strict_quotes),
        "kanban_mutated": False,
        "agents_executed": False,
        "external_actions_executed": False,
    }


def _write_private_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def run_shadow_suite(
    cases: Iterable[dict[str, Any]],
    *,
    live_profiles: set[str],
    project_root: Path = PROJECT_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    as_of: dt.datetime | None = None,
) -> dict[str, Any]:
    """Write six graph/receipt pairs and one stable suite receipt."""
    current_time = (as_of or _utc_now()).astimezone(dt.timezone.utc)
    selected = select_shadow_cases(cases, per_workflow=3)
    quote_rows = _read_csv(project_root / "data" / "quote_master.csv")
    receipts: list[dict[str, Any]] = []
    graphs: list[dict[str, Any]] = []

    for selected_case in selected:
        graph = build_graph(selected_case)
        graph["generated_at"] = current_time.replace(microsecond=0).isoformat()
        graph["mode"] = "shadow_readiness_only"
        graph["kanban_mutated"] = False
        graph["agents_executed"] = False
        graph["external_actions_executed"] = False
        receipt = evaluate_shadow_graph(
            selected_case,
            graph,
            live_profiles=live_profiles,
            quote_rows=quote_rows,
            project_root=project_root,
            as_of=current_time,
        )
        case_dir = output_root / str(selected_case["case_id"])
        _write_private_json(case_dir / "graph.json", graph)
        _write_private_json(case_dir / "shadow_receipt.json", receipt)
        graphs.append(graph)
        receipts.append(receipt)

    selected_ids = [str(row["case_id"]) for row in selected]
    stable_suite = {
        "selected_case_ids": selected_ids,
        "graph_sha256s": [graph["graph_sha256"] for graph in graphs],
        "receipt_sha256s": [receipt["receipt_sha256"] for receipt in receipts],
    }
    suite_hash = hashlib.sha256(
        json.dumps(stable_suite, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    workflow_counts = {
        workflow: sum(str(row.get("workflow_type") or "").upper() == workflow for row in selected)
        for workflow in ("EXPORT", "GOV")
    }
    summary = {
        "schema_version": 1,
        "generated_at": current_time.replace(microsecond=0).isoformat(),
        "mode": "shadow_readiness_only",
        "status": "PASS" if len(receipts) == 6 and all(row["status"] == "PASS" for row in receipts) else "FAIL",
        "selected_case_count": len(selected),
        "selected_case_ids": selected_ids,
        "workflow_counts": workflow_counts,
        "suite_sha256": suite_hash,
        "suite_idempotency_key": f"teos:shadow-case-graphs:v1:{suite_hash[:16]}",
        "receipts": [
            {
                "case_id": receipt["case_id"],
                "workflow_type": receipt["workflow_type"],
                "status": receipt["status"],
                "end_state": receipt["end_state"],
                "ready_stage_count": receipt["ready_stage_count"],
                "blocked_stage_count": receipt["blocked_stage_count"],
                "receipt_sha256": receipt["receipt_sha256"],
                "path": str(output_root / receipt["case_id"] / "shadow_receipt.json"),
            }
            for receipt in receipts
        ],
        "kanban_mutated": False,
        "agents_executed": False,
        "external_actions_executed": False,
    }
    _write_private_json(output_root / "shadow_suite_receipt.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    args = parser.parse_args()
    output_root = Path(args.output_root).expanduser()
    if not output_root.is_absolute():
        output_root = PROJECT_ROOT / output_root
    summary = run_shadow_suite(
        load_cases(),
        live_profiles=get_live_profiles(),
        project_root=PROJECT_ROOT,
        output_root=output_root,
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "selected_case_ids": summary["selected_case_ids"],
                "suite_idempotency_key": summary["suite_idempotency_key"],
                "output": str(output_root / "shadow_suite_receipt.json"),
            },
            indent=2,
        )
    )
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
