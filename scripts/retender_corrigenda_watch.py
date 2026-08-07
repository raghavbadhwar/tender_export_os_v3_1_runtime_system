#!/usr/bin/env python3
"""Detect retender, corrigendum, amendment, and date-extension signals."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event  # noqa: E402
from scripts.low_competition_order_radar import (  # noqa: E402
    DATA_DIR,
    DEFAULT_KEYWORDS,
    OUTPUT_DIR,
    cluster_hits,
    load_csv,
    load_source_records,
    load_yaml_config,
    now_utc,
    relative,
    source_record_to_case,
    text_blob,
    today_compact,
)


def classify_change(row: dict[str, Any], hits: list[str]) -> str:
    text = text_blob(row)
    if any("retender" in hit.lower() or "re-tender" in hit.lower() or "re tender" in hit.lower() for hit in hits):
        return "RETENDER"
    if "single bid" in text or "shortfall of bidders" in text:
        return "LOW_BIDDER_RECALL"
    if "date extension" in text or "extended bid date" in text or "technical bid extended" in text:
        return "DATE_EXTENSION"
    if "revised boq" in text or "boq revised" in text:
        return "REVISED_BOQ"
    if "amendment" in text:
        return "AMENDMENT"
    return "CORRIGENDUM"


def detect_retender_corrigenda_records(
    cases: list[dict[str, Any]],
    source_records: list[dict[str, Any]],
    keyword_config: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = list(cases)
    rows.extend(source_record_to_case(record, index) for index, record in enumerate(source_records))
    output = []
    for row in rows:
        hits = cluster_hits(row, keyword_config).get("retender_corrigenda", [])
        text = text_blob(row)
        has_structured_corrigendum = str(row.get("corrigenda_count", "")).strip() not in {"", "0"}
        if not hits and not has_structured_corrigendum:
            continue
        change_type = classify_change(row, hits)
        output.append(
            {
                "old_case_id": row.get("case_id", ""),
                "new_possible_case_or_source_url": row.get("source_url", ""),
                "buyer": row.get("buyer_name", ""),
                "old_deadline": row.get("old_deadline", "") or row.get("previous_deadline", ""),
                "new_deadline": row.get("deadline_date", ""),
                "change_type": change_type,
                "why_this_may_reduce_competition": reason_for_change(change_type, text),
                "what_to_recheck": [
                    "deadline",
                    "BOQ/specification changes",
                    "eligibility and OEM/manufacturer-only language",
                    "EMD/tender fee changes",
                    "supplier proof feasibility",
                ],
                "recommended_action": "Re-deep-read public documents and route internally; no upload, bid, payment, DSC, or external message without approval.",
                "matched_keywords": hits,
            }
        )
    return sorted(output, key=lambda item: (item["change_type"], item["old_case_id"]))


def reason_for_change(change_type: str, text: str) -> str:
    if change_type == "RETENDER":
        return "Retender/reissue signals can mean prior bidder pool was thin or requirements changed."
    if change_type == "LOW_BIDDER_RECALL":
        return "Single-bid/shortfall signal suggests competition may have been insufficient."
    if change_type == "DATE_EXTENSION":
        return "Date extension gives more time for evidence review and may be under-monitored by competitors."
    if change_type == "REVISED_BOQ":
        return "Revised BOQ can reset bidder assumptions and create a narrow recheck window."
    if "corrigendum" in text:
        return "Corrigendum-driven updates are often missed by simple keyword monitors."
    return "Amended procurement needs recheck and may be less crowded than fresh headline tenders."


def build_report(
    matches: list[dict[str, Any]],
    records_analyzed: int,
    *,
    as_of: dt.date | None = None,
) -> dict[str, Any]:
    run_date = as_of or dt.date.today()
    return {
        "run_id": f"RUN-{run_date.strftime('%Y%m%d')}-RETENDER-CORRIGENDA",
        "run_date": run_date.isoformat(),
        "created_at": now_utc(),
        "records_analyzed": records_analyzed,
        "top_candidates_count": len(matches),
        "safety_boundary": "Internal-only watch. No portal bypass, bid, upload, payment, DSC, external message, or final commitment executed.",
        "matches": matches,
    }


def build_change_actions(
    matches: list[dict[str, Any]],
    *,
    report_path: str,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for match in matches:
        case_id = str(match.get("old_case_id") or "").strip()
        if not case_id:
            continue
        stable = {
            "case_id": case_id,
            "source_url": str(match.get("new_possible_case_or_source_url") or ""),
            "change_type": str(match.get("change_type") or "CORRIGENDUM"),
            "old_deadline": str(match.get("old_deadline") or ""),
            "new_deadline": str(match.get("new_deadline") or ""),
            "matched_keywords": sorted(str(value) for value in match.get("matched_keywords") or []),
        }
        change_hash = hashlib.sha256(
            json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        invalidated = ["deep_read", "supplier", "pricing", "compliance", "artifacts"]
        handoff = {
            "case_id": case_id,
            "workflow_type": "GOV",
            "stage": "document_diff",
            "source_event_ids": [],
            "input_artifacts": [report_path],
            "required_output_schema": "config/schemas/mcp_tool_result.schema.json",
            "approval_required": False,
            "deadline": stable["new_deadline"],
            "stop_conditions": ["missing_documents", "ambiguous_compliance", "portal_human_challenge"],
            "next_profile": "gov-tender-intelligence",
        }
        body = "\n".join(
            [
                "TEOS_TYPED_HANDOFF_V1",
                json.dumps(handoff, sort_keys=True),
                "",
                f"Evidenced change: {json.dumps(stable, sort_keys=True)}",
                f"Change hash: {change_hash}",
                f"Invalidate readiness for: {', '.join(invalidated)}",
                f"Source report: {report_path}",
                "Produce a cited document/corrigendum diff. Do not submit, upload, contact, pay, use DSC, or make final commitments.",
                "external_effect: false",
            ]
        )
        previous = stable["old_deadline"]
        new = stable["new_deadline"]
        event = None
        if previous and new and previous != new:
            event = {
                "event_type": "tender.deadline_changed",
                "case_id": case_id,
                "object_type": "case",
                "object_id": case_id,
                "payload": {
                    "previous_deadline": previous,
                    "new_deadline": new,
                    "change_hash": change_hash,
                    "source_url": stable["source_url"],
                    "invalidate_stages": invalidated,
                },
                "citations": [report_path, stable["source_url"]] if stable["source_url"] else [report_path],
                "idempotency_key": f"teos:deadline-change:{case_id}:{change_hash}",
            }
        actions.append(
            {
                "case_id": case_id,
                "change_hash": change_hash,
                "change_type": stable["change_type"],
                "invalidate_stages": invalidated,
                "event": event,
                "task": {
                    "title": f"{case_id} — Review evidenced {stable['change_type'].lower()} and document diff",
                    "body": body,
                    "assignee": "gov-tender-intelligence",
                    "idempotency_key": f"teos:{case_id}:document-diff:{change_hash}",
                    "external_effect": False,
                },
            }
        )
    return sorted(actions, key=lambda row: (row["case_id"], row["change_hash"]))


def apply_change_actions(actions: list[dict[str, Any]], *, report_path: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for action in actions:
        event_id = ""
        event = action.get("event")
        if event:
            recorded = append_event(
                event["event_type"],
                "retender_corrigenda_watch",
                case_id=event["case_id"],
                object_type=event["object_type"],
                object_id=event["object_id"],
                source="official_public_corrigenda_watch",
                payload=event["payload"],
                citations=event["citations"],
                idempotency_key=event["idempotency_key"],
            )
            event_id = recorded["event_id"]
        task = action["task"]
        command = [
            "hermes", "kanban", "--board", "tender-export-os", "create", task["title"],
            "--body", task["body"], "--assignee", task["assignee"],
            "--workspace", f"dir:{PROJECT_ROOT}", "--tenant", action["case_id"],
            "--idempotency-key", task["idempotency_key"], "--max-runtime", "900",
            "--max-retries", "1", "--created-by", "retender_corrigenda_watch", "--json",
        ]
        completed = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120, check=False)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Kanban task creation failed")
        data = json.loads(completed.stdout)
        task_id = str(data.get("id") or data.get("task_id") or (data.get("task") or {}).get("id") or "")
        if not task_id:
            raise RuntimeError("Kanban task creation returned no task id")
        results.append({"case_id": action["case_id"], "event_id": event_id, "task_id": task_id})
    return results


def write_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"retender_corrigenda_watch_{today_compact()}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def maybe_append_event(report: dict[str, Any], path: Path, *, dry_run: bool, record_event: bool) -> None:
    if dry_run or not record_event:
        return
    append_event(
        "retender_corrigenda.watch_generated",
        "retender_corrigenda_watch",
        object_type="retender_corrigenda_watch",
        object_id=report["run_id"],
        source="local_runtime",
        payload={
            "run_id": report["run_id"],
            "report_path": relative(path),
            "records_analyzed": report["records_analyzed"],
            "top_candidates_count": report["top_candidates_count"],
            "created_at": report["created_at"],
        },
        citations=[relative(path)],
        idempotency_key=f"teos:retender-corrigenda-watch:{report['run_date']}",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch retender/corrigenda/date-extension signals")
    parser.add_argument("--dry-run", action="store_true", help="Write local report only; do not append events")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--record-event", action="store_true")
    parser.add_argument("--apply-actions", action="store_true", help="Append evidenced deadline events and create idempotent internal diff cards")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    cases = load_csv(DATA_DIR / "master_cases.csv", "master_cases.example.csv")
    source_records = load_source_records()
    matches = detect_retender_corrigenda_records(cases, source_records, load_yaml_config(DEFAULT_KEYWORDS))
    report = build_report(matches, len(cases) + len(source_records))
    path = write_report(report, Path(args.output_dir))
    report_path = relative(path)
    actions = build_change_actions(matches, report_path=report_path)
    report["change_actions"] = actions
    report["change_action_count"] = len(actions)
    report["actions_applied"] = []
    report["kanban_mutated"] = False
    report["external_actions_executed"] = False
    if args.apply_actions and not args.dry_run:
        report["actions_applied"] = apply_change_actions(actions, report_path=report_path)
        report["kanban_mutated"] = bool(report["actions_applied"])
    write_report(report, Path(args.output_dir))
    maybe_append_event(report, path, dry_run=args.dry_run, record_event=args.record_event)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Retender/corrigenda watch report: {path}")
        print("No external action was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
