# Tender Export OS v4.1 - Complete Architecture Reference

**Version:** 4.1.2  
**Status:** Production-Ready Operating System  
**Branch:** feat/teos-production-readiness-governance

---

## Executive Summary

Tender Export OS v4.1 is a **Hermes-native operating system** for Indian government tenders and export RFQs. It combines an event-ledger control plane, a plugin-powered artifact factory (Codex), a deep research boardroom (ChatGPT), and a shared knowledge bus (Google Drive) into a single governed operating rhythm.

> **Core Principle:** *Do not build unnecessary external orchestration unless Hermes cannot do it.*

---

## System Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TENDER EXPORT OS v4.1                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   CONTROL PLANE │  │  ARTIFACT FACTORY│  │  STRATEGY ROOM  │              │
│  │   (Hermes)      │  │   (Codex)       │  │  (ChatGPT)      │              │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤              │
│  │ • Daily rhythm  │  │ • File/script   │  │ • Deep research │              │
│  │ • Kanban board  │  │ • Plugins       │  │ • Market intel  │              │
│  │ • Approvals     │  │ • PDF/DOCX/PPTX │  │ • Weekly review │              │
│  │ • Memory/skills │  │ • Spreadsheets  │  │ • Citations     │              │
│  │ • Routing       │  │ • Dashboards    │  │ • Strategy      │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                ▼                                            │
│                    ┌─────────────────────┐                                  │
│                    │  KNOWLEDGE BUS      │                                  │
│                    │  (Google Drive)     │                                  │
│                    ├─────────────────────┤                                  │
│                    │ • Registers         │                                  │
│                    │ • Artifacts         │                                  │
│                    │ • Approvals/Receipts│                                  │
│                    │ • Snapshots         │                                  │
│                    └─────────────────────┘                                  │
│                                │                                            │
│                    ┌───────────▼───────────┐                                │
│                    │  CANONICAL STATE      │                                │
│                    │  (data/events.jsonl)  │                                │
│                    ├───────────────────────┤                                │
│                    │ Append-only event log │                                │
│                    │ All projections       │                                │
│                    │ rebuild from here     │                                │
│                    └───────────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Five-Layer Architecture

| Layer | System | Role | Key Contracts |
|-------|--------|------|---------------|
| **1. Control Plane** | Hermes | Chief Operating Agent — rhythm, approvals, Kanban, memory, routing | `HERMES.md`, `config/kanban_board.yaml`, `config/hermes_cron.yaml` |
| **2. Durable Workboard** | Hermes Kanban | Cases, tasks, blockers, approvals, handoffs, weekly learning | `config/kanban_board.yaml` |
| **3. Artifact Runtime** | Codex App-Server | File edits, parsing, spreadsheets, PDFs, DOCX, PPTX, dashboards, plugin production | `docs/CODEX_APP_SERVER_RUNTIME.md`, `config/codex_runtime_policy.yaml` |
| **4. Strategy Boardroom** | ChatGPT Project | Deep cited research, weekly review, category/export strategy | `docs/CHATGPT_BOARDROOM.md` |
| **5. Knowledge Bus** | Google Drive | Shared registers, packs, approvals, receipts, snapshots, artifacts | `docs/GOOGLE_DRIVE_KNOWLEDGE_BUS.md` |

---

## Canonical State Model

```
data/events.jsonl  ←  APPEND-ONLY CANONICAL STATE STREAM
        │
        ├──► data/master_cases.csv          (Case register projection)
        ├──► data/approvals_receipts.csv    (Approval register projection)
        ├──► data/supplier_master.csv       (Supplier register projection)
        ├──► data/quote_master.csv          (Quote register projection)
        ├──► data/source_health.csv         (Source health projection)
        ├──► data/plugin_health.csv         (Plugin health projection)
        ├──► data/buyer_demand_signals.csv  (Buyer demand projection)
        ├──► data/outreach_queue.csv        (Outreach queue projection)
        ├──► data/communication_log.csv     (Communication log projection)
        ├──► Hermes Kanban cards            (Working view)
        ├──► Daily briefs                   (Working view)
        ├──► Approval cards                 (Working view)
        └──► Artifact manifests             (Working view)
```

