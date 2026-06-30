# Scheduled Prompt - Tender Export OS Weekly System Review

**Date:** 2026-06-30
**Agent Name:** agent_loop_scheduler
**Sources Used:** `config/agent_loops.json`, `config/loop_schedule.json`, `config/approval_policy.yaml`, `workflows/agent_loop_runtime.md`, `workflows/agent_loop_schedule.md`

Run the Tender + Export OS weekly system review for this workspace.

## Required Preflight

1. Run `python3 scripts/validate_agent_loops.py`.
2. Run `python3 scripts/validate_loop_schedule.py`.
3. If either validator fails, stop and append an `agent_run_log.csv` row with `PARTIAL_FAILURE`.

## Schedule To Follow

Use `config/loop_schedule.json` schedule `weekly_system_review`.

Run only internal audit and briefing work:

1. `daily_autopilot_supervised_loop` for `schedule_and_registry_audit`.
2. `owner_briefing_loop` for `weekly_owner_summary`.

## Audit Scope

Check:

- loop registry and schedule registry drift
- stale active cases
- stale approval cards
- stale supplier quote proof gaps
- repeated source health failures
- repeated plugin health failures
- missing run-log rows
- approval-gate consistency
- event-ledger and CSV projection consistency where local scripts support it

## Hard Stops

Do not:

- send, submit, upload, pay, or use DSC
- contact suppliers, buyers, tender portals, or public services
- enable credential-heavy plugins
- patch pricing or compliance skills without approval
- change recurring schedules automatically
- write owner approval decisions
- treat ChatGPT or plugin output as final compliance authority

When a change is needed, create a recommendation or approval card and stop.

## Required Outputs

- Schedule and loop validation result
- Weekly owner summary under `outputs/daily_briefs/brief_YYYYMMDD.html` or the closest existing weekly summary target
- Any source/plugin health notes supported by evidence
- Recommended schedule, skill, memory, or policy changes as staged proposals only
- One append-only row per weekly review phase in `data/agent_run_log.csv`

## Final Run Summary

Report:

- validators passed or failed
- stale cases found
- stale approvals found
- source or plugin health blockers
- proposed schedule or loop changes
- owner action needed
