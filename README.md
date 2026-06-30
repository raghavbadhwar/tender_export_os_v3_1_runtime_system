# Tender Export OS v4.1
**Event-ledger hardened Hermes-Native Control Plane + Codex Plugin Runtime for Indian government tenders and export RFQs.**

---

## What This Is

A real company machine: Hermes runs the operating rhythm, Codex produces artifacts, ChatGPT handles deep research, and Google Drive stays the business source of truth.

v4.1 adds an append-only event ledger, schema validation, projection rebuilds, owner-decision receipts, readiness gates, artifact manifests, source-adapter fixtures, and Hermes Kanban reconciliation plans.

The max-capability upgrade adds live Hermes cron operating loops, per-case workspaces, evidence bundles, executable Kanban task graphs, structured approval-card JSON, founder quick commands, and an expanded event taxonomy. The agent-excellence upgrade tunes each agent to a best-in-class professional standard and maps Claude plugins/Accio skills into safe capability bundles. See `docs/MAX_CAPABILITY_UPGRADE_ROADMAP.md`, `docs/FOUNDER_QUICK_COMMANDS.md`, `docs/AGENT_EXCELLENCE_SYSTEM.md`, and `docs/ROLE_CAPABILITY_STANDARDS.md`.

Communication between ChatGPT and Codex/Hermes runs through Google Drive:

```text
Tender Export OS - Knowledge Bus/08_ChatGPT_Bridge/
```

Codex/Hermes writes bounded packets to `01_To_ChatGPT`; ChatGPT returns research to `02_From_ChatGPT`; Hermes/Codex stages and reviews returns before anything reaches the event ledger or registers.

It runs a structured pipeline across two workflows:

```
Find → Fast Kill → Deep Read → Supplier Proof → Pricing Proof → Approval → Execution → Receipt
```

**Automation handles:** scanning, extraction, scoring, sourcing, pricing, drafting, briefing.  
**Humans approve:** bids, quotes, EMD/security, DSC, HSN/origin claims, supplier commitment, delivery promises, payment terms.

---

## v4 Architecture

| Layer | Tool | Role |
|---|---|---|
| **Control Plane** | Hermes | Chief Operating Agent, owner rhythm, approvals, Kanban, memory, skills, routing |
| **Durable Workboard** | Hermes Kanban | Cases, tasks, blockers, approvals, handoffs, weekly learning |
| **Artifact Runtime** | Codex App-Server Runtime | File/script work, plugins, spreadsheets, PDFs, DOCX, PPTX, dashboards, packs |
| **Strategy Boardroom** | ChatGPT Project | Deep cited research, weekly review, category/export strategy |
| **Knowledge Bus** | Google Drive | Registers, artifacts, approvals, receipts, snapshots |

Paperclip is intentionally not used by default. Reconsider it only if Hermes Kanban is not enough.

---

## Workflow A — Government Tenders

1. Radar Agent scans GeM, CPPP, eProcure, state portals daily
2. Fast Kill Agent rejects non-starters (EMD, eligibility, deadline, experience)
3. Deep Read Agent extracts BOQ, eligibility, clauses, delivery, payment, penalties
4. Supplier Engine sources 5+ candidate suppliers across 3+ source types
5. Pricing Agent builds landed-cost bid price waterfall
6. Pack Builder prepares full bid pack + compliance matrix
7. Approval Desk creates approval card → owner approves
8. After approval: Execution Tracker monitors submission, follow-up, result

---

## Workflow B — Export RFQs

1. Radar Agent scans buyer portals, RFQ platforms, foreign-government sources
2. Fast Kill Agent rejects on buyer risk, payment risk, product restriction
3. Deep Read Agent extracts product spec, quantity, destination, deadline, Incoterms
4. Compliance Agent drafts HSN/ITC-HS candidate, export policy flags, certificates
5. Supplier Engine sources from India/global using 5-3-2 rule
6. Pricing Agent builds EXW/FOB/CIF waterfall
7. Pack Builder prepares export quote pack
8. Approval Desk creates approval card → owner approves before any reply