**Key Scripts:**
- `scripts/initialize_event_ledger.py` — Seeds ledger from reviewed registers
- `scripts/rebuild_projections_from_events.py` — Rebuilds CSVs from ledger
- `scripts/validate_register_schemas.py` — Validates schemas and event shapes
- `scripts/validate_case_readiness.py` — Checks quote, approval, compliance gates
- `scripts/process_owner_decision.py` — Records decisions and receipts
- `scripts/generate_artifact_manifest.py` — Maps artifacts and receipts per case
- `scripts/reconcile_hermes_kanban.py` — Creates reconciliation plan

---

## Hybrid Research + Operational Capture Model

This is the **routing contract** that prevents scope creep between discovery and proof.

### Decision Rule

| If the task needs... | Route to... |
|---------------------|-------------|
| Broad judgment across unknown sources, markets, categories | **ChatGPT Scheduled Deep Research** |
| Exact repetition on known sources, portal listing capture | **Python/Playwright + Codex** |
| Login/session/download/BOQ parsing | **Python/Playwright with approval boundaries** |
| Market/category/source discovery | **ChatGPT Deep Research** |
| Memory, dedupe, approvals, tests, schema validation | **Repo/Python (local)** |

### Workflow Examples

**Workflow A: New Category Discovery**
```
1. Deep Research → finds low-competition categories
2. Owner selects categories
3. Repo adds source/keyword watch
4. Python scans known sources repeatedly
```

**Workflow B: Specific Tender Proof**
```
1. Deep Research flags possible retender
2. Lead staged via `stage_deep_research_leads.py`
3. Python/Playwright checks known source
4. Documents/evidence captured
5. Case enters Fast Kill/Deep Read only if evidence supports
```

**Workflow C: Export Opportunity**
```
1. Deep Research identifies buyer/product market
2. Lead staged
3. Repo validates buyer evidence, supplier readiness, compliance, quote-proof
3. Owner approves any external buyer/supplier action
```

### Evidence Levels (Critical Distinction)

| Level | Meaning | Actionable? |
|-------|---------|-------------|
| `PUBLIC_LISTING_ONLY` | Lead from listing/teaser only | ❌ Lead only, not bid-ready |
| `DETAIL_PAGE_READ` | Detail page read, no documents | ❌ Needs documents |
| `DOCUMENTS_DISCOVERED` | Document links found | ⚠️ Operational capture can attempt |
| `DOCUMENTS_DOWNLOADED` | Documents downloaded/parsed | ✅ Can support case candidate |
| `DEEP_READ_COMPLETE` | Full extraction with evidence | ✅ Bid-ready candidate |
| `BLOCKED_*` | Login/CAPTCHA/paywall/manual | 🛑 Requires owner decision |

> **Never:** Treat `PUBLIC_LISTING_ONLY` as bid-ready. Never let Deep Research bypass Fast Kill, supplier proof, or approval gates.

---

## Agent Roster (11 Agents)

### Agent 0 — Hermes Chief Operator (Control Plane)
- **File:** `agents/hermes_chief_operator.md`
- **Purpose:** Daily rhythm, Kanban, approvals, routing, briefings, memory/skills, source/plugin health
- **Runs:** Always-on via cron, owner commands, Kanban events
- **Capabilities:** `operations`, `productivity`, `enterprise-search`, `data` + `tender-export-ops` skill bundle
- **Quality Gates:** One owner action, blockers surfaced, approval gates intact, Kanban current

### Agent 1 — Radar Agent (Discovery)
- **File:** `agents/radar_agent.md`
- **Purpose:** Find tenders/RFQs, assign case IDs, create starter records
- **Runs:** Daily 05:30 IST (cron: `core_source_agent_browser_radar`)
- **Inputs:** `config/sources.gov.yaml`, `config/sources.export.yaml`, `data/source_health.csv`
- **Outputs:** New `master_cases.csv` rows (status=`NEW`), updated `source_health.csv`
- **Capability Bundle:** `company-research`, `market-insight-product-selection`, `browser/playwright`, `data`
- **Quality Gates:** Dedupe by URL/title+buyer+deadline, source health updated, no CAPTCHA bypass

### Agent 2 — Fast Kill Agent (Triage)
- **File:** `agents/fast_kill_agent.md`
- **Purpose:** Quick rejection of non-viable opportunities using kill rules
- **Runs:** After each Radar scan (06:00 IST cron: `morning_opportunity_intelligence_html`)
- **Inputs:** `config/kill_rules.yaml`, `config/scoring_weights.yaml`, `config/categories.yaml`
- **Outputs:** Status → `REJECTED`/`WATCHLIST`/`DEEP_READ`, `no_go_reason_note.txt`, scores
- **Capability Bundle:** `market-viability-logic-auditor`, `operations`, `data`
- **Quality Gates:** Hard reject only with evidence; missing data = `WATCHLIST`; no-go note includes rule + evidence + reconsider condition

