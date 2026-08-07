# Hermes-Native Maximum-Capability Setup

## Outcome

Tender Export OS uses one isolated Hermes profile, `tender-export-os`, as its durable control plane. The profile is anchored to this repository, supervised by launchd, connected to a persistent Hermes Kanban board, equipped with six Tender domain skills, and scheduled through nine no-agent supervised jobs.

This keeps deterministic collection, validation, projection, monitoring, and reporting out of the LLM loop. Hermes is reserved for judgment, routing, explanation, Kanban orchestration, bounded delegation, and owner-facing decisions.

## Verified runtime snapshot

Verified on 2026-07-12:

- Hermes Agent `0.18.2` from the current NousResearch installation.
- Hermes Desktop rebuilt locally from backend commit `4281151a`; the prior app bundle is retained for rollback.
- Profile home: `/Users/raghav/.hermes/profiles/tender-export-os`.
- Workspace: `/Users/raghav/Downloads/tender_export_os_v3_1_runtime_system`.
- Gateway: launchd-supervised service `ai.hermes.gateway-tender-export-os`.
- Cron: nine active no-agent jobs; every job calls the repository supervisor and produces an immutable receipt plus event pair. The added jobs capture core sources through agent-browser and monitor Gmail-plugin reply packets.
- Kanban: board `tender-export-os`, dispatcher embedded in the gateway, one in-progress task per profile and two globally.
- Skills: 87 enabled profile skills at the upgrade baseline, including `teos-chief-operator`, `teos-evidence-verifier`, `teos-prediction-calibration`, `teos-buyer-acquisition`, `teos-recovered-context`, and `teos-public-web-scraping`, with those six governed operating skills bundled as `/teos-ops`.
- Compatibility commands: the former Tender specialist aliases (`hermes-chief-operator`, `gov-tender-radar`, `export-rfq-radar`, `supplier-sourcing`, `pricing-compliance`, `sales-followup`, `learning-review`, `source-health`, `codex-artifact-factory`, and `chatgpt-boardroom-handoff`) now route to this unified profile. Unrelated legacy persona aliases remain archived and inactive.
- Profile boundary: those compatibility commands are shell wrappers, not Hermes profiles. The current on-disk business profiles are `brained`, `freshos`, and `tender-export-os`; specialist isolation is not present until the planned specialist profiles are provisioned and validated.
- Profile memory: `memories/MEMORY.md` and `memories/USER.md` both exist under the Tender profile. Built-in memory is active; no external memory provider is configured.
- Hook: `teos-event-bridge`, recording privacy-safe lifecycle metadata in `data/events.jsonl`.
- Web discovery: DDGS is installed as the no-key search fallback; exact evidence capture still uses agent-browser/Python because DDGS is search-only.
- Web scraping: `scripts/public_web_evidence_scraper.py` handles robots-aware, rate-limited public static HTML and bounded same-host crawling with raw HTML, structured JSON/text, final URLs, blockers, and hashes. JavaScript pages route to the existing agent-browser evidence lane.
- Plugin hardening: the focused `security-guidance` plugin is enabled; credential-heavy or broad plugin activation remains opt-in.
- Computer Use: `cua-driver` 0.7.1 is installed, and macOS Accessibility plus Screen Recording are granted to `CuaDriver.app`.
- Model resilience: the primary remains `gpt-5.6-terra`; verified `gpt-5.5` on the same OpenAI Codex OAuth account is the first fallback for rate limits, overload, service errors, or connection failures.
- Rollback safety: Hermes filesystem checkpoints are enabled with 12 snapshots per project, a 300 MB total cap, 10 MB per-file cap, seven-day retention, and automatic pruning. A live canary created one restorable checkpoint in 3.5 seconds using 1.19 MB. A local bug fix makes Hermes' 50,000-file guard count files rather than directory entries.
- Deterministic Gmail boundary: browser/web access to `mail.google.com` and `gmail.com` is blocked in Hermes, and terminal use of `gws` or Himalaya is denied even under YOLO. Google Drive and public Tender sources remain available.
- Behavioral reliability: `scripts/evaluate_hermes_behavioral_contracts.py` runs nine critical approval/evidence/injection cases three times with only the `clarify` toolset. The verified run passed 27/27 cases, including the rule that an OPA `allowed` probe is not execution when no execution tool exists. The profile audit requires a passing report no older than seven days.
- Governed MCP: a local FastMCP `3.4.4` stdio server now gives Hermes nine typed Tender OS tools for case/source/approval reads, advisory scoring, local document evidence, robots-compliant public capture, capability health, and policy probing. Hermes exposes only the explicit allowlist; MCP resources, prompts, parallel calls, server-initiated sampling, and elicitation are disabled. Because measured cold discovery takes roughly two to three seconds, `mcp_discovery_timeout` is 20 seconds and one-shot startup waits before the agent snapshots tools. The reliability receipt passes 3/3 cold and 10/10 warm canaries at `outputs/upgrade_baseline/mcp_discovery_reliability.json`.
- Infrastructure policy: Open Policy Agent `1.16.2` evaluates T0–T5 rules before every MCP call. It rejects model-supplied approval claims and verifies the local register, structured card, owner-decision receipt, exact case/action scope hash, expiry, unused execution state, and T5 controls. Decisions produce receipts and canonical `policy.decision_recorded` events.
- Runtime security: newly published Python dependency advisories were patched locally and `hermes security audit` reports no known vulnerabilities; see `docs/HERMES_RUNTIME_SECURITY_PATCH_20260712.md`.
- Checkpoint runtime patch: see `docs/HERMES_RUNTIME_CHECKPOINT_PATCH_20260712.md`; a future Hermes update may supersede it and should rerun the checkpoint canary.
- Safe regression: the earlier FAIL snapshot is historical. The canonical `outputs/regression/full_safe_regression_report.json` was regenerated with `.venv/bin/python` and passes all 16 checks.

