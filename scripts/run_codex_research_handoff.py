#!/usr/bin/env python3
"""Run a bounded Tender Export OS research handoff through Codex CLI.

Hermes remains the control plane. Codex performs the research/runtime work and
writes a report. This script is safe by design: prompts forbid external business
actions, credential use, submissions, payments, DSC, and final claims.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "outputs" / "codex_research"
RUN_LOG = PROJECT_ROOT / "data" / "agent_run_log.csv"

RUN_LOG_FIELDS = [
    "run_id", "run_date", "run_time", "agent_name", "trigger_type",
    "cases_processed", "cases_created", "cases_rejected", "cases_updated",
    "sources_checked", "sources_failed", "actions_taken", "approval_cards_created",
    "receipts_created", "errors", "warnings", "runtime_seconds", "status", "notes",
]

BASE_PROMPT = """You are Codex acting as the research/runtime worker for Tender Export OS v4.1.
Hermes is the control plane; you are not the owner-facing approver.

NON-NEGOTIABLE SAFETY:
- No supplier/buyer messages.
- No tender/RFQ submissions or portal uploads.
- No payments, EMD, security deposit, advance, or DSC use.
- No login/captcha/paywall bypass.
- No final HSN/ITC-HS classification, origin claim, price, delivery, or payment-term commitment.
- Every opportunity/case statement must cite local files or URLs already present in the repo.
- If evidence is weak, say so; do not fabricate.

WORKDIR: {project_root}

Primary files to inspect:
- data/master_cases.csv
- data/source_health.csv
- data/agent_run_log.csv
- config/sources.gov.yaml
- config/sources.export.yaml
- outputs/source_scans/*.json and *.md
- outputs/demand_signals/*.json and *.md

Task:
{task}

Required output file: {output_file}
Write a concise markdown research report to the required output file with:
1. Demand signals found / validated
2. Top actionable cases with case_id, buyer/authority, product, deadline, source URL
3. Evidence quality and missing information
4. Source blockers / credentials needed
5. What Hermes should ask the owner to approve next
6. Explicit safety line: no external business action executed
"""

TASKS = {
    "demand-signal-audit": "Audit today's demand signals. Separate real evidence-backed GOV/EXPORT opportunities from weak/mock/internal-only rows. Recommend which top cases Hermes should deep-read or fast-kill next.",
    "source-adapter-plan": "Review source scan outputs and configs. Identify which live source adapters Codex should build or repair next, with exact expected fields/tests and source blockers.",
    "case-deep-read-plan": "Review active NEW cases and determine the next Codex deep-read tasks needed. Do not perform external portal actions; propose bounded artifact/runtime tasks only.",
}


def now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def make_run_id() -> str:
    return "RUN-" + now().strftime("%Y%m%d%H%M%S")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def append_run_log(row: dict[str, str]) -> None:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    exists = RUN_LOG.exists()
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RUN_LOG_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in RUN_LOG_FIELDS})


def run_codex(prompt_file: Path, output_file: Path, timeout: int, sandbox: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        "codex", "exec",
        "--skip-git-repo-check",
        "--sandbox", sandbox,
        "-C", str(PROJECT_ROOT),
        "-o", str(output_file),
        "-",
    ]
    prompt = prompt_file.read_text(encoding="utf-8")
    env = os.environ.copy()
    env.setdefault("TERM", "xterm-256color")
    return subprocess.run(
        cmd,
        input=prompt,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        cwd=str(PROJECT_ROOT),
        env=env,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded Tender Export research via Codex")
    parser.add_argument("--task", choices=sorted(TASKS), default="demand-signal-audit")
    parser.add_argument("--task-text", default="", help="Override task text")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--sandbox", default="danger-full-access", choices=["read-only", "workspace-write", "danger-full-access"])
    parser.add_argument("--dry-run", action="store_true", help="Write prompt only; do not invoke Codex")
    args = parser.parse_args()

    start = now()
    rid = make_run_id()
    stamp = start.strftime("%Y%m%d_%H%M%S")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = OUT_DIR / f"{args.task}_{stamp}_prompt.md"
    report_file = OUT_DIR / f"{args.task}_{stamp}_codex_research_report.md"
    final_message_file = OUT_DIR / f"{args.task}_{stamp}_codex_final_message.md"
    stdout_file = OUT_DIR / f"{args.task}_{stamp}_codex_stdout.log"
    meta_file = OUT_DIR / f"{args.task}_{stamp}_metadata.json"

    task_text = args.task_text.strip() or TASKS[args.task]
    prompt = BASE_PROMPT.format(
        project_root=PROJECT_ROOT,
        task=task_text,
        output_file=rel(report_file),
    )
    prompt_file.write_text(prompt, encoding="utf-8")

    status = "DRY_RUN"
    errors = 0
    warnings = 0
    returncode = None
    if args.dry_run:
        stdout_file.write_text("dry-run: Codex not invoked\n", encoding="utf-8")
    else:
        try:
            proc = run_codex(prompt_file, final_message_file, args.timeout, args.sandbox)
            returncode = proc.returncode
            stdout_file.write_text(proc.stdout, encoding="utf-8")
            if proc.returncode == 0 and report_file.exists() and report_file.stat().st_size > 0:
                status = "SUCCESS"
            else:
                status = "FAILED"
                errors = 1
        except subprocess.TimeoutExpired as exc:
            stdout_file.write_text((exc.stdout or "") + "\nTIMEOUT\n", encoding="utf-8")
            status = "TIMEOUT"
            errors = 1
        except Exception as exc:  # noqa: BLE001
            stdout_file.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
            status = "FAILED"
            errors = 1

    elapsed = int((now() - start).total_seconds())
    meta = {
        "run_id": rid,
        "task": args.task,
        "status": status,
        "returncode": returncode,
        "prompt_file": rel(prompt_file),
        "report_file": rel(report_file),
        "final_message_file": rel(final_message_file),
        "stdout_file": rel(stdout_file),
        "sandbox": args.sandbox,
        "dry_run": args.dry_run,
        "runtime_seconds": elapsed,
        "safety": "codex_research_only_no_external_business_action",
    }
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    append_run_log({
        "run_id": rid,
        "run_date": start.strftime("%Y-%m-%d"),
        "run_time": start.strftime("%H:%M:%S"),
        "agent_name": "codex_research_handoff",
        "trigger_type": "hermes_routed_research_to_codex",
        "cases_processed": "0",
        "cases_created": "0",
        "cases_rejected": "0",
        "cases_updated": "0",
        "sources_checked": "0",
        "sources_failed": "0",
        "actions_taken": f"codex_{args.task}_handoff",
        "approval_cards_created": "0",
        "receipts_created": "1",
        "errors": str(errors),
        "warnings": str(warnings),
        "runtime_seconds": str(elapsed),
        "status": status,
        "notes": f"Codex research handoff task={args.task}; report={rel(report_file)}; final={rel(final_message_file)}; stdout={rel(stdout_file)}; no external business action authorized.",
    })

    print(json.dumps(meta, indent=2))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