### Agent 3 — Deep Read Agent (Extraction)
- **File:** `agents/deep_read_agent.md`
- **Purpose:** Full document extraction from PDFs, BOQs, corrigenda, RFQs
- **Runs:** On cases promoted from Fast Kill (status=`DEEP_READ`)
- **Inputs:** Downloaded documents, `data/master_cases.csv`, `config/scoring_weights.yaml`
- **Outputs:** `deep_read_<case_id>.json/.md`, eligibility assessment, BOQ, risk flags, compliance checklist
- **Capability Bundle:** `pdf`, `docx`, `xlsx` + `pdf-viewer`, `pdf-server-mcp`, `ms_office_word`
- **Quality Gates:** All docs/corrigenda listed, risky clauses quoted verbatim, no eligibility claim without proof

### Agent 4 — Supplier Engine (Sourcing)
- **File:** `agents/supplier_engine_agent.md`
- **Purpose:** Source 5+ candidates across 3+ source types with 2+ quote proofs (5-3-2 rule)
- **Runs:** After Deep Read (status=`SUPPLIER_SEARCH`)
- **Inputs:** `config/sources.supplier.yaml`, `data/supplier_master.csv`, Deep Read report
- **Outputs:** `supplier_master.csv`, `quote_master.csv`, `supplier_shortlist_<case_id>.md`
- **Capability Bundle:** `product-supplier-sourcing`, `supplier-performance-manager`, `1688-sourcing`, `company-research`
- **Quality Gates:** 5 candidates minimum, 3 source types, 2 quote proofs, blacklist/certificate checks

### Agent 5 — Pricing Agent (Cost Waterfall)
- **File:** `agents/pricing_agent.md`
- **Purpose:** Complete landed-cost waterfall for GOV bids and EXW/FOB/CIF export quotes
- **Runs:** After 2+ quote proofs received (status=`PRICING_READY`)
- **Inputs:** `data/quote_master.csv`, Deep Read report, market freight rates
- **Outputs:** `pricing_<case_id>.json/.md` with full waterfall, margin scenarios, assumptions
- **Capability Bundle:** `profit-margin-analyzer`, `tariff-search`, `international-shipping-customs`, `finance`, `xlsx`
- **Quality Gates:** Complete cost waterfall, no invisible costs, unknown = conservative + flagged, price draft until approval

### Agent 6 — Compliance Agent (Draft-Only)
- **File:** `agents/compliance_agent.md`
- **Purpose:** Clause-by-clause compliance matrix, HSN/ITC-HS candidate, export policy, SCOMET check
- **Runs:** For export cases after Deep Read (status=`COMPLIANCE_REVIEW`)
- **Inputs:** Deep Read report, DGFT schedules, destination requirements
- **Outputs:** `compliance_draft_<case_id>.md/.json` (DRAFT ONLY)
- **Capability Bundle:** `international-shipping-customs`, `tariff-search`, `regulatory-legal`, `commercial-legal`
- **Quality Gates:** DGFT/SCOMET sources cited, HSN/origin = candidate only, SCOMET suspicion stops case

### Agent 7 — Pack Builder (Assembly)
- **File:** `agents/pack_builder_agent.md`
- **Purpose:** Complete bid pack (GOV) or export quote pack (EXPORT) for owner review
- **Runs:** After Pricing + Compliance (status=`ARTIFACT_PRODUCTION` → `APPROVAL_REQUIRED`)
- **Inputs:** All case reports, pricing, supplier shortlist, compliance draft, templates
- **Outputs:** `outputs/bid_packs/<case_id>/` or `outputs/export_quote_packs/<case_id>/`, approval card
- **Capability Bundle:** `pdf`, `docx`, `xlsx`, `pptx`, `invoice-generator` + document/presentation plugins
- **Quality Gates:** Pack includes cover, source list, risk register, missing-items list; artifacts opened/rendered/tested

