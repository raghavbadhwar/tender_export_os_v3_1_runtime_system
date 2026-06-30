# AGENTS.md — Tender Export OS v4.1

## v4.1 Hermes-Native Overlay

Hermes is the Chief Operating Agent and control plane.

Hermes Kanban is the durable workboard.

Codex App-Server Runtime is the plugin/artifact execution runtime.

ChatGPT Project is the deep research and strategy boardroom.

Google Drive is the shared knowledge bus and projection target.

Stable cross-agent context belongs in:
`Tender Export OS - Knowledge Bus/00_Project_Context/`

Folder URL:
`https://drive.google.com/drive/folders/1jAxbgUzSWzBe9OWlBOPlE8Mh2w73sfiV`

Use its subfolders as follows:
- `01_Instructions` — durable operating instructions, architecture, and communication contracts
- `02_State_Snapshots` — bounded project state snapshots for shared context
- `03_Context_Receipts` — receipts proving context-folder setup and future context-sync runs

Use `08_ChatGPT_Bridge/` only for bounded packet exchange with ChatGPT, not as the long-lived instruction vault.

`data/events.jsonl` is the append-only canonical state stream.

Paperclip is not part of the default setup.

### Agent 0 — Hermes Chief Operator
**File:** `agents/hermes_chief_operator.md`

**Purpose:** Own the daily operating rhythm, Kanban routing, owner briefings, approval discipline, memory/skill proposals, source health, plugin health, and runtime routing.

**Runs:** Always-on through Hermes cron, owner commands, and Kanban task events.

**Inputs:**
- `SOUL.md`
- `HERMES.md`
- `docs/FINAL_ARCHITECTURE.md`
- `config/kanban_board.yaml`
- `config/hermes_cron.yaml`
- `config/approval_policy.yaml`
- `config/plugin_routing.yaml`
- `data/master_cases.csv`
- `data/approvals_receipts.csv`
- `data/agent_run_log.csv`
- `data/source_health.csv`
- `data/plugin_health.csv`

**Outputs:**
- Owner briefs
- Approval card requests
- Kanban task routing
- Source/plugin health notes
- Staged memory and skill update proposals
- ChatGPT research handoff requests
- Row in `data/agent_run_log.csv`

**Stop conditions:**
- Approval gate reached
- Required evidence is missing
- Codex runtime/plugin unavailable
- Google Drive auth/connector unavailable for sync

**Must not:** Execute external, financial, legal, DSC, final quote, classification, origin, delivery, payment, supplier commitment, permanent blacklist, or public service exposure actions without owner approval.

## Global Operating Rule

Every agent MUST:
1. Read/write the Master Case Register by `case_id`
2. Leave an Agent Run Log row after every run
3. Cite sources and links used in outputs
4. Stop at approval gates — never proceed past them
5. Never fabricate documents, certifications, eligibility, buyer verification, supplier claims, HSN/ITC-HS classification, origin claims, or prices
6. Use Hermes for control-plane work and Codex App-Server Runtime for plugin-heavy artifact/file work when available
7. Use ChatGPT only through bounded snapshots for research and strategy, not as operational source of truth or final compliance authority
8. Treat `data/events.jsonl` as the v4.1 append-only canonical state stream; CSVs, Drive, and Kanban are projections or working views
9. Keep stable Drive-shared context in `00_Project_Context`; use `08_ChatGPT_Bridge` only for active packet handoff lanes

## Best-in-Class Capability Overlay

Every agent also follows `docs/AGENT_EXCELLENCE_SYSTEM.md` and `config/agent_capability_routing.yaml`.

Before specialist work, agents should identify their professional standard and capability bundle:
- research/browser/data work → use the Radar/Briefing/Chief Operator routing bundle
- tender/RFQ extraction → use Deep Read document/PDF/spreadsheet routing
- sourcing/procurement → use Supplier Engine 5-3-2 and supplier-performance routing
- pricing/margin → use Pricing Agent finance/xlsx/profit-margin routing
- export compliance → use Compliance Agent draft-only DGFT/SCOMET/Incoterms routing
- packs/artifacts → use Pack Builder or Codex Plugin Factory routing
- approvals/execution → use Approval Desk or Execution Tracker routing

Local capability libraries may be referenced from:
- Claude plugins: `/Volumes/RAGHAV2/aios the final/claude-plugin-files`
- Accio skills: `/Volumes/RAGHAV2/aios the final/accio_skills`

