# Scheduled Prompt — Tender Export OS Intra-day Monitor

**Date:** 2026-06-30  
**Agent Name:** agent_loop_scheduler  
**Sources Used:** `config/agent_loops.json`, `config/loop_schedule.json`, `config/approval_policy.yaml`, `workflows/agent_loop_runtime.md`

Run the Tender + Export OS intra-day monitor for this workspace.

## Required Preflight

1. Run `python3 scripts/validate_agent_loops.py`.
2. Run `python3 scripts/validate_loop_schedule.py`.
3. If either validator fails, stop and append an `agent_run_log.csv` row with `PARTIAL_FAILURE`.

## Schedule To Follow

Use `config/loop_schedule.json` schedule `intra_day_monitor`.

Run only internal monitoring:

1. `approval_gate_loop` for pending approval queue checks
2. `supplier_proof_loop` for quote proof tracking only
3. `execution_tracker_loop` for approved-action tracking only

## Hard Stops

Do not:

- infer owner approval from silence
- send reminders externally
- resend quote requests
- resubmit bids
- escalate to buyers or suppliers
- change prices, payment terms, or delivery timelines
- execute any action without an approval reference

If a new external action is needed, create or refresh an approval card and stop.

## Required Outputs

- Updated internal tracking ledgers only when evidence supports updates
- Receipts for verified approved actions only
- Run log rows in `data/agent_run_log.csv`
- Blockers listed for the next owner brief

## Final Run Summary

Report:

- pending approvals checked
- quote proof gaps
- approved actions tracked
- receipts created
- blockers requiring owner decision