### Agent 8 — Approval Desk (Decision Interface)
- **File:** `agents/approval_desk_agent.md`
- **Purpose:** Create structured approval cards for owner (decision in <2 minutes)
- **Runs:** After Pack Builder creates pack (status=`APPROVAL_REQUIRED`)
- **Inputs:** Pack, case record, `config/approval_policy.yaml`
- **Outputs:** `receipts/approvals/<case_id>_approval_card.html`, `approvals_receipts.csv` row (PENDING)
- **Capability Bundle:** `sales-negotiator`, `operations`, `legal`, `data`
- **Quality Gates:** Card readable in <2 min, benefit/risk/recovery/missing info explicit, status stays PENDING until receipt

### Agent 9 — Execution Tracker (Post-Approval Monitor)
- **File:** `agents/execution_tracker_agent.md`
- **Purpose:** Track outcomes after approval; alert on divergence; never re-execute
- **Runs:** Daily 17:00 IST (cron: `supplier_followup_review`) + 30-min buyer monitor
- **Inputs:** Approved cases, `approvals_receipts.csv`, `quote_master.csv`
- **Outputs:** Status transitions, receipts, follow-up flags, daily brief contributions
- **Capability Bundle:** `supplier-performance-manager`, `gmail-assistant`, `operations`, `productivity`
- **Quality Gates:** Receipts evidence-backed, overdue escalated not auto-sent, WON/LOST requires evidence

### Agent 10 — Owner Briefing Agent (Intelligence)
- **File:** `agents/owner_briefing_agent.md`
- **Purpose:** One crisp daily brief with one recommended action
- **Runs:** Daily 08:30 IST (cron: `morning_operator_brief`)
- **Inputs:** All registers, agent run logs, approvals, source health, scoring
- **Outputs:** `outputs/daily_briefs/brief_YYYYMMDD.html`
- **Capability Bundle:** `company-research`, `internal-comms`, `data`, `productivity`, `enterprise-search`
- **Quality Gates:** Signal over noise, top approvals/blockers/deadlines, ONE owner action

### Agent 11 — Codex Plugin Factory (Artifact Production)
- **File:** `agents/codex_plugin_factory_agent.md`
- **Purpose:** Use Codex runtime + plugins for spreadsheets, PDFs, DOCX, dashboards, packs
- **Runs:** After Hermes routing, on-demand for artifact production
- **Inputs:** `config/plugin_routing.yaml`, `data/capability_registry.csv`, `data/plugin_health.csv`
- **Outputs:** Artifacts under `outputs/`, plugin receipts under `receipts/plugin_runs/`
- **Capability Bundle:** All document/spreadsheet/presentation plugins + `claude-code-setup`, `github`, `testing-automation`
- **Quality Gates:** Plugin choice recorded, artifact validated, plugin receipt saved, bid-pack/quote-pack verification receipts match

---

## Status Flow (Canonical)

```
NEW → FAST_KILL → REJECTED
NEW → FAST_KILL → WATCHLIST → DEEP_READ → SUPPLIER_SEARCH → PRICING_READY
                                                        → ARTIFACT_PRODUCTION
                                                        → APPROVAL_REQUIRED
                                                        → APPROVED → SENT_OR_SUBMITTED
                                                        → CHANGES_REQUESTED (loop back)
                                                        → REJECTED (owner rejected)
SENT_OR_SUBMITTED → FOLLOW_UP → WON / LOST → ARCHIVED
```

**Status Definitions:**
- `NEW` — Radar created, not yet triaged
- `FAST_KILL` — Being evaluated by kill rules
- `REJECTED` — Hard kill with evidence-backed reason
- `WATCHLIST` — Borderline, needs human review or more data
- `DEEP_READ` — Full document extraction in progress/complete
- `SUPPLIER_SEARCH` — 5-3-2 sourcing active
- `PRICING_READY` — 2+ quote proofs received, waterfall built
- `ARTIFACT_PRODUCTION` — Pack Builder assembling pack
- `APPROVAL_REQUIRED` — Pack complete, approval card pending
- `APPROVED` — Owner approved, ready for execution
- `CHANGES_REQUESTED` — Owner asked for changes, loops to relevant stage
- `SENT_OR_SUBMITTED` — External action executed (bid sent, quote sent)
- `FOLLOW_UP` — Tracking response, delivery, payment
- `WON` / `LOST` — Terminal outcome with evidence
- `ARCHIVED` — Closed case

---

## Approval Boundaries (Non-Negotiable)

### Mode A — Autopilot (No Approval Required)
```
✓ Scan sources, extract fields from PDF
✓ Read tender documents
✓ Score opportunities
✓ Create case IDs
✓ Fast kill scoring
✓ Deep read extraction
✓ Identify candidate suppliers
✓ Prepare draft pricing
✓ Prepare draft compliance notes
✓ Generate daily brief
✓ Update internal registers
✓ Create Kanban tasks internally
✓ Produce internal artifact drafts
```