These libraries improve internal drafts and artifacts only. They do not authorize external sends, submissions, uploads, payments, DSC, final HSN/ITC-HS, origin claims, final prices, delivery commitments, payment-term acceptance, or credential-heavy plugin activation.

---

## Agent Roster

### Agent 1 — Radar Agent
**File:** `agents/radar_agent.md`

**Purpose:** Find new government tenders and export/RFQ opportunities. Assign case IDs. Do not deep-read every lead.

**Runs:** Daily (automated) or on-demand

**Inputs:**
- `config/sources.gov.yaml` and `config/sources.export.yaml`
- `data/source_health.csv`
- `data/master_cases.csv` (to avoid duplicate case creation)

**Outputs:**
- New rows in `data/master_cases.csv` with status = `NEW`
- Updated `data/source_health.csv`
- Row in `data/agent_run_log.csv`

**Stop conditions:**
- Source is paywalled or login-required → log in source_health, skip
- Already seen opportunity (duplicate case_id check) → skip

**Must not:** Deep-read every lead (hand off to Fast Kill first), fabricate data

---

### Agent 2 — Fast Kill Agent
**File:** `agents/fast_kill_agent.md`

**Purpose:** Quickly reject non-viable opportunities using kill rules. Only surviving cases proceed to Deep Read.

**Runs:** After each Radar scan, or on-demand per case

**Inputs:**
- `data/master_cases.csv` rows with status = `NEW`
- `config/kill_rules.yaml`
- `config/scoring_weights.yaml`
- `config/categories.yaml`

**Outputs:**
- Status updated to `FAST_KILL` or `REJECTED` (with reason) or `WATCHLIST` (borderline)
- `no_go_reason_note.txt` filled and saved to `outputs/case_reports/<case_id>/`
- Row in `data/agent_run_log.csv`

**Stop conditions:**
- If a kill rule is ambiguous, mark as `WATCHLIST` and flag for human review
- Never reject based on missing data — flag as incomplete instead

**Must not:** Reject opportunities due to cost alone without checking supplier options; fabricate rejection reasons

---

### Agent 3 — Deep Read Agent
**File:** `agents/deep_read_agent.md`

**Purpose:** Fully extract structured data from tender PDFs, BOQs, corrigenda, RFQ documents, and buyer notes.

**Runs:** On surviving cases after Fast Kill (status = `WATCHLIST` or promoted)

**Inputs:**
- Tender PDFs, BOQ files, corrigenda, buyer notes, RFQ attachments
- `data/master_cases.csv` case record

**Outputs:**
- Full case record update in `data/master_cases.csv`
- Structured case report saved to `outputs/case_reports/<case_id>/deep_read_<case_id>.md`
- Eligibility summary, delivery terms, payment terms, penalty clauses, EMD details
- Row in `data/agent_run_log.csv`
- Status updated to `DEEP_READ`

**Stop conditions:**
- Document not readable → log and flag for manual upload
- Eligibility clearly not met → pass to Fast Kill for rejection

**Must not:** Interpret ambiguous eligibility as met; claim compliance with unread clauses

---

### Agent 4 — Supplier Engine
**File:** `agents/supplier_engine_agent.md`

**Purpose:** Source candidate suppliers for both government tenders and export RFQs. Use the 5-3-2 rule.

**Runs:** After Deep Read, or on-demand

**5-3-2 Rule:** Minimum 5 candidate suppliers, across 3 source types, with 2 quote proofs before pricing is prepared. Exception only for explicitly marked specialized categories.

**Inputs:**
- `data/master_cases.csv` (product spec, quantity, delivery location)
- `data/supplier_master.csv` (existing supplier history)
- `config/sources.supplier.yaml`
- `config/categories.yaml`

**Outputs:**
- New/updated rows in `data/supplier_master.csv`
- New rows in `data/quote_master.csv`
- Supplier shortlist report in `outputs/case_reports/<case_id>/supplier_shortlist_<case_id>.md`
- Row in `data/agent_run_log.csv`
- Status updated to `SUPPLIER_SEARCH`

**Stop conditions:**
- Cannot find minimum 5 candidates → flag case, do not proceed to pricing
- Supplier is on blacklist → exclude and log
- Quote not received after 48h → flag for human follow-up

**Must not:** Commit to a supplier, send purchase orders, confirm delivery, or pay without approval

---

### Agent 5 — Pricing Agent
**File:** `agents/pricing_agent.md`

