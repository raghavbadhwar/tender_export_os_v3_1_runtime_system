# Recovered Hermes Context Audit - 2026-07-12

## Supplied source

The owner supplied:

`/Volumes/ANUJ SSD 2/RAGHAV2_RECOVERED_FINAL_2026-07-11/CONSOLIDATED_ORIGINAL_TREE/hermes/`

It is a recovered Hermes source checkout customized as **Ares Wholesale AIOS**, version `0.14.0`. It is not the old live Hermes profile home and should not replace the current `0.18.2` installation.

## Useful continuity recovered

The source contains durable design decisions worth carrying forward:

- build a vertical application/plugin layer rather than hard-forking Hermes core;
- keep deterministic business state outside generic conversational memory;
- require multiple observations before saving a business pattern;
- use self-contained cron jobs and explicit work directories;
- default execution adapters to dry-run;
- require owner approval before external or ledger-impacting actions;
- persist action results and failures as audit records;
- use atomic writes for durable local state.

These patterns informed the Tender profile, event ledger, supervised cron jobs, memory rules, approval boundary, and forecast calibration changes.

## Runtime-state search

The supplied recovered source tree is not a live profile backup. A separate surviving local runtime was subsequently found at `~/.ares`:

- `~/.ares/state.db` contains 52 legacy sessions and 754 messages dated 2026-05-23 through 2026-05-26, plus later Tender owner-brief messages inside a Telegram session;
- `~/.ares/memories/MEMORY.md` and `USER.md` contain a small AIOS path note plus personal/fitness/Nectra preferences;
- `~/.ares/profiles/a-soul/` contains an older revenue-operator identity and settings;
- `~/.ares/cron/jobs.json` contains old fitness and Tender schedules;
- `~/.ares/clients/demo-wholesaler/` contains demo invoices, mock GST work, and connector fixtures rather than verified live business state.

This state is valuable as a historical archive, but it is not safe to merge wholesale into the isolated Tender profile. The old `Tom`/`A. Soul` identity, health schedules, generic wholesaler fixtures, mock GST records, and stale connector state would contaminate Tender operations. Credentials, `.env` files, cookies, auth state, and platform tokens are explicitly excluded from migration.

The legacy session database is therefore preserved separately under the current profile and exposed through the bounded, read-only search command in `scripts/search_recovered_ares_context.py`. Tool messages are excluded by default. Recovered statements remain historical evidence until reverified.

Legacy command wrappers were handled the same way. Ten Tender specialist aliases now route to the unified `tender-export-os` profile. The unrelated `a-soul`, `hiral`, and `monkey` persona wrappers are preserved under `recovered-context/legacy-aliases-20260712/` but are inactive, preventing identity or workflow leakage into Tender operations.

## Safe recovery decision

The current `tender-export-os` profile remains authoritative. The source checkout is design evidence; the preserved legacy database is on-demand historical evidence. Tender-specific durable state remains in the repository event stream, receipts, current Hermes profile, and current Kanban board.

Recovery routing and promotion rules are recorded in `config/recovered_context.yaml`. The active profile receives only compact, Tender-relevant memory entries and a local skill for provenance-aware archive search.