### Mode B — Approval-Gated (Owner Approval REQUIRED)
| Action | Type | Card Required |
|--------|------|---------------|
| Send supplier quote request | Per-case | ✅ |
| Send supplier clarification | Per-case | ✅ |
| Send supplier follow-up | Per-case | ✅ |
| Request supplier price/availability | Per-case | ✅ |
| Portal login/signup/credential creation | Per-source | ✅ |
| Send buyer RFQ reply | Per-case | ✅ |
| Send buyer introductory outreach | Per-case | ✅ |
| Send export quotation | Per-case | ✅ |
| **Submit tender bid** | Per-case + DSC | ✅ |
| Upload tender documents | Per-case | ✅ |
| Commit final price | Per-case | ✅ |
| Commit delivery timeline | Per-case | ✅ |
| Accept payment terms | Per-case | ✅ |
| Confirm HSN/ITC-HS classification | Per-case + Expert | ✅ |
| Claim country of origin | Per-case + Expert | ✅ |
| Pay EMD/bid security | Per-case | ✅ |
| Pay security deposit | Per-case | ✅ |
| Pay advance to supplier | Per-case | ✅ |
| Place supplier purchase order | Per-case | ✅ |
| Use DSC | Per-action | ✅ |
| Send invoice externally | Per-case | ✅ |
| Blacklist supplier permanently | Per-supplier | ✅ |
| Patch pricing/compliance skill | Per-change | ✅ |
| Enable credential-heavy plugin | Per-plugin | ✅ |
| Expose Hermes/Codex publicly | Per-action | ✅ |

### Mode C — Execution Tracker (Post-Approval Auto)
```
✓ Track supplier response
✓ Track bid submission status
✓ Track buyer follow-up
✓ Track quote validity
✓ Track delivery deadline
✓ Track payment status
✓ Record receipts
✓ Update case status
✓ Send internal reminders
✓ Update Kanban
✓ Sync approved artifacts to Drive
```

---

## Scheduled Operating Rhythm (Hermes Cron)

| Time (IST) | Job | Purpose | Runtime |
|------------|-----|---------|---------|
| 05:30 | Core Source Agent-Browser Radar | Capture GeM/CPPP/UNGM via read-only agent-browser | `hermes_no_agent_script` |
| 06:00 | Morning Opportunity Intelligence | Public intake, requirements, supplier 5-3-2, pricing drafts, HTML report | `hermes_no_agent_script` |
| 06:50 | Daily Shadow Profile Probe | Local profile evidence checks | `hermes_no_agent_script` |
| 07:05 | Daily Production Readiness Gate | Safe production-readiness gate + owner action packet | `hermes_no_agent_script` |
| 07:15 | V5 Prediction Shadow | Shadow-run demand forecast + low-competition intelligence | `hermes_no_agent_script` |
| 07:20 | Hermes Capability Truth Audit | Configured vs observed capabilities | `hermes_no_agent_script` |
| 08:30 | **Morning Operator Brief** | Canonical control tower from cases, approvals, health | `hermes_default` |
| 08:45 | Morning Agentic Review Enqueue | Create Kanban review card | `hermes_no_agent_script` |
| 09:00–21:59 (30min) | Buyer Reply Monitor | Gmail plugin inbound classification | `hermes_no_agent_script` |
| 12:30 | Daily Retender/Corrigenda Watch | Detect retenders, corrigenda, BOQ changes | `hermes_no_agent_script` |
| 13:00 | Midday Opportunity Radar | Canary-test live sources, evidence-only | `hermes_plus_codex_when_needed` |
| 17:00 | Supplier Follow-up Review | Check quotes, external inbox, blocked cases | `hermes_default` |
| 18:00 (Fri) | Weekly Learning Review | Wins/losses, source quality, propose memory/skill updates | `hermes_plus_chatgpt_snapshot` |
| 18:30 (Fri) | Weekly Learning Enqueue | Create Kanban review card | `hermes_no_agent_script` |
| 20:30 | Evening Execution Close | Reconcile, update Kanban, list blockers, tomorrow's action | `hermes_default` |

**Plus:** Monthly Strategy Deep Research (owner-approved only, ChatGPT Project)

---

## Key Configuration Files

