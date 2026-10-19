# Paperclip Decision

## Decision
Do not integrate Paperclip in the default v4 setup.

## Reason
Hermes already provides the needed control-plane primitives for this system:
- Kanban durable task board
- scheduled cron jobs
- webhooks and gateway delivery
- skills
- memory
- session search and recall
- MCP
- Codex App-Server Runtime
- toolsets
- terminal backends
- code execution
- subagent/delegation primitives where enabled by the platform
- self-improvement loop

## Reconsider Paperclip Only If
- a separate external multi-company dashboard is needed
- non-Hermes agents must be managed in one external UI
- Hermes Kanban becomes insufficient
- stakeholder-facing org charts or budgets are required outside Hermes

## Current Default
Use Hermes Kanban as the company workboard.

## Sources
- User upgrade brief: `/Users/raghav/.codex/attachments/50962de5-cb39-48a4-8d6e-31bce3df71ac/pasted-text.txt`
- Local `hermes --help`, run on 2026-06-30, confirmed `kanban`, `cron`, `webhook`, `gateway`, `skills`, `memory`, `mcp`, `tools`, and `serve`.
