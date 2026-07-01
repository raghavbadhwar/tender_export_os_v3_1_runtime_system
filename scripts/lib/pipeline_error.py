"""Structured pipeline error records for safe regressions and agent runs."""

from __future__ import annotations

import csv
import datetime as dt
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.event_ledger import EVENTS_FILE, append_event


@dataclass
class PipelineError:
    code: str
    stage: str
    message: str
    recoverable: bool = True
    safe_status: str = "BLOCKED"
    created_at: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat())

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reason"] = self.message
        payload["blocker_status"] = self.safe_status
        return payload

    def exit_code(self) -> int:
        return 1


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_RUN_LOG = PROJECT_ROOT / "data" / "agent_run_log.csv"
RUN_LOG_FIELDS = [
    "run_id",
    "run_date",
    "run_time",
    "agent_name",
    "trigger_type",
    "cases_processed",
    "cases_created",
    "cases_rejected",
    "cases_updated",
    "sources_checked",
    "sources_failed",
    "actions_taken",
    "approval_cards_created",
    "receipts_created",
    "errors",
    "warnings",
    "runtime_seconds",
    "status",
    "notes",
]


def make_pipeline_error(
    stage: str,
    message: str,
    code: str = "PIPELINE_BLOCKED",
    *,
    recoverable: bool = True,
    safe_status: str = "BLOCKED",
) -> PipelineError:
    return PipelineError(
        code=code,
        stage=stage,
        message=message,
        recoverable=recoverable,
        safe_status=safe_status,
    )


def blocked_error(stage: str, message: str, code: str = "PIPELINE_BLOCKED") -> dict[str, Any]:
    return make_pipeline_error(stage, message, code).to_dict()


def append_error_event(
    error: PipelineError | dict[str, Any],
    *,
    actor: str = "pipeline_error",
    case_id: str = "",
    source: str = "local_runtime",
    citations: list[str] | None = None,
    events_file: Path = EVENTS_FILE,
) -> dict[str, Any]:
    payload = error.to_dict() if isinstance(error, PipelineError) else dict(error)
    payload.setdefault("reason", payload.get("message", "Pipeline blocked"))
    payload.setdefault("blocker_status", payload.get("safe_status", "BLOCKED"))
    return append_event(
        "pipeline.error",
        actor,
        case_id=case_id,
        object_type="pipeline_error",
        object_id=str(payload.get("code", "PIPELINE_BLOCKED")),
        source=source,
        payload=payload,
        citations=citations or [],
        events_file=events_file,
    )


def write_agent_run_failure(
    error: PipelineError | dict[str, Any],
    *,
    agent_name: str,
    trigger_type: str = "pipeline_error",
    run_log_path: Path = AGENT_RUN_LOG,
    runtime_seconds: int | float = 0,
    notes: str = "",
) -> Path:
    payload = error.to_dict() if isinstance(error, PipelineError) else dict(error)
    now = dt.datetime.now().astimezone()
    row = {
        "run_id": f"RUN-{now.strftime('%Y%m%d%H%M%S')}-{str(payload.get('code', 'PIPELINE'))[:18]}",
        "run_date": now.date().isoformat(),
        "run_time": now.strftime("%H:%M:%S"),
        "agent_name": agent_name,
        "trigger_type": trigger_type,
        "cases_processed": 0,
        "cases_created": 0,
        "cases_rejected": 0,
        "cases_updated": 0,
        "sources_checked": 0,
        "sources_failed": 0,
        "actions_taken": 0,
        "approval_cards_created": 0,
        "receipts_created": 0,
        "errors": 1,
        "warnings": 0,
        "runtime_seconds": runtime_seconds,
        "status": "FAILURE",
        "notes": notes or payload.get("message", ""),
    }
    run_log_path.parent.mkdir(parents=True, exist_ok=True)
    exists = run_log_path.exists()
    with run_log_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RUN_LOG_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in RUN_LOG_FIELDS})
    return run_log_path


def fail_pipeline(
    stage: str,
    message: str,
    *,
    code: str = "PIPELINE_BLOCKED",
    agent_name: str = "pipeline",
    trigger_type: str = "pipeline_error",
    case_id: str = "",
    source: str = "local_runtime",
    citations: list[str] | None = None,
    write_run_log: bool = True,
    record_event: bool = True,
) -> int:
    error = make_pipeline_error(stage, message, code)
    if record_event:
        append_error_event(error, actor=agent_name, case_id=case_id, source=source, citations=citations)
    if write_run_log:
        write_agent_run_failure(error, agent_name=agent_name, trigger_type=trigger_type)
    return error.exit_code()