```
config/
├── approval_policy.yaml          # What requires owner approval
├── agent_capability_routing.yaml # Best-in-class capability bundles per agent
├── agent_loops.json              # Bounded loop contracts
├── loop_schedule.json            # Scheduled cadence
├── kanban_board.yaml             # Board config, statuses, profiles
├── hermes_cron.yaml              # Cron job definitions
├── memory_policy.yaml            # Memory write approvals
├── plugin_routing.yaml           # Plugin routing rules
├── codex_runtime_policy.yaml     # Codex app-server policy
├── sources.gov.yaml              # Government tender sources
├── sources.export.yaml           # Export RFQ sources
├── sources.supplier.yaml         # Supplier sourcing channels
├── categories.yaml               # Product categories, active flags
├── kill_rules.yaml               # Ordered kill rules
├── scoring_weights.yaml          # Scoring factors
├── low_competition_keywords.yaml # Low-competition signals
├── sync_policy.yaml              # Google Drive sync rules
├── research_capture_routing.yaml # Deep Research vs operational capture
├── schemas/                      # JSON schemas for all registers
│   ├── master_cases.schema.json
│   ├── approvals_receipts.schema.json
│   ├── quote_master.schema.json
│   ├── supplier_master.schema.json
│   ├── event.schema.json
│   ├── approval_card.schema.json
│   ├── drive_manifest.schema.json
│   └── plugin_run_receipt.schema.json
└── compliance_by_category.yaml   # Category-specific compliance
```

---

## Data Registers (CSV Projections)

| Register | Purpose | Key Fields |
|----------|---------|------------|
| `master_cases.csv` | All tender/export cases | case_id, workflow_type, status, buyer, deadline, scores |
| `approvals_receipts.csv` | Approval cards + decisions | approval_id, case_id, action, status, approved_by/at |
| `supplier_master.csv` | Supplier directory + scores | supplier_id, products, certs, scores, quote history |
| `quote_master.csv` | Quote requests + responses | quote_id, case_id, supplier_id, price, status, proof |
| `source_health.csv` | Source reliability tracking | source_name, health_status, last_checked, relevance |
| `plugin_health.csv` | Plugin/tool health | plugin_or_tool, health_status, version, blocker |
| `buyer_demand_signals.csv` | Staged demand hypotheses | buyer, category, evidence_level, confidence |
| `outreach_queue.csv` | Approved outbound queue | case_id, target, message_type, status |
| `communication_log.csv` | All external comms log | case_id, direction, counterparty, timestamp |
| `agent_run_log.csv` | Every agent run record | agent_name, trigger, cases_processed, status, blockers |

---

## Output Artifacts Structure

```
outputs/
├── daily_briefs/              # brief_YYYYMMDD.html
├── case_reports/              # Per-case reports (deep_read, pricing, supplier, compliance)
├── bid_packs/                 # GOV bid packs per case_id
├── export_quote_packs/        # EXPORT quote packs per case_id
├── dashboards/                # Founder dashboards, scorecards
├── operating_desk/            # Daily operating desk reports
├── intraday_monitor/          # Intraday exception packets
├── learning_packets/          # Weekly learning packets
├── low_competition_radar/     # Radar outputs
├── demand_forecasting/        # V5 forecasts + calibration
├── source_canary/             # Live source canary results
├── evidence/                  # Captured evidence (private + redacted)
├── historical_intelligence/   # Gov historical captures
└── regression/                # Test matrix results

receipts/
├── approvals/                 # Approval cards + decision receipts
├── submissions/               # Bid/RFQ submission receipts
├── supplier_quotes/           # Quote proof receipts
├── owner_decisions/           # Owner decision receipts
├── executions/                # Execution milestone receipts
└── plugin_runs/               # Codex plugin run receipts
```

---

## Safety & Compliance Contracts

### Never Automated (Hard Blocks)
```
❌ Bid submission
❌ Tender portal upload
❌ DSC signing
❌ EMD/security payment
❌ Buyer quotation sending
❌ Supplier PO placement
❌ Supplier/buyer external outreach without approval
❌ Final price or delivery commitment
❌ Final HSN/ITC-HS classification
❌ Country-of-origin claim
❌ Legal/tax/compliance certification
❌ CAPTCHA/OTP/MFA/paywall bypass
❌ Credential/session/cookie/token/DSC/bank storage in repo
```

