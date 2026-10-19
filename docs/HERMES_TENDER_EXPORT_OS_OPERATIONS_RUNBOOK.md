# Hermes Tender Export OS Operations Runbook

This runbook is the operator reference for the Tender Export OS Hermes control plane.

## 1. Start / status checks

```bash
hermes status
hermes gateway status
hermes doctor
python3 scripts/check_runtime_slos.py --json
```

Expected:

- Hermes profile `tender-export-os` exists.
- Gateway is running.
- Runtime SLO report is `PASS`.
- Exception cards are zero or actively assigned.

## 2. Stop / safe pause

Do not kill active work blindly. First inspect:

```bash
hermes kanban --board tender-export-os list --json
hermes cron status
```

Pause only after confirming no approved execution is in progress. External sends, submissions, payments, uploads, DSC, and final commitments always remain owner-gated.

## 3. Recovery

Run:

```bash
python3 scripts/run_disaster_recovery_drill.py --json
```

Use the latest report under:

```text
outputs/disaster_recovery_drill/
```

Canonical recovery source is `data/events.jsonl`. Rebuilt projections go to a temporary output folder first. Never write rebuilt projections back to `data/*.csv` until reviewed.

## 4. Profile provisioning / validation

```bash
python3 scripts/validate_profile_operating_budgets.py --json
python3 scripts/validate_profile_behavioral_gate.py --json
python3 scripts/validate_specialist_profiles.py
```

Profiles remain shadow-only until:

- behavioral gate passes;
- shadow pilot passes;
- production routing gate passes;
- owner review approves routing.

## 5. Auth renewal

Check:

```bash
hermes auth status openai-codex
python3 scripts/revalidate_drive_knowledge_bus_sync.py --json
```

Gmail operations must use the Gmail plugin only. Do not use gws, IMAP, Himalaya, or browser Gmail for Gmail operations.

## 6. Kanban dispatch

Inspect:

```bash
hermes kanban --board tender-export-os list --json
```

Allowed board work is internal routing, evidence review, drafts, and task completion/blocking. The board itself does not authorize external effects.

## 7. Cron repair

Check:

```bash
hermes cron status
python3 scripts/validate_live_cron_installation.py --json
python3 scripts/check_runtime_slos.py --json
```

`config/hermes_cron.yaml` is the desired state. The live Hermes profile has a separate scheduler store, so `validate_live_cron_installation.py` must pass before treating a configured job as deployed. It checks the live no-agent job, wrapper name, schedule, work directory, and no-agent mode for every non-manual configured job.

If the validator reports a missing job:

1. Restore or create the matching profile wrapper named by `hermes_script` in `config/hermes_cron.yaml`. It must only call `teos_cron_runner.run_job("<job_id>")`.
2. Validate the supervised command without running it:

   ```bash
   python3 scripts/teos_job_supervisor.py --job-id JOB_ID --dry-run --json
   ```

3. Create the job as a local, no-agent Hermes cron job using the configured cadence, `hermes_name`, and `hermes_script`; preserve `dir:/Users/raghav/Downloads/tender_export_os_v3_1_runtime_system` as its work directory.
4. Trigger one safe internal run only when its stop condition permits it, then rerun the installation validator and check the resulting receipt under `receipts/job_runs/JOB_ID/`.

If cron is stale, repair the deterministic script first. Agent-backed cron is only for durable Kanban review cards; the scheduler enqueuer itself remains no-agent and performs no external action.

## 8. MCP diagnosis

```bash
python3 scripts/check_mcp_discovery_reliability.py
python3 scripts/check_runtime_slos.py --json
```

If MCP discovery fails, keep production routing disabled and use local scripts until the health check passes.

## 9. Connector ambiguity

Ambiguous connector state blocks execution.

Gmail:

```bash
python3 scripts/generate_gmail_plugin_outbox.py
```

Packets are written only after `config/gmail_send_preflight.yaml` passes.

Drive:

```bash
python3 scripts/revalidate_drive_knowledge_bus_sync.py --json
```

If auth is blocked, keep Drive sync dry-run only.

Contact form:

```bash
python3 scripts/validate_contact_form_lane.py --json
python3 scripts/validate_contact_form_connector_design.py --json
```

The lane remains disabled until a separate approved connector design exists.

Final readiness:

```bash
python3 scripts/run_production_readiness_gate.py --json
python3 scripts/generate_final_readiness_receipt.py --json
python3 scripts/generate_owner_action_packet.py --json
python3 scripts/record_production_readiness_signoff.py --approved-by OWNER_NAME --json
```

The aggregate readiness gate is the canonical one-command check. It regenerates safe local receipts, emits the owner-action packet, and leaves production routing disabled. The signoff recorder refuses to write `receipts/production_readiness/owner_signoff.json` while any readiness blocker remains.

## 10. Approval expiry

Review:

```bash
python3 scripts/generate_operating_desk_report.py --date YYYYMMDD --no-log
```

Expired or ambiguous approval requires a fresh approval card. Do not reuse stale approval for sends, submissions, prices, delivery commitments, classification, origin, payments, or DSC.

## 11. Outcome recording

Use explicit evidence ingestion scripts:

```bash
python3 scripts/record_export_execution_milestone.py --help
python3 scripts/record_gov_execution_milestone.py --help
```

Outcomes require evidence. WON/LOST/ORDER_RECEIVED/SUBMITTED states must not be inferred from weak text.

## 12. Model rollback

Model/fallback changes must be recorded in config and validated by behavioral evaluation:

```bash
python3 scripts/evaluate_hermes_behavioral_contracts.py --validate-only --json
python3 scripts/validate_profile_behavioral_gate.py --json
```

If behavior regresses, return profiles to shadow.

## 13. Skill rollback

Agent-created skills and memory writes require approval. If a skill causes unsafe behavior:

- disable the skill from the profile bundle;
- run behavioral evaluation;
- create a learning proposal instead of silently patching live behavior.

## 14. Incident escalation

Escalate to owner when any of these occur:

- external action ambiguity;
- connector state ambiguity;
- policy violation;
- duplicate send/submission/payment risk;
- missing evidence for a commercial/compliance claim;
- Computer Use display/session blocker;
- Drive auth failure for required context sync;
- runtime SLO failure.

## 15. Non-negotiable boundaries

Never execute without owner approval:

- buyer or supplier message send;
- tender bid submission;
- portal upload;
- DSC/e-signature;
- EMD/security/advance/payment;
- supplier PO or commercial commitment;
- final price, payment, delivery, HSN/ITC-HS, origin, certification, legal, or tax claim.
