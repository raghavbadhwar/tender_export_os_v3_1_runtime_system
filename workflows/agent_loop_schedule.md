# Agent Loop Schedule

**Date:** 2026-06-30  
**Agent Name:** agent_loop_scheduler  
**Primary v4 Schedule Spec:** `config/hermes_cron.yaml`  
**Legacy Loop Spec:** `config/loop_schedule.json`  
**Timezone:** Asia/Kolkata

## v4 Hermes Cron Schedule

Hermes cron is the first scheduler. External schedulers are fallback only.

| Time IST | Job | Runtime | Purpose | Hard Stop |
|---|---|---|---|---|
| 08:30 daily | Morning Operator Brief | Hermes default | Read Knowledge Bus, Kanban, memory, approvals, source/plugin health; produce owner brief | No external forwarding unless gateway configured |
| 13:00 daily | Midday Opportunity Radar | Hermes + Codex when needed | Scan GOV/EXPORT sources, create cases, fast-kill, deep-read top cases | CAPTCHA, paywall, login, duplicate, approval gate |
| 17:00 daily | Supplier Follow-up Review | Hermes default | Check pending quote proofs and supplier blockers | No reminders or sends without approval |
| 20:30 daily | Evening Execution Close | Hermes default | Close day, update Kanban, list blockers, tomorrow first action | No new external actions |
| Friday 18:00 | Weekly Learning Review | Hermes + ChatGPT snapshot | Review wins/losses/rejections/source/supplier/pricing/corrections | Stage changes only unless approved |
| Owner-approved monthly | Strategy Deep Research | ChatGPT Project | Deep research on categories, sources, and business model changes | No operational execution |

Use `hermes cron --help` before creating local jobs because exact CLI syntax may differ by Hermes version.

## Sources Used

- `config/agent_loops.json`
- `workflows/agent_loop_runtime.md`
- `workflows/daily_autopilot.md`
- `config/approval_policy.yaml`
- `data/master_cases.csv`
- `data/agent_run_log.csv`
- `data/approvals_receipts.csv`

## Operating Rules

- All scheduled runs are supervised internal operations.
- `case_id` remains the primary state key.
- Every phase appends to `data/agent_run_log.csv`.
- Approval-gated actions stop at an approval card.
- No scheduled run may send, submit, upload, pay, use DSC, commit price or terms, confirm HSN/ITC-HS, or claim origin without explicit approval.
- Validators must pass before scheduled loops run:

```bash
python3 scripts/validate_agent_loops.py
python3 scripts/validate_loop_schedule.py
```

## Legacy Compatibility Schedule

The older `config/loop_schedule.json` remains valid for bounded-loop tests and compatibility. For v4 operations, prefer `config/hermes_cron.yaml` and the Hermes cron schedule above.

Schedule ID: `daily_morning_autopilot`  
Cadence: Daily at 06:00 IST. On weekends, run brief-only unless manually overridden.  
Max runtime: 210 minutes.

| Time IST | Loop | Phase | Purpose | Hard Stop |
|---|---|---|---|---|
| 05:55 | `daily_autopilot_supervised_loop` | preflight | Validate loop and schedule registries | Any validator failure |
| 06:00 | `source_scan_loop` | radar_scan | Scan active GOV and EXPORT sources | CAPTCHA, paywall, login, duplicate |
| 06:30 | `case_progression_loop` | fast_kill | Score NEW cases and reject clear non-starters | Missing data cannot be used as rejection proof |
| 07:00 | `case_progression_loop` | deep_read | Extract surviving cases and documents | Unreadable docs or ambiguous eligibility |
| 07:30 | `supplier_proof_loop` | supplier_search | Research suppliers using 5-3-2 rule | Quote request send requires approval |
| 08:00 | `compliance_draft_loop` | export_compliance | Draft export compliance notes | SCOMET, prohibited category, final HSN/origin claim |
| 08:15 | `pricing_pack_approval_loop` | pricing_and_pack | Build pricing and packs where proof exists | Fewer than 2 quote proofs or price commitment |
| 08:50 | `approval_gate_loop` | approval_queue_refresh | Create or refresh approval cards | Never pre-fill owner decision |
| 09:00 | `owner_briefing_loop` | daily_owner_brief | Generate owner brief | No external forwarding |

## Intra-day Monitor

