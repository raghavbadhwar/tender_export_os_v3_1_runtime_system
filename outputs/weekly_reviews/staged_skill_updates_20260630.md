# Staged Skill Update Proposals — Tender Export Operator

Generated at: 2026-06-30T13:11:58+05:30
Task: `t_50fcbad9`
Status: staged only. No skill was patched in this run because owner approval is required before writing skills.

## Proposed target

Hermes skill: `tender-export-operator`

## Proposal 1 — Expand weekly learning review inputs

Add `data/events.jsonl`, `data/drive_manifest.csv`, `outputs/system_health/hermes_kanban_reconciliation_plan.json`, current Hermes Kanban board state, and recent ChatGPT bridge packets to the Weekly Learning Review input checklist.

Reason: this review found material learning in the event ledger, Drive/Telegram receipts, and Kanban DB that was not visible from case CSVs alone.

## Proposal 2 — Add Kanban deadlock/unassigned-task check

Add a weekly-review step: inspect the Tender Export OS Kanban board for unassigned tasks, blocked approval tasks, stale running tasks, and task graphs whose dependent tasks cannot dispatch. If unassigned/deadlocked tasks exist, stage a board repair task for `hermes-chief-operator` or the correct specialist profile before declaring the system healthy.

Evidence this week: read-only query of `/Users/raghav/.hermes/kanban/boards/tender-export-os/kanban.db` found 24 unassigned `todo` tasks and 4 blocked tasks, including owner-approval gates and operational blockers.

## Proposal 3 — Quote-proof reconciliation rule

Add a rule to supplier/pricing review: quote-proof counts must come from `data/quote_master.csv` and case evidence receipts, not from narrative `agent_run_log.csv` notes alone. If run-log notes and quote register disagree, block pricing and log a correction before any price/quote pack work.

Evidence this week: `RUN-004` said three quotes were received for `EXP-20260630-001`, but `data/quote_master.csv` contains one quote proof (`Q-002`). The audit corrected the case to supplier search incomplete and prepared APR-003 without sending anything.

## Proposal 4 — Approval-card completeness guard

Add a weekly/daily brief check: pending approval cards with missing concrete risk or recovery/rollback fields should be surfaced as `Ask Changes` candidates, not recommended for approval.

Evidence this week: the generated daily brief displayed missing risk/recovery text for APR-001, APR-002, and APR-003, while the approval policy requires both fields.

## Sources

- `workflows/weekly_learning_flow.md`
- `data/master_cases.csv`
- `data/approvals_receipts.csv`
- `data/agent_run_log.csv`
- `data/quote_master.csv`
- `data/plugin_health.csv`
- `data/events.jsonl`
- `/Users/raghav/.hermes/kanban/boards/tender-export-os/kanban.db` read-only status query
- `outputs/case_reports/EXP-20260630-001/audit_EXP-20260630-001.md`
- `outputs/daily_briefs/brief_20260630.html`