The reproducible desired state is in `config/hermes_profile_capabilities.yaml`. Secrets and platform credentials are intentionally excluded.

## Capability routing

Use Hermes Kanban for work that must survive a restart, wait at an approval gate, cross a profile boundary, or retain a durable handoff. Use bounded delegation only for a result needed in the current turn. Use `execute_code` for compact multi-tool data loops and the terminal for builds, tests, parsers, and supervised repository jobs.

Approval waits use a typed `needs_input` block. During the 2026-07-12 buyer-pilot verification, Hermes 0.18.2 auto-promoted four cards created with an untyped initial block; one worker performed read-only local/public-source verification before it was reclaimed. The local Hermes DB layer now records `--initial-status blocked` as a sticky `needs_input` event, the focused upstream regression test passes, and a live canary remained blocked through a dispatcher pass. The audit receipt is `outputs/buyer_market_research/DR-BUYER-MARKET-20260712-HANDICRAFT-PILOT/kanban_receipt.json`.

Use no-agent cron when a deterministic script can do the work. It avoids model cost, treats process exit codes as truth, and creates repeatable receipts. Agent-backed cron should be added only when the job genuinely needs judgment that cannot be encoded and evaluated deterministically.

## Prediction and tracking

`forecast_score` remains a prioritization score. It is never presented as a probability.

Forecast rows now include:

- a named prediction target;
- a conservative expert-prior probability;
- `PRIOR_UNCALIBRATED` status;
- a model version;
- a maturity date;
- a frozen feature snapshot;
- historical backtest rows rather than overwritten snapshots;
- Brier components only for mature, scorable outcomes.

Calibration remains `INSUFFICIENT_MATURE_SAMPLE` until at least 30 mature outcomes exist. Research-only category demand is capped, a buyer repeat window requires at least two distinct cases, and a same-day pre-existing outcome cannot be counted as a forecast success.

## Buyer acquisition and replies

ChatGPT Deep Research handles broad foreign-market, retailer, importer, and assortment discovery. The read-only agent-browser lane captures exact GeM, CPPP, UNGM, retailer catalogue, product, company, and public-contact evidence. Repo staging turns verified observations into demand signals, buyer targets, personalized drafts, and approval cards without treating catalogue fit as an RFQ.