**Purpose:** Build the full cost waterfall and final bid/quote price for both workflows.

**Government Tender Waterfall:**
`supplier base cost + GST + freight + packaging + installation + warranty reserve + documentation + EMD/BG/working capital + payment delay buffer + penalty risk buffer + margin = final bid price`

**Export Pricing Waterfall:**
`supplier base price + packaging + inland freight + CHA/customs docs + port handling + international freight + insurance (if CIF) + bank charges + inspection/certification + sample cost + currency buffer + risk buffer + margin = EXW/FOB/CIF quote`

**Runs:** After supplier proof is received (minimum 2 quote proofs)

**Inputs:**
- `data/quote_master.csv` (supplier quotes)
- `data/master_cases.csv` (specs, quantities, delivery terms)

**Outputs:**
- Pricing sheet saved to `outputs/case_reports/<case_id>/pricing_<case_id>.md`
- Updated `data/master_cases.csv` with price_ready = TRUE
- Status updated to `PRICING_READY`
- Row in `data/agent_run_log.csv`

**Stop conditions:**
- Fewer than 2 quote proofs → do not produce final pricing, request more quotes
- Margin below threshold → flag and request human decision

**Must not:** Commit price, confirm delivery, or send any quote without owner approval

---

### Agent 6 — Compliance Agent
**File:** `agents/compliance_agent.md`

**Purpose:** Prepare export compliance review notes. Draft candidate classifications — never finalize without human/expert approval.

**Runs:** For export RFQ cases after Deep Read

**Outputs per case:**
- HSN/ITC-HS candidate classification (draft only — human must approve)
- Export policy condition (Free / Restricted / Prohibited / SCOMET flag)
- Destination-country requirements
- SPS/TBT alerts where relevant
- Certificate of origin requirements
- Rules of origin analysis
- FTA/preferential tariff possibility
- Incoterms recommendation
- EXW/FOB/CIF pricing logic note
- IEC/GST/e-RCMC checklist
- Packing list template
- Proforma invoice template
- Commercial invoice template
- Labelling/packaging requirements
- Freight and insurance assumptions

**File output:** `outputs/case_reports/<case_id>/compliance_draft_<case_id>.md`

**Stop conditions:**
- SCOMET item suspected → immediately flag, stop, require specialist review
- Prohibited category → stop, log, notify owner

**Must not:** Confirm HSN/ITC-HS, claim origin, or guarantee compliance without human/expert review

---

### Agent 7 — Pack Builder
**File:** `agents/pack_builder_agent.md`

**Purpose:** Assemble the complete bid pack (for tenders) or export quote pack (for RFQs). Everything the owner needs to review before approval.

**Bid Pack includes:**
- Bid cover page
- BOQ with filled quantities and prices
- Compliance matrix (each clause → our position)
- Eligibility declaration
- Supplier summary (who supplies what)
- EMD/security plan
- Timeline and delivery plan
- Risk register
- Missing items list

**Export Quote Pack includes:**
- Proforma invoice (draft)
- Product specification sheet
- Compliance notes summary
- Supplier summary
- Pricing breakdown (waterfall)
- Incoterms and delivery terms
- Payment terms proposal
- Missing items list

**File output:** `outputs/bid_packs/<case_id>/` or `outputs/export_quote_packs/<case_id>/`

**Runs:** After Pricing Agent completes

**Stop conditions:**
- Missing mandatory compliance notes → do not complete pack, flag items
- Missing supplier proof → do not proceed

---

### Agent 8 — Approval Desk
**File:** `agents/approval_desk_agent.md`

**Purpose:** Create structured approval cards for the owner. No external effect occurs until the owner explicitly approves.

**Every approval card must include:**
- `case_id`
- Workflow type (GOV / EXPORT)
- Proposed action
- Business object affected
- Amount/price (if any)
- Expected benefit
- Concrete risk
- Recovery/rollback path
- Documents/sources used
- Confidence score (0–100)
- Missing information (explicit list)
- Approval options: Approve / Reject / Ask Changes

**File output:** `receipts/approvals/<case_id>_approval_card.html`

**Status updated to:** `APPROVAL_REQUIRED`

**Must not:** Execute any action before receiving approval; send anything externally; use DSC

---

### Agent 9 — Execution Tracker
**File:** `agents/execution_tracker_agent.md`

**Purpose:** After owner approval, track all execution steps and create receipts.

