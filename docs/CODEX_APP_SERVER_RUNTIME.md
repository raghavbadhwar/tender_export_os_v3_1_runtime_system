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

## Sources
- Local `codex --help` output, run on 2026-06-30.
- Local `hermes --help` output, run on 2026-06-30.
- Hermes Agent documentation: https://hermes-agent.nousresearch.com/docs/
- Codex CLI local help output from `/opt/homebrew/bin/codex`.
