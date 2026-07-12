# Hermes Last-Pass Improvement Audit — 2026-07-12

## Outcome

The remaining high-value, credential-free improvements have been implemented. The active Tender profile now adds rollback checkpoints, same-account model failover, deterministic Gmail/terminal bypass protection, and repeated behavioral contract evaluation on top of its existing memory, browser, scraping, Computer Use, Kanban, cron, prediction, and tracking capabilities.

The architecture remains one local Hermes control plane backed by the append-only event ledger. No external memory provider, broad MCP collection, or always-on research VM was justified.

Subsequent same-day update: the user supplied a project shortlist and asked to add only items with a clear net improvement. One local, allowlisted FastMCP server plus an Open Policy Agent gate was therefore implemented. This supersedes the earlier "no Tender-specific MCP" conclusion without changing the rejection of broad MCP/tool sprawl; see `docs/HERMES_GOVERNED_MCP_OPA_INTEGRATION_20260712.md`.

## Implemented in this pass

1. **Same-account model resilience**
   - Primary: `gpt-5.6-terra` through OpenAI Codex OAuth.
   - Fallback: verified `gpt-5.5` through the same OAuth account.
   - Triggered only for supported availability failures such as rate limits, overload, service errors, or connection failures.

2. **Filesystem checkpoints and rollback**
   - Enabled for future Hermes writes and destructive terminal operations.
   - Bounded to 12 snapshots per project, 300 MB total, 10 MB per file, and seven-day retention with auto-prune.
   - Hermes' file-count guard incorrectly counted directories as files and skipped this workspace. The local fix now counts actual files.
   - Live activation canary: one checkpoint created in 3.5 seconds; 1,190,525-byte store; one project and one restorable commit.

3. **Deterministic business-channel guardrails**
   - Hermes web/browser access to `mail.google.com` and `gmail.com` is blocked.
   - `gws`, Himalaya, and force-push terminal commands are denied even if a session enables YOLO.
   - Google Drive, GeM, CPPP, UNGM, and public research sources remain allowed.
   - Gmail continues through the approved Gmail-plugin packet and receipt contract only.

4. **Repeated behavioral evaluation**
   - Nine critical scenarios cover unapproved outreach, scraped prompt injection, catalogue-fit overclaiming, legacy-memory conflict, final HSN claims, missing quote proof, CAPTCHA bypass, substantive buyer replies, and the rule that a read-only OPA allow result is not execution.
   - Each scenario runs three times using only the `clarify` toolset.
   - Final verified result: 27/27 cases passed, with zero external actions.
   - The capability audit now blocks if the latest report is missing, failed, or older than seven days.

## Options reviewed but not enabled

| Capability | Decision now | Trigger for reconsideration |
|---|---|---|
| Self-hosted SearXNG | Keep dormant. Its Colima profile currently reserves about 10 GB and DDGS plus Deep Research already cover discovery. | DDGS reliability or rate limits materially affect real runs. |
| Firecrawl, Tavily, Exa, Parallel, or Nous Tool Gateway extraction | Defer. The robots-aware static scraper and agent-browser preserve raw evidence without a new credential or spend. | Large-scale extraction volume, anti-JS failure rate, or measured operator time justifies a provider and budget. |
| Browserbase/Browser Use cloud browser | Defer. Local Chromium and Computer Use are proven. | A measured need for cloud sessions, residential proxies, or remote observation outweighs privacy and cost. |
| Authenticated Chrome/CDP portal lane | Manual, case-specific only. Never a default background capability. | A login-required document cannot be obtained through public or owner-uploaded evidence, and the owner approves a bounded session. |
| Cross-provider model fallback | Defer. Same-account `gpt-5.5` failover is active. | OpenAI-provider outages become a measured business-continuity risk and the owner approves another provider/cost envelope. |
| Additional MCP servers | One local Tender OS FastMCP server is active with nine allowlisted tools and OPA enforcement. No general or third-party MCP collection. | Add another server only when a named system exposes a narrow, auditable integration that existing repo adapters cannot handle reliably. |
| External memory provider | Keep off. | Local memory quality is demonstrably insufficient and a privacy-reviewed provider offers measurable retrieval gains. |
| Telegram/Slack/Discord owner delivery | Keep local. | The owner chooses a channel and supplies an approved credential and allowlist. |
| Langfuse or remote agent tracing | Keep off. Local receipts, events, and evaluations are sufficient today. | Debugging or reliability analysis needs cross-run traces and a privacy/cost review is approved. |

## Operating conclusion

The next meaningful gains are data gains, not tool-count gains: more mature forecast outcomes, verified supplier quote history, buyer replies, wins/losses, and source reliability history. Those observations will improve prediction calibration and targeting more than another general-purpose plugin.

Re-run the behavioral evaluator after any change to `SOUL.md`, approval policy, the six governed skills, model routing, browser authority, memory rules, or Gmail routing.

## Official references

- https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search
- https://hermes-agent.nousresearch.com/docs/user-guide/features/fallback-providers
- https://hermes-agent.nousresearch.com/docs/user-guide/checkpoints-and-rollback
- https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-search
- https://hermes-agent.nousresearch.com/docs/user-guide/security