Gmail operations use the Gmail plugin only. Approved drafts become outbox handoffs only after a matching owner receipt and scope hash exist. Send receipts and replies are ingested into the outreach and communication ledgers; opt-outs, bounces, and not-interested responses stop automatically, while substantive replies become owner actions. No reply is sent automatically.

## Learning and memory

Hermes memory and agent-created skill writes require approval. Durable patterns need repeated observations. Raw tender/RFQ text, supplier-table dumps, credentials, cookies, DSC material, bank details, and unverified claims never become profile memory.

The weekly learning job may propose memory, skill, source, and rule changes. It may not silently activate them.

The recovered Ares/Hermes v0.14 runtime is preserved as a separate read-only archive. Its 52 sessions and 754 messages are searchable on demand through `scripts/search_recovered_ares_context.py`; they are not merged into the live session database. Tool outputs are excluded by default, and old `Tom`/`A. Soul` identity, fitness schedules, demo-wholesaler invoices, mock GST data, credentials, cookies, and tokens are not activated in this profile. See `config/recovered_context.yaml` and `docs/HERMES_RECOVERY_CONTEXT_AUDIT_20260712.md`.

## Capabilities intentionally left off

- Hermes gateway delivery remains local because no owner-approved Telegram/Slack/etc credential is configured. Gmail buyer communication remains a separate Gmail-plugin-only Codex bridge; Hermes never substitutes browser Gmail, IMAP, or `gws`.
- Paid search/extraction backends remain off because no supported key and cost envelope are configured. DDGS provides free search; agent-browser and evidence-aware source adapters provide public-page capture.
- A cross-provider inference fallback remains off until the owner chooses a second provider and cost envelope. Same-account failover from `gpt-5.6-terra` to `gpt-5.5` is active.
- Temporal, PostgreSQL/pgvector, Langfuse, Browsertrix, changedetection.io, Kingfisher, OpenSearch, AGE, Splink, and heavy Docling/PaddleOCR deployment remain off. Current ledgers are small, source/corrigenda monitoring and hashed evidence already exist, and the machine has limited free disk. Add one only after a measured workflow, query, retrieval, evidence, or OCR failure justifies its operating cost.

These are explicit capability boundaries, not hidden failures.

## Recovery and verification

Use Hermes profile snapshots before material profile changes. Do not replace the current runtime with the recovered `0.14.0` Ares/Hermes source fork. It contains valuable design context but is older than the installed runtime and is a separate vertical product.

Verification commands:

```bash
hermes -p tender-export-os config check
hermes -p tender-export-os gateway status
hermes -p tender-export-os cron status
hermes -p tender-export-os cron list
hermes -p tender-export-os kanban diagnostics
hermes -p tender-export-os mcp list
hermes -p tender-export-os mcp test tender_os
opa check policies/tender_os_authorization.rego
.venv/bin/python scripts/tender_os_policy.py --self-test
.venv/bin/python scripts/check_cron_gateway_reliability.py --json
.venv/bin/python scripts/audit_hermes_profile_capabilities.py --json
.venv/bin/python scripts/evaluate_hermes_behavioral_contracts.py --json
.venv/bin/python scripts/check_projection_integrity.py --fail-on-drift
.venv/bin/python scripts/public_web_evidence_scraper.py --url https://example.com --max-pages 1 --max-depth 0
.venv/bin/python scripts/run_v5_shadow_cycle.py
.venv/bin/python scripts/validate_register_schemas.py
.venv/bin/python scripts/check_mcp_discovery_reliability.py --cold-trials 3 --warm-trials 10 --output outputs/upgrade_baseline/mcp_discovery_reliability.json
.venv/bin/python scripts/run_full_safe_regression.py --output outputs/regression/full_safe_regression_report.json
```

## Primary Hermes references

- https://hermes-agent.nousresearch.com/docs/user-guide/profiles
- https://hermes-agent.nousresearch.com/docs/user-guide/features/cron
- https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban
- https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- https://hermes-agent.nousresearch.com/docs/user-guide/features/code-execution
- https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
- https://hermes-agent.nousresearch.com/docs/user-guide/features/fallback-providers
- https://hermes-agent.nousresearch.com/docs/user-guide/checkpoints-and-rollback
- https://hermes-agent.nousresearch.com/docs/user-guide/security