### Always Required
```
✅ Case_id on every action, file, receipt, decision
✅ Source citations on every owner-facing output
✅ Approval gate stops execution
✅ Agent run log row after every run
✅ Event ledger append for every durable state change
✅ No fabricated documents, certifications, eligibility, verification, claims, prices
✅ Codex App-Server Runtime for plugin-heavy work
✅ Hermes Kanban as default durable workboard
✅ ChatGPT receives bounded snapshots only
✅ data/events.jsonl = canonical state stream
✅ Owner decisions create receipts but never execute externally
```

---

## MCP Server (Bounded Tool Gateway)

The FastMCP server (`scripts/tender_os_mcp_server.py`) exposes **17 governed tools** to Hermes:

### Read-Only Tools (9)
| Tool | Purpose |
|------|---------|
| `capability_status` | Live bounded stack report |
| `get_case` | Read master-case row by case_id |
| `search_cases` | Search cases by status/workflow |
| `assess_opportunity` | Advisory scoring/Fast Kill |
| `get_source_health` | Source health evidence |
| `parse_local_documents` | Parse/hash 1-20 local docs |
| `capture_public_web` | Robots-compliant public HTTPS capture |
| `get_approval_status` | Read approval metadata |
| `evaluate_business_action` | T0-T5 policy probe (read-only) |

### Internal-Write Tools (8) — All Receipt-Backed, Idempotent
| Tool | Purpose |
|------|---------|
| `stage_case_transition` | Stage validated case transition |
| `attach_case_evidence` | Attach hashed evidence artifact |
| `stage_supplier_candidate` | Stage evidence-backed supplier |
| `record_quote_proof_review` | Record validated/rejected quote proof |
| `create_internal_approval_card` | Create pending approval card |
| `record_case_outcome` | Record verified case outcome |
| `stage_learning_proposal` | Stage reversible learning proposal |
| `reconcile_projection_from_receipt` | Stage projection reconciliation |

**Policy Engine:** Local OPA (`policies/tender_os_authorization.rego`) — fail-closed, every call leaves `policy.decision_recorded` event.

---

## Prediction Contract (Forecasting)

| Property | Value |
|----------|-------|
| `forecast_score` | Ranking score (NOT probability) |
| Current Model | `teos-expert-prior-v1` |
| Probability Status | `PRIOR_UNCALIBRATED` |
| Calibration Minimum | 30 mature outcomes |
| Required Tracking | forecast_date, eligible_for_backtest_at, feature_snapshot, predicted_probability, model_version, observed_outcome, maturity_status, brier_component |

**Until 30 mature outcomes:** Do not claim accuracy, precision, recall, or calibration. Research-only demand cannot receive high confidence. Pre-existing outcomes cannot be credited as forecast hits.

---

## Buyer Acquisition Lane

```
ChatGPT Deep Research (broad discovery)
       │
       ▼
Stage via `stage_buyer_market_research.py` → data/buyer_demand_signals.csv
       │
       ▼
Agent-Browser + Python/Playwright (exact capture)
       │
       ▼
Validate: buyer identity, procurement role, contact evidence
       │
       ▼
Gmail Plugin ONLY for approved sends
       │
       ▼
Owner approval for EVERY first contact, follow-up, quote, reply
```

**Critical Rules:**
- Catalogue fit = hypothesis, not RFQ
- Never guess email or label general sales address as procurement
- Opt-outs/bounces/not-interested = auto-stop outreach
- No auto-reply

---

## Running the System

### Morning (5-10 min)
```bash
# 1. Review daily brief
open outputs/daily_briefs/brief_$(date +%Y%m%d).html

# 2. Check approval cards
ls receipts/approvals/

# 3. Approve via Hermes
# approve case GOV-20260630-001
```

### Health Checks
```bash
# System health
python3 scripts/system_health_check.py --runtime

# Schema validation
python3 scripts/validate_register_schemas.py

# Projection rebuild
python3 scripts/rebuild_projections_from_events.py

# Case readiness
python3 scripts/validate_case_readiness.py --all
```

### Manual Operations
```bash
# Run specific agents
python3 scripts/run_source_adapter.py --adapter mock
python3 scripts/generate_daily_brief.py
python3 scripts/score_opportunity.py --case_id GOV-20260630-001
python3 scripts/reconcile_hermes_kanban.py
```

### Low-Competition Radar
```bash
python3 scripts/low_competition_order_radar.py --dry-run
python3 scripts/retender_corrigenda_watch.py --dry-run
python3 scripts/buyer_repeat_purchase_analyzer.py --dry-run
python3 scripts/supplier_ready_category_matcher.py --dry-run
```

