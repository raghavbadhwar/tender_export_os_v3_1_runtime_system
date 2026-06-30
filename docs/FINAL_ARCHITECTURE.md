# Tender Export OS v4.1 - Final Architecture

## Version
Tender Export OS v4.1 - Event-Ledger Hardened Hermes-Native Control Plane + Codex Plugin Runtime

## Core Principle
Do not build unnecessary external orchestration unless Hermes cannot do it.

Hermes is the resident operating brain and control plane. Codex is the plugin-powered artifact factory inside the Hermes operating rhythm. ChatGPT Project is the deep research and strategy boardroom. Google Drive is the shared source of truth. Paperclip is not part of the default v4 setup.

v4.1 adds an append-only local event ledger as the canonical state record. CSV registers, Hermes Kanban cards, Google Drive manifests, daily briefs, approval cards, and artifact manifests are projections from or citations back to this ledger.

## Control Plane
| Layer | System | Role |
|---|---|---|
| Operating brain | Hermes | Daily rhythm, approvals, memory, Kanban, routing, source health, plugin health, owner briefings |
| Durable workboard | Hermes Kanban | Cases, tasks, blockers, approvals, handoffs, weekly learning |
| Artifact/runtime factory | Codex App-Server Runtime | File edits, parsing, spreadsheets, PDFs, DOCX, PPTX, dashboards, plugin production |
| Deep research boardroom | ChatGPT Project | Cited public research, strategy, category analysis, weekly reviews |
| Knowledge bus | Google Drive | Shared registers, packs, approvals, receipts, snapshots, artifacts |
| Founder learning layer | Obsidian/local notes | Qualitative playbook, lessons, founder thinking |

## Canonical State Model
`data/events.jsonl` is the append-only canonical state stream.

CSV registers remain operational projections:
- `data/master_cases.csv`
- `data/approvals_receipts.csv`
- `data/supplier_master.csv`
- `data/quote_master.csv`
- `data/source_health.csv`
- `data/plugin_health.csv`

Use these scripts to maintain the state model:
- `scripts/initialize_event_ledger.py` seeds the ledger from reviewed registers.
- `scripts/rebuild_projections_from_events.py` rebuilds CSV projections from the ledger.
- `scripts/validate_register_schemas.py` validates CSV schemas and event shape.
- `scripts/validate_case_readiness.py` checks quote, approval, and compliance gates.
- `scripts/process_owner_decision.py` records owner decisions and receipts without external execution.
- `scripts/generate_artifact_manifest.py` maps all artifacts and receipts per case.
- `scripts/reconcile_hermes_kanban.py` creates a plan-only Hermes Kanban reconciliation.

## Runtime Split
Hermes directly handles:
- owner briefings and approval cards
- quick case explanations and status checks
- memory and skill update proposals
- Kanban task routing and comments
- follow-up reminders
- source-health and plugin-health summaries
- lightweight supplier or buyer drafts that remain internal

Codex handles:
- tender PDF, BOQ, spreadsheet, and attachment parsing
- structured file edits and scripts
- dashboards, workbooks, PDFs, DOCX, PPTX, invoices, scorecards, bid packs, and export quote packs
- plugin inventory checks and plugin-heavy artifact production
- source adapter repair and testable parser work

ChatGPT handles:
- market and category research
- export destination research
- strategic weekly review
- dashboard interpretation
- source landscape review
- business-model-level opportunity ranking

Google Drive stores:
- synced control-center registers
- daily briefs
- case reports
- bid packs and export quote packs
- supplier proof
- approval and execution receipts
- config snapshots
- ChatGPT snapshots and returned research

## Status Flow
`NEW -> FAST_KILL -> REJECTED`

`NEW -> FAST_KILL -> WATCHLIST -> DEEP_READ -> SUPPLIER_SEARCH -> PRICING_READY -> ARTIFACT_PRODUCTION -> APPROVAL_REQUIRED -> APPROVED -> SENT_OR_SUBMITTED -> FOLLOW_UP -> WON / LOST -> ARCHIVED`

`APPROVAL_REQUIRED -> CHANGES_REQUESTED` loops back to the relevant production or analysis step.

## Approval Boundary
No system may execute an external, financial, legal, DSC, final classification, origin, final price, supplier commitment, or delivery commitment action without explicit owner approval and a receipt.

## Default Paperclip Decision
Paperclip is optional later and excluded by default. Hermes already supplies the required primitives for this one-founder operating system: Kanban, cron, gateway delivery, skills, memory, MCP, toolsets, terminal backends, Codex App-Server Runtime, code execution, and session recall.

## Sources
- User upgrade brief: `/Users/raghav/.codex/attachments/50962de5-cb39-48a4-8d6e-31bce3df71ac/pasted-text.txt`
- Local `hermes --help` output, run on 2026-06-30, confirmed `cron`, `kanban`, `skills`, `memory`, `tools`, `mcp`, `sessions`, `gateway`, and `serve`.
- Local `codex --help` output, run on 2026-06-30, confirmed `app-server`, `plugin`, `doctor`, `mcp`, and `exec`.
- NousResearch Hermes Agent repository: https://github.com/NousResearch/hermes-agent
- Hermes Agent documentation: https://hermes-agent.nousresearch.com/docs/
