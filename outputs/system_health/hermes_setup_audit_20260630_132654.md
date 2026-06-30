# Hermes Setup Audit - 2026-06-30 13:26 IST

Scope: read-only audit of Hermes setup for Tender Export OS workspace.

## Summary

Hermes is installed and the Tender Export OS board exists, but the operating loop is not healthy enough to reliably surface demand signal.

The main broken items are:

1. Hermes gateway service is installed but stopped.
2. Hermes cron jobs are active but will not fire automatically while the gateway is stopped.
3. TenderOS scheduled jobs are delivering `local`, while workspace config and mobile setup docs say scheduled delivery should go to Telegram.
4. The external intake script cannot run under the current workspace Python environment because required packages are missing.
5. The Hermes board has many unassigned case tasks, so work can sit without a responsible profile.
6. Hermes config is outdated by one migration version.

## Evidence

- `hermes --version`: Hermes Agent v0.17.0, Python 3.11.14, update available.
- `ares-hermes --version`: Hermes Agent v0.14.0.
- `hermes doctor`: core runtime OK, config version outdated v31 to v32, OpenAI Codex auth OK, Telegram configured, orphan alias `hiral`.
- `hermes status`: Telegram configured, Gateway Service installed but stopped, 11 active scheduled jobs.
- `hermes cron status`: gateway not running, cron jobs will not fire automatically.
- `hermes cron list`: 11 active jobs; TenderOS jobs exist but show `Deliver: local`.
- `config/hermes_cron.yaml`: `owner_gateway: telegram`, `deliver_scheduled_briefs_to_telegram: true`, and job command hints use `--deliver telegram`.
- `docs/MOBILE_DELIVERY_SETUP.md`: current scheduled delivery target documented as `telegram`.
- `python3 scripts/run_external_task_intake.py --help`: fails with `ModuleNotFoundError: No module named 'requests'`.
- Hermes venv Python also fails external intake with `ModuleNotFoundError: No module named 'bs4'`.
- `hermes kanban --board tender-export-os stats`: board exists with blocked=7, done=5, ready=1, todo=25.
- `hermes kanban --board tender-export-os list`: many case tasks are unassigned; one ready task is unassigned: `EXP-20260630-002 - Buyer verification draft`.
- `hermes logs gateway`: repeated `API_SERVER_KEY is required` errors for API server component; gateway later received SIGTERM on 2026-06-29 15:43 IST and stopped.

## Not Broken

- Hermes CLI is present at `/Users/raghav/.local/bin/hermes`.
- Ares Hermes CLI is present at `/Users/raghav/.ares/bin/ares-hermes`.
- Tender Export OS Kanban board exists.
- Telegram is configured in Hermes status.
- Register and event schema validation passed.
- No active Kanban diagnostics were reported.
- Demand rows exist in `data/master_cases.csv`; current issue is surfacing/orchestration, not total absence of leads.

## Root Cause For No Visible Demand Signal

The demand signals are entering local registers, but Hermes is not reliably delivering them to the owner loop:

- Cron scheduler is not firing because gateway is stopped.
- Actual scheduled jobs deliver locally, not to Telegram.
- External intake dependencies are not consistently installed in the runtime used by the scripts.
- Kanban has unassigned tasks, so case work can wait without a profile owner.

## Recommended Fixes

Stage these as internal maintenance tasks before expecting reliable demand signal:

1. Start/repair Hermes gateway after confirming owner approval for service restart.
2. Run `hermes doctor --fix` or `hermes setup` to migrate config v31 to v32.
3. Align TenderOS cron delivery with the intended Telegram target, or explicitly change docs/config back to local delivery.
4. Install or vendor runtime dependencies for `scripts/run_external_task_intake.py`: `requests`, `PyYAML`, and `beautifulsoup4`.
5. Assign unassigned TenderOS Kanban tasks to the correct profiles using `config/kanban_board.yaml` roles.
6. Decide whether API server should be disabled or configured with `API_SERVER_KEY`; current logs show repeated API server retries.
7. Clean stale Hermes dashboard/slash-worker processes only after confirming which sessions are active, to avoid disrupting live chat.

## Safety

No Hermes service restart, cron edit, gateway send, external supplier/buyer contact, approval decision, payment, DSC action, source login, or credential-heavy plugin activation was performed in this audit.
