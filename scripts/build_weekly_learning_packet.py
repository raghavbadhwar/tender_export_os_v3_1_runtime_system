#!/usr/bin/env python3
"""Build Hermes weekly learning council packet from local ledgers."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts.build_source_yield_metrics import build_report as build_source_yield_report
    from scripts.build_weekly_forecast_quality_report import build_report as build_forecast_quality_report
    from scripts.supplier_performance_projection import build_projection, read_csv
    from scripts.event_ledger import load_events
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from build_source_yield_metrics import build_report as build_source_yield_report
    from build_weekly_forecast_quality_report import build_report as build_forecast_quality_report
    from supplier_performance_projection import build_projection, read_csv
    from event_ledger import load_events


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "learning_packets"
PROMPT_PATH = PROJECT_ROOT / "prompts" / "hermes" / "weekly_learning_council.md"


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def upper(value: Any) -> str:
    return clean(value).upper()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def status_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(upper(row.get(field)) or "UNKNOWN" for row in rows))


def failed_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures = []
    for row in rows:
        blob = " ".join(clean(row.get(key)) for key in ("status", "result", "notes", "error"))
        if any(token in blob.upper() for token in ("FAIL", "ERROR", "BLOCKED")):
            failures.append({
                "run_id": clean(row.get("run_id")),
                "agent": clean(row.get("agent")) or clean(row.get("profile")),
                "status": clean(row.get("status")) or clean(row.get("result")),
                "notes": clean(row.get("notes"))[:240],
            })
    return failures[:50]


def reply_results(communication_rows: list[dict[str, Any]], outreach_rows: list[dict[str, Any]]) -> dict[str, Any]:
    reply_like = [row for row in communication_rows if any(token in upper(row.get("message_type") or row.get("direction") or row.get("classification")) for token in ("REPLY", "INBOUND"))]
    return {
        "communication_rows": len(communication_rows),
        "outreach_rows": len(outreach_rows),
        "reply_like_rows": len(reply_like),
        "outreach_status_counts": status_counts(outreach_rows, "send_status") or status_counts(outreach_rows, "approval_status"),
    }


def policy_denials(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    denials = []
    for event in events:
        if event.get("event_type") != "policy.decision_recorded":
            continue
        payload = event.get("payload") or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        if str(payload.get("allowed")).lower() == "false" or upper(payload.get("status")) in {"DENIED", "BLOCKED"}:
            denials.append({
                "event_id": event.get("event_id"),
                "action": payload.get("action"),
                "reason_code": payload.get("reason_code"),
                "status": payload.get("status"),
            })
    return denials[:50]


def proposal_effectiveness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total": len(rows),
        "status_counts": status_counts(rows, "status"),
        "approved": sum(upper(row.get("status")) == "APPROVED" for row in rows),
        "applied": sum(upper(row.get("status")) == "APPLIED" for row in rows),
        "failed_or_rejected": sum(upper(row.get("status")) in {"FAIL", "REJECTED"} for row in rows),
    }


def skill_usage(events: list[dict[str, Any]], run_rows: list[dict[str, Any]]) -> dict[str, Any]:
    skill_events = [event for event in events if "skill" in json.dumps(event, default=str).lower()]
    profile_counts = Counter(clean(row.get("agent")) or clean(row.get("profile")) or "UNKNOWN" for row in run_rows)
    return {
        "skill_related_event_count": len(skill_events),
        "top_profiles": dict(profile_counts.most_common(10)),
    }


def unresolved_contradictions(events: list[dict[str, Any]], run_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found = []
    for event in events:
        text = json.dumps(event, default=str).lower()
        if "contradiction" in text or "conflict" in text:
            found.append({"event_id": event.get("event_id"), "event_type": event.get("event_type"), "summary": text[:240]})
    for row in run_rows:
        text = json.dumps(row, default=str).lower()
        if "contradiction" in text or "conflict" in text:
            found.append({"run_id": row.get("run_id"), "summary": text[:240]})
    return found[:50]


def build_packet(*, week_ending: str) -> dict[str, Any]:
    events = load_events(DATA_DIR / "events.jsonl")
    outcomes = load_csv(DATA_DIR / "case_outcomes.csv")
    run_rows = load_csv(DATA_DIR / "agent_run_log.csv")
    proposals = load_csv(DATA_DIR / "learning_proposals.csv")
    communication = load_csv(DATA_DIR / "communication_log.csv")
    outreach = load_csv(DATA_DIR / "outreach_queue.csv")
    forecasts = load_csv(DATA_DIR / "forecast_candidates.csv")
    backtests = load_csv(DATA_DIR / "forecast_backtests.csv")
    source_health = load_csv(DATA_DIR / "source_health.csv")
    supplier_report = build_projection(
        suppliers=read_csv(DATA_DIR / "supplier_master.csv"),
        quotes=read_csv(DATA_DIR / "quote_master.csv"),
        outcomes=read_csv(DATA_DIR / "case_outcomes.csv"),
        owner_corrections=[],
    )
    forecast_quality = build_forecast_quality_report(
        forecasts=forecasts,
        backtests=backtests,
        source_health=source_health,
        week_ending=week_ending,
    )
    return {
        "packet_type": "HERMES_WEEKLY_LEARNING_COUNCIL",
        "week_ending": week_ending,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "prompt_path": rel(PROMPT_PATH),
        "safety_boundary": "Learning packet only. No external action, source weight change, supplier promotion, model promotion, payment, DSC, final price, or compliance commitment.",
        "outcomes": {"count": len(outcomes), "outcome_type_counts": status_counts(outcomes, "outcome_type")},
        "owner_corrections": {"count": 0, "note": "No dedicated owner corrections ledger found; supplier projection accepts optional verified corrections."},
        "failed_runs": failed_runs(run_rows),
        "source_yield": build_source_yield_report(),
        "supplier_performance": supplier_report,
        "reply_results": reply_results(communication, outreach),
        "forecast_error": forecast_quality["calibration_state"],
        "policy_denials": policy_denials(events),
        "unresolved_contradictions": unresolved_contradictions(events, run_rows),
        "skill_usage": skill_usage(events, run_rows),
        "previous_proposal_effectiveness": proposal_effectiveness(proposals),
        "recommended_council_questions": [
            "Which target/workflow lacks mature outcomes most urgently?",
            "Which source or supplier recommendation has enough evidence to become a formal proposal?",
            "Which blocked run indicates a missing tool, source adapter, or approval contract?",
            "Which proposal should be delayed because rollback/evaluation evidence is weak?",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week-ending", default=dt.date.today().isoformat())
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    packet = build_packet(week_ending=args.week_ending)
    outputs: dict[str, str] = {}
    if args.write:
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"weekly_learning_packet_{args.week_ending.replace('-', '')}.json"
        output.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        outputs["json"] = rel(output)
    payload = packet | {"outputs": outputs}
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
