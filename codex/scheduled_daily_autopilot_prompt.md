# Scheduled Prompt — Tender Export OS Daily Autopilot

**Date:** 2026-06-30  
**Agent Name:** agent_loop_scheduler  
**Sources Used:** `config/agent_loops.json`, `config/loop_schedule.json`, `config/approval_policy.yaml`, `workflows/agent_loop_runtime.md`, `workflows/daily_autopilot.md`

Run the Tender + Export OS morning schedule for this workspace.

## Required Preflight

1. Run `python3 scripts/validate_agent_loops.py`.
2. Run `python3 scripts/validate_loop_schedule.py`.
3. If either validator fails, stop, append an `agent_run_log.csv` row with `PARTIAL_FAILURE`, and include the blocker in the owner brief if possible.

## Schedule To Follow

Use `config/loop_schedule.json` schedule `daily_morning_autopilot`.

Execute only the internal scheduled phases that are due:

1. `source_scan_loop`
2. `case_progression_loop` for Fast Kill
3. `case_progression_loop` for Deep Read
4. `supplier_proof_loop`
5. `compliance_draft_loop`
6. `pricing_pack_approval_loop`
7. `approval_gate_loop`
8. `owner_briefing_loop`

## Hard Stops

Do not:

- send supplier quote requests
- send buyer replies
- send export quotations
- submit bids
- upload tender documents
- use DSC
- commit price, delivery, or payment terms
- confirm HSN/ITC-HS or country of origin
- pay EMD, security, advance, or supplier amounts
- bypass CAPTCHA or portal terms

When a gated action is needed, create or refresh the approval card and stop at `APPROVAL_REQUIRED`.

## Required Outputs

- Updated internal ledgers only when evidence supports updates
- Any new case reports under `outputs/case_reports/{case_id}/`
- Approval cards under `receipts/approvals/` when required
- Daily brief under `outputs/daily_briefs/brief_YYYYMMDD.html`
- One append-only row per phase in `data/agent_run_log.csv`

## Final Run Summary

Report:

- validators passed or failed
- cases created
- cases updated
- cases blocked
- approval cards created
- daily brief path
- any sources skipped due to paywall, login, CAPTCHA, or unreadable documents