---

## How to Run the System Daily

### Morning (5–10 minutes)
1. Open Hermes through the configured gateway (Telegram/WhatsApp/CLI/local file).
2. Review the daily brief. If gateway delivery is not configured, read `outputs/daily_briefs/brief_YYYYMMDD.html`.
3. Review pending approval cards in `receipts/approvals/`.
4. Approve, reject, or request changes through Hermes using commands such as `approve case GOV-20260630-001`.

### First Commands / Actions

1. Inspect Hermes:
```bash
hermes doctor
hermes --help
hermes tools --help
hermes skills --help
hermes mcp --help
```

2. Inspect Codex:
```bash
codex --version
codex --help
codex plugin list --available --json
codex app-server --help
```

3. Run local readiness check:
```bash
python3 scripts/check_codex_runtime_readiness.py
```

4. Run full safe system health check:
```bash
python3 scripts/system_health_check.py --runtime
```

5. Validate v4.1 state contracts:
```bash
python3 scripts/validate_register_schemas.py
python3 scripts/rebuild_projections_from_events.py
python3 scripts/validate_case_readiness.py --all
python3 scripts/prepare_chatgpt_drive_packet.py
```

6. Configure safety:
- `config/memory_policy.yaml`: `memory.write_approval = true`
- `config/memory_policy.yaml`: `skills.write_approval = true`
- `config/memory_policy.yaml`: `display.memory_notifications = verbose`
- `config/approval_policy.yaml`: external/money/legal/DSC/classification/origin gates stay strict

7. Enable Codex runtime inside Hermes if supported:
```text
/codex-runtime codex_app_server
```

Fallback:
```text
/codex-runtime auto
```

8. Create Hermes Kanban board after checking local syntax:
```bash
hermes kanban --help
bash scripts/setup_hermes_kanban_board.sh
```

9. Create Hermes cron jobs from `config/hermes_cron.yaml` after checking:
```bash
hermes cron --help
```

10. Create the Google Drive Knowledge Bus using `docs/GOOGLE_DRIVE_KNOWLEDGE_BUS.md`, then dry-run sync:
```bash
python3 scripts/sync_to_drive.py
```

11. Run dry-run artifacts/snapshots:
```bash
python3 scripts/generate_chatgpt_snapshot.py
python3 scripts/supplier_score.py
python3 scripts/case_id_generator.py --type GOV
python3 scripts/case_id_generator.py --type EXP
```

12. Review:
- Hermes Kanban board
- daily brief
- case report
- artifact pack

13. Create/refresh max-capability case operating assets:
```bash
python3 scripts/create_case_workspace.py --all-active --record-event
python3 scripts/capture_case_evidence.py --case-id GOV-20260630-001 --record-event
python3 scripts/create_case_task_graph.py --case-id GOV-20260630-001 --execute --record-event
python3 scripts/generate_approval_cards.py --json --overwrite --record-event
```

Use `--execute` on `create_case_task_graph.py` only for internal Kanban task creation. It does not send, submit, upload, pay, use DSC, or commit commercial/compliance claims.
- approval queue
- receipts

### Manual CLI Operations
If you want to trigger parts of the system manually:
```bash
python3 scripts/system_health_check.py --runtime
python3 scripts/validate_register_schemas.py
python3 scripts/rebuild_projections_from_events.py
python3 scripts/process_owner_decision.py --approval-id APR-001 --decision ask-changes --owner OWNER --changes "what to change" --dry-run
python3 scripts/validate_case_readiness.py --all
python3 scripts/generate_artifact_manifest.py --all
python3 scripts/run_source_adapter.py --adapter mock
python3 scripts/reconcile_hermes_kanban.py
python3 scripts/prepare_chatgpt_drive_packet.py
python3 scripts/stage_chatgpt_return.py --input tests/fixtures/chatgpt_returns/sample_return.md
python3 scripts/run_daily_autopilot_pseudocode.py
python3 scripts/generate_daily_brief.py
python3 scripts/score_opportunity.py --case_id GOV-20260630-001
python3 scripts/generate_chatgpt_snapshot.py
```

