# 14-Day Shadow Pilot Runbook

The shadow pilot measures whether Tender Export OS specialist profiles can improve throughput and quality without receiving new external authority.

## Contract

Config: `config/shadow_pilot.yaml`

Mode: `SHADOW_ONLY`

Duration: 14 days

Allowed internal work:

- read
- research
- draft
- create internal artifacts
- update approved internal projections
- block Kanban tasks
- complete Kanban tasks

Prohibited work:

- buyer or supplier contact
- email send
- portal submit or upload
- payment
- DSC or e-signature
- purchase order
- final price, delivery, classification, origin, legal, or compliance commitment
- public service exposure

## Daily command

Activate a clean pilot window once before measuring:

```bash
python3 scripts/generate_shadow_pilot_report.py --activate --date YYYYMMDD --json
```

This writes `data/shadow_pilot_state.json` and excludes historical runs before the activation date from the pilot pass/fail decision.

Run after the day’s internal work:

```bash
python3 scripts/generate_shadow_pilot_report.py --date YYYYMMDD --json
```

The command writes:

- `outputs/shadow_pilot/shadow_pilot_YYYYMMDD.json`
- `outputs/shadow_pilot/shadow_pilot_YYYYMMDD.html`

Use `--ignore-state` only for legacy rolling-window diagnostics.

## What the report measures

- owner-time estimate
- run/task success rate
- qualified opportunity throughput
- evidence completeness
- policy violations
- cost telemetry when available
- task/model latency
- external-action markers inside the shadow window
- daily probe and matching evaluation coverage for every configured profile
- comparison with the prior baseline window

## Completion rule

TASK-092 is complete only after a clean 14-day measured window exists.

A clean shadow-pilot window means:

- report status is `PASS`;
- explicit activation state exists in `data/shadow_pilot_state.json`;
- no external-action markers are detected;
- no policy violations are detected;
- every calendar day in the active window has one local-only probe and one matching evaluation for every configured profile; repeated runs on the same day do not add credit;
- production routing remains disabled;
- owner has reviewed the result.

TASK-092 does not enable live production routing. Passing TASK-092 only creates evidence for TASK-093.
