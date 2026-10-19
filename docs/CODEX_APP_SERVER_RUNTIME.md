# Codex App-Server Runtime Policy

## Decision
Use Hermes's built-in Codex App-Server Runtime first. Do not build a custom Hermes-to-Codex bridge unless the app-server runtime is unavailable or repeatedly fails for the needed task.

## Confirmed Local Baseline
Local checks on 2026-06-30 found:
- `hermes` at `/Users/raghav/.local/bin/hermes`
- `ares-hermes` at `/Users/raghav/.ares/bin/ares-hermes`
- `codex` at `/opt/homebrew/bin/codex`
- `codex --version`: `codex-cli 0.141.0`
- `codex --help` includes `app-server`, `plugin`, `doctor`, `mcp`, `exec`, and `apply`
- `hermes --help` includes `cron`, `kanban`, `skills`, `plugins`, `memory`, `tools`, `mcp`, `sessions`, `gateway`, and `serve`

## Readiness Command
Run:

```bash
python3 scripts/check_codex_runtime_readiness.py
```

The script inspects local command availability and help output before marking capabilities as ready. It does not assume exact syntax.

## Preferred Runtime Activation
Inside Hermes, try:

```text
/codex-runtime codex_app_server
```

If unsupported, inspect local Hermes help and fall back to the local command indicated there. If Hermes supports auto runtime selection, use:

```text
/codex-runtime auto
```

## Runtime Behavior
Hermes remains the shell:
- sessions
- slash commands
- gateway/mobile interaction
- memory
- skills
- Kanban
- review loop

Codex handles:
- shell and file operations
- structured patching
- native Codex plugins
- sandbox-aware execution
- web/file parsing work
- app-server backed artifact production

## Expected Tool Callback
When supported, Hermes should expose the following back into Codex through MCP or runtime callbacks:
- web search and extraction
- browser tools
- vision and image generation
- skills list and skill view
- text to speech
- Kanban tools

## Important Limitation
Some Hermes agent-context tools may not be available inside a Codex turn. Keep memory-heavy, session-search-heavy, delegation-heavy, and Kanban-orchestration work in default Hermes runtime unless local testing proves otherwise.

## Fallback Bridge
Create or use the fallback bridge only if app-server runtime is unavailable or consistently fails:

- `runtime/codex_inbox/`
- `runtime/codex_outbox/`
- `scripts/hermes_create_codex_task.py`
- `scripts/codex_task_runner.py`

This bridge is a fallback, not the primary architecture.

## Governed GOV Bid-Pack Receipt

For a government-tender bid pack, Hermes creates a bounded internal Codex packet with:

- `python3 scripts/hermes_create_codex_task.py --case-id <CASE_ID> --bid-pack --input-artifact <path>`

Codex may only create internal draft artifacts. It must not submit, upload, use DSC, contact a party, pay, or make a final commercial or compliance commitment. Before an Approval Desk card is generated, run:

```bash
python3 scripts/codex_task_runner.py --verify-bid-pack --case-id <CASE_ID> --write-receipt --json
```

The verifier requires a complete bid-pack manifest, all mandatory artifacts, a separate missing-items list, a successful internal plugin receipt, and open/render/parse checks. It writes `outputs/bid_packs/<CASE_ID>/verification_receipt.json` and a canonical audit event. Approval-card generation independently rechecks that the receipt matches the current manifest, so a stale receipt cannot unlock an approval card.

## Governed EXPORT Quote-Pack Receipt

For a buyer-specific, verified export RFQ, Hermes creates a bounded internal quote-pack task with:

```bash
python3 scripts/hermes_create_codex_task.py --case-id <CASE_ID> --export-quote-pack --input-artifact <path>
```

The task may create only draft artifacts: a draft proforma invoice, product specification, supplier summary, pricing waterfall, compliance caveats, Incoterm/payment proposal, validity/delivery assumptions, and missing-items list. It may not send a quotation, contact a buyer, accept an order, ship, invoice, pay, or finalize price, classification, origin, or delivery claims. Verify the finished pack before creating a buyer-facing quotation approval card:

```bash
python3 scripts/codex_task_runner.py --verify-export-quote-pack --case-id <CASE_ID> --write-receipt --json
```

The verifier requires a `DRAFT_READY` commercial-readiness report backed by two strict supplier-specific quote proofs, full EXW/FOB/CIF inputs, draft-only classification/origin treatment, and a successful internal plugin receipt. A change to any artifact or readiness input makes the persisted verification receipt stale and blocks the card.

## Sources
- Local `codex --help` output, run on 2026-06-30.
- Local `hermes --help` output, run on 2026-06-30.
- Hermes Agent documentation: https://hermes-agent.nousresearch.com/docs/
- Codex CLI local help output from `/opt/homebrew/bin/codex`.