### Weekly (30 minutes)
- ChatGPT Project: weekly review of wins/losses, source health, supplier performance
- Update `config/categories.yaml` for new product focus areas
- Archive closed cases

---

## Folder Structure

```
tender-export-os/
├── README.md                    ← You are here
├── AGENTS.md                    ← Agent roster and responsibilities
├── HERMES.md                    ← Hermes chief operator instructions
├── SOUL.md                      ← v4 operating identity and non-negotiables
├── docs/                        ← v4 architecture and policy docs
├── manifest.json                ← System metadata
├── config/                      ← All configurable rules and sources
│   ├── sources.gov.yaml
│   ├── sources.export.yaml
│   ├── sources.supplier.yaml
│   ├── categories.yaml
│   ├── kill_rules.yaml
│   ├── scoring_weights.yaml
│   ├── approval_policy.yaml
│   ├── codex_runtime_policy.yaml
│   ├── hermes_cron.yaml
│   ├── kanban_board.yaml
│   ├── memory_policy.yaml
│   ├── plugin_routing.yaml
│   ├── agent_capability_routing.yaml
│   ├── source_strategy.yaml
│   ├── sync_policy.yaml
│   ├── schemas/
│   ├── agent_loops.json
│   └── loop_schedule.json
├── data/                        ← Master registers (Excel/CSV)
│   ├── events.jsonl             ← v4.1 append-only canonical event ledger
│   ├── master_cases.csv
│   ├── supplier_master.csv
│   ├── source_health.csv
│   ├── approvals_receipts.csv
│   ├── quote_master.csv
│   ├── plugin_health.csv
│   ├── capability_registry.csv
│   ├── chatgpt_snapshot.md
│   └── agent_run_log.csv
├── agents/                      ← Agent instruction files
├── skills/                      ← v4 reusable Hermes/Codex workflow skills
├── chatgpt_project/             ← Boardroom instructions and research prompts
├── workflows/                   ← Runtime flow documents and agent loop handoff
├── templates/                   ← Email, approval card, brief templates
├── hermes/                      ← Hermes mobile command center config
├── codex/                       ← Codex backend operator config
├── outputs/                     ← Generated outputs (briefs, packs, reports)
│   ├── daily_briefs/
│   ├── case_reports/
│   ├── bid_packs/
│   ├── export_quote_packs/
│   └── dashboards/
├── receipts/                    ← Immutable action receipts
│   ├── approvals/
│   ├── submissions/
│   ├── supplier_quotes/
│   └── owner_decisions/
├── scripts/                     ← Python utilities and loop validators
└── tests/fixtures/sources/       ← Safe source-adapter fixtures
```

---

## Non-Negotiable Safety Rules

- ❌ Never submit bids automatically
- ❌ Never send final quotes without owner approval
- ❌ Never confirm HSN/ITC-HS classification without export expert review
- ❌ Never claim origin, eligibility, or certificates not verified
- ❌ Never use DSC without explicit owner action
- ❌ Never commit payment terms or delivery without approval
- ❌ Never pay EMD, security deposit, or advance without approval
- ✅ All approvals must be logged with case_id, timestamp, and receipt
- ✅ Codex App-Server Runtime is preferred for plugin-heavy artifact/file work
- ✅ Hermes Kanban is the default durable workboard
- ✅ ChatGPT receives bounded snapshots, not raw operational databases
- ✅ `data/events.jsonl` is the canonical v4.1 event stream; CSVs and Kanban are projections
- ✅ Owner decisions create receipts but never send, submit, upload, pay, or commit externally by themselves