Schedule ID: `intra_day_monitor`  
Cadence: Weekdays at 11:00, 15:00, and 18:00 IST.  
Max runtime: 45 minutes.

| Time IST | Loop | Phase | Purpose | Hard Stop |
|---|---|---|---|---|
| 11:00 / 15:00 / 18:00 | `approval_gate_loop` | pending_approval_check | Check pending approvals | No inferred approval |
| 11:00 / 15:00 / 18:00 | `supplier_proof_loop` | quote_response_monitor | Track quote proof gaps | No external reminders without approval |
| 11:00 / 15:00 / 18:00 | `execution_tracker_loop` | approved_action_tracker | Track approved actions and receipts | New external action needs new approval |

## Weekly System Review

Schedule ID: `weekly_system_review`  
Cadence: Mondays at 09:30 IST.  
Max runtime: 45 minutes.

| Time IST | Loop | Phase | Purpose | Hard Stop |
|---|---|---|---|---|
| 09:30 | `daily_autopilot_supervised_loop` | schedule_and_registry_audit | Audit schedule, loop registry, stale cases, source health | Recommend changes only |
| 09:50 | `owner_briefing_loop` | weekly_owner_summary | Summarize schedule health and blockers | No external forwarding |

## Event-driven Triggers

These are not clock-based. They run only when internal evidence or an explicit owner decision appears.

| Trigger | Loop | Phase | Purpose | Hard Stop |
|---|---|---|---|---|
| New document uploaded | `case_progression_loop` | document_reprocess | Deep read one case again | No unsupported eligibility claim |
| Quote proof received | `pricing_pack_approval_loop` | pricing_trigger | Price one case if 2 quote proofs exist | No final price commitment |
| Owner decision recorded | `approval_gate_loop` | owner_decision_route | Record Approve / Reject / Ask Changes | Ambiguous owner response |
| Approved action needs tracking | `execution_tracker_loop` | receipt_follow_up | Track one approved action | Missing approval reference |

## Codex App Automation Targets

Three app-level cron automations are active or intended:

1. `Tender Export OS Daily Autopilot`
   - Automation ID: `tender-export-os-daily-autopilot`
   - Uses `codex/scheduled_daily_autopilot_prompt.md`
   - Runs the daily morning schedule.

2. `Tender Export OS Intra-day Monitor`
   - Automation ID: `tender-export-os-intra-day-monitor`
   - Uses `codex/scheduled_intraday_monitor_prompt.md`
   - Runs the approval, quote proof, and execution monitor.

3. `Tender Export OS Weekly System Review`
   - Automation ID: `tender-export-os-weekly-system-review`
   - Uses `codex/scheduled_weekly_system_review_prompt.md`
   - Runs the weekly schedule, stale-case, source-health, plugin-health, and approval-gate audit.

Event-driven triggers remain manual or owner-commanded. They are not clock-based automations.

## Simulated Test Result

| Test | Result |
|---|---|
| Every loop is scheduled or event-triggered | Pass |
| Every scheduled entry has a runtime limit | Pass |
| Schedule references only valid loop names | Pass |
| Approval gates remain enforced | Pass |
| Daily job has preflight validation | Pass |
| Intra-day monitor cannot send reminders externally | Pass |
| Weekly review cannot patch schedules or skills without approval | Pass |
| Event-driven owner decision requires explicit choice | Pass |

## Critic Score

Score: 95/100

| Area | Score | Note |
|---|---:|---|
| Requirements coverage | 20/20 | All loop registry items are scheduled, app-targeted, or event-triggered |
| Architecture fit | 14/15 | Daily, intra-day, weekly, and event-driven slots match operational cadence |
| Tool safety | 20/20 | All risky actions remain approval-gated |
| Stop condition clarity | 14/15 | Runtime and validation stops are explicit |
| Memory/privacy fit | 9/10 | Uses current ledgers and avoids credentials |
| Eval strength | 9/10 | Validator and simulated tests cover scheduled and gated failure paths |
| Handoff completeness | 9/10 | App automation targets and prompts are complete; event triggers remain owner-commanded |

## Final Handoff Package

- `config/loop_schedule.json`
- `workflows/agent_loop_schedule.md`
- `scripts/validate_loop_schedule.py`
- `codex/scheduled_daily_autopilot_prompt.md`
- `codex/scheduled_intraday_monitor_prompt.md`
- `codex/scheduled_weekly_system_review_prompt.md`