---

## Folder Structure (Complete)

```
tender-export-os/
├── README.md                    # This system overview
├── ARCHITECTURE.md              # This file — complete architecture
├── AGENTS.md                    # Agent roster + responsibilities
├── HERMES.md                    # Hermes chief operator instructions
├── SOUL.md                      # Operating identity + non-negotiables
├── AGENT_REFERENCE.md           # Quick agent lookup card
├── manifest.json                # System metadata
├── docs/                        # Architecture & policy docs
├── config/                      # All configurable rules
│   ├── schemas/                 # JSON schemas
│   └── *.yaml                   # Source, kill, scoring, cron, kanban, etc.
├── data/                        # Master registers + canonical ledger
│   ├── events.jsonl             # ← CANONICAL APPEND-ONLY STATE
│   ├── *.csv                    # Projections
│   └── examples/                # Public template examples
├── agents/                      # 11 agent instruction files
├── scripts/                     # 200+ Python utilities
│   ├── source_adapters/         # Source-specific adapters
│   └── tests/                   # Test fixtures
├── templates/                   # Email, approval, brief templates
├── outputs/                     # Generated artifacts (gitignored)
├── receipts/                    # Immutable receipts (gitignored)
├── cases/                       # Per-case workspaces (gitignored)
├── runtime/                     # Codex bridge dirs (gitignored)
├── .github/workflows/           # CI: safe regression
├── .hermes/                     # Hermes profile config
├── skills/                      # Hermes skills (teos-ops bundle)
├── chatgpt_project/             # Boardroom prompts
├── scheduled_deep_research_tasks/ # ChatGPT scheduled prompts
└── workflows/                   # Runtime flow docs
```

---

## GitHub Repository

- **Remote:** `origin/feat/teos-production-readiness-governance`
- **Branch:** `feat/teos-production-readiness-governance` (ahead 5, behind 8)
- **CI:** `.github/workflows/ci.yml` — runs `run_full_safe_regression.py --include-pytest`
- **Architecture Docs:** This file + `docs/` directory

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v4.1.2 | 2026-07-30 | Hybrid Research + Capture correction, Low-Competition Radar lane |
| v4.1.1 | 2026-07-12 | Max-capability upgrade: cron, Kanban, evidence bundles, task graphs |
| v4.1.0 | 2026-06-30 | Event-ledger hardening, Hermes-native control plane, Codex runtime |
| v3.1   | 2026-06-15 | Original runtime system |

---

## Quick Reference: Agent → Capability Bundle Mapping

| Agent | Primary Capability Bundle | Key Config |
|-------|---------------------------|------------|
| Hermes Chief Operator | `operations, productivity, enterprise-search, data` + `teos-ops` | `config/kanban_board.yaml`, `config/hermes_cron.yaml` |
| Radar Agent | `company-research, market-insight-product-selection, browser/playwright, data` | `config/sources.gov.yaml`, `config/sources.export.yaml` |
| Fast Kill Agent | `market-viability-logic-auditor, operations, data` | `config/kill_rules.yaml`, `config/scoring_weights.yaml` |
| Deep Read Agent | `pdf, docx, xlsx` + document plugins | `config/scoring_weights.yaml` |
| Supplier Engine | `product-supplier-sourcing, supplier-performance-manager, 1688-sourcing` | `config/sources.supplier.yaml`, 5-3-2 rule |
| Pricing Agent | `profit-margin-analyzer, tariff-search, international-shipping-customs, finance` | `config/pricing_assumptions.yaml` |
| Compliance Agent | `international-shipping-customs, tariff-search, regulatory-legal` | `config/compliance_by_category.yaml` |
| Pack Builder | `pdf, docx, xlsx, pptx, invoice-generator` + doc plugins | `templates/` |
| Approval Desk | `sales-negotiator, operations, legal, data` | `config/approval_policy.yaml` |
| Execution Tracker | `supplier-performance-manager, gmail-assistant, operations` | `config/approval_policy.yaml` (Mode C) |
| Owner Briefing | `company-research, internal-comms, data, productivity` | `templates/daily_brief.html` |
| Codex Plugin Factory | All doc/sheet/pres plugins + `claude-code-setup, github, testing` | `config/plugin_routing.yaml`, `config/codex_runtime_policy.yaml` |

---

*This architecture document is the single source of truth for Tender Export OS v4.1 system design. All agents, configs, and workflows derive from this specification.*