## Agent Loop Runtime

The bounded loop contracts live in `config/agent_loops.json`.
The scheduled operating cadence lives in `config/loop_schedule.json`.

Before changing loop behavior or running a new automation pattern:

```bash
python scripts/validate_agent_loops.py
python scripts/validate_loop_schedule.py
```

Human-readable handoff: `workflows/agent_loop_runtime.md`
Schedule handoff: `workflows/agent_loop_schedule.md`

Every loop must keep:
- explicit stop conditions
- max iteration and timeout limits
- approval gates for external or financial actions
- append-only run logging
- source citations in generated reports
- no fabricated supplier, pricing, eligibility, classification, or origin claims

The default schedule is:
- Morning Operator Brief at 08:30 IST
- Midday Opportunity Radar at 13:00 IST
- Supplier Follow-up Review at 17:00 IST
- Evening Execution Close at 20:30 IST
- Weekly Learning Review on Friday at 18:00 IST
- Monthly Strategy Deep Research only when owner-approved

---

## First-Time Setup Checklist

- [ ] Run `python3 scripts/check_codex_runtime_readiness.py`
- [ ] Run `python3 scripts/system_health_check.py --runtime`
- [ ] Run `python3 scripts/validate_register_schemas.py`
- [ ] Run `python3 scripts/rebuild_projections_from_events.py` and review `outputs/projections/`
- [ ] Run `python3 scripts/generate_artifact_manifest.py --all`
- [ ] Inspect `hermes kanban --help` and configure the `tender-export-os` board from `config/kanban_board.yaml`
- [ ] Inspect `hermes cron --help` and configure jobs from `config/hermes_cron.yaml`
- [ ] Configure `config/memory_policy.yaml` with write approvals enabled
- [ ] Confirm Google Drive connector/auth before any non-dry-run sync
- [ ] Copy `config/sources.gov.yaml` and add your preferred portals with login flags
- [ ] Copy `config/categories.yaml` and mark your active product/service categories
- [ ] Fill `data/supplier_master.csv` with any existing supplier contacts
- [ ] Set your IEC, GSTIN, company name in `codex/codex_project_prompt.md`
- [ ] Configure Hermes profile from `hermes/hermes_profile.md`
- [ ] Read `hermes/mobile_commands.md` for all available Hermes commands
- [ ] Trigger first Codex artifact/runtime dry run using `codex/codex_runtime_instructions.md`

---

## Key v4 Files

- `docs/ARCHITECTURE_CRITIQUE_AND_V4_1_PROPOSAL.md`
- `docs/FINAL_ARCHITECTURE.md`
- `docs/HERMES_NATIVE_CONTROL_PLANE.md`
- `docs/CODEX_APP_SERVER_RUNTIME.md`
- `docs/HERMES_KANBAN_BOARD.md`
- `docs/CODEX_PLUGIN_RUNTIME_POLICY.md`
- `docs/GOOGLE_DRIVE_KNOWLEDGE_BUS.md`
- `docs/CHATGPT_BOARDROOM.md`
- `docs/PAPERCLIP_DECISION.md`
- `docs/APPROVAL_BOUNDARIES.md`
- `docs/WEB_BROWSER_RESEARCH_ROUTING.md`
- `docs/CHATGPT_CODEX_HERMES_DRIVE_COMMUNICATION.md`
- `data/events.jsonl`
- `config/schemas/`
- `scripts/validate_register_schemas.py`
- `scripts/process_owner_decision.py`
- `scripts/validate_case_readiness.py`
- `scripts/generate_artifact_manifest.py`
- `scripts/reconcile_hermes_kanban.py`
- `scripts/prepare_chatgpt_drive_packet.py`
- `scripts/stage_chatgpt_return.py`

*System version: v4.1 | Hermes-native | Event-ledger hardened | Built for one-founder operation | Safe for semi-autonomous daily use*