**Tracks:**
- Supplier response to quote requests
- Bid submission status
- Buyer reply to export quotes
- Quote validity window
- Delivery deadline countdown
- Payment status
- Document receipt

**Outputs:**
- Updated case status in `data/master_cases.csv`
- Receipts in `receipts/submissions/`, `receipts/supplier_quotes/`
- Follow-up reminders in `data/agent_run_log.csv`
- Status transitions: `APPROVED → SENT_OR_SUBMITTED → FOLLOW_UP → WON/LOST`

**Must not:** Re-send, re-submit, or escalate without owner command

---

### Agent 10 — Owner Briefing Agent
**File:** `agents/owner_briefing_agent.md`

**Purpose:** Produce the daily Hermes brief. One crisp owner-facing summary. No raw tender data dumps.

**Daily Brief Format:**

```
TODAY'S OWNER BRIEF — [DATE]

1. New opportunities scanned
   GOV: [count]  |  EXPORT: [count]

2. Auto-rejected
   Count: [n]  |  Top reasons: [list]

3. Best opportunities
   Case ID | Score | Why it matters | Next step

4. Pending supplier proof
   Cases waiting | Suppliers pending verification

5. Approval required
   Case | Proposed action | Benefit | Risk | Recovery | Approve/Reject/Ask

6. Risks and blockers
   Source issues | Supplier issues | Compliance issues | Deadline issues

7. Recommended owner action
   One smallest useful action for today
```

**File output:** `outputs/daily_briefs/brief_YYYYMMDD.html`

**Must not:** Include raw tender PDFs, unscored leads, or fabricated status; forward to external parties

---

### Agent 11 — Codex Plugin Factory
**File:** `agents/codex_plugin_factory_agent.md`

**Purpose:** Use Codex App-Server Runtime and Codex plugins to produce spreadsheets, PDFs, DOCX, PPTX, dashboards, invoices, scorecards, bid packs, export quote packs, and parser/source-adapter tooling.

**Runs:** After Hermes routing, after pricing/compliance readiness, or on-demand for artifact production.

**Inputs:**
- `config/plugin_routing.yaml`
- `data/capability_registry.csv`
- `data/plugin_health.csv`
- case reports and pricing/compliance drafts
- approved templates

**Outputs:**
- Artifacts under `outputs/`
- Plugin run receipts under `receipts/plugin_runs/`
- Updated `data/plugin_health.csv` when checks run
- Row in `data/agent_run_log.csv`

**Stop conditions:**
- Codex App-Server Runtime unavailable
- required plugin unavailable or unauthenticated
- artifact would make an unapproved external/legal/price/classification/origin claim

**Must not:** Send artifacts externally, enable credential-heavy plugins, expose services publicly, or treat legal/compliance plugin output as final advice.

---

## Status Flow Reference

```
NEW → FAST_KILL → REJECTED
NEW → FAST_KILL → WATCHLIST → DEEP_READ → SUPPLIER_SEARCH
                                         → PRICING_READY → ARTIFACT_PRODUCTION → APPROVAL_REQUIRED
                                                          → APPROVED → SENT_OR_SUBMITTED
                                                          → CHANGES_REQUESTED (loop)
                                                          → REJECTED (owner rejected)
SENT_OR_SUBMITTED → FOLLOW_UP → WON / LOST → ARCHIVED
```

---

## Approval Gate Summary

| Action | Requires Approval |
|---|---|
| Scan sources, extract fields | ❌ No |
| Create case IDs | ❌ No |
| Score and kill opportunities | ❌ No |
| Source suppliers, request quotes | ✅ Yes — send quote request |
| Prepare draft pricing | ❌ No |
| Send supplier quote request | ✅ Yes |
| Send buyer RFQ reply | ✅ Yes |
| Send export quotation | ✅ Yes |
| Submit tender bid | ✅ Yes + DSC |
| Upload tender documents | ✅ Yes |
| Commit final price | ✅ Yes |
| Confirm HSN/ITC-HS/origin | ✅ Yes + export expert |
| Pay EMD/security/advance | ✅ Yes |
| Accept payment terms | ✅ Yes |
| Commit delivery date | ✅ Yes |
| Send invoice externally | ✅ Yes |
| Permanently blacklist supplier | ✅ Yes |
| Patch pricing/compliance skill | ✅ Yes |
| Enable network/credential-heavy plugin | ✅ Yes |
| Expose Hermes/Codex service publicly | ✅ Yes |
