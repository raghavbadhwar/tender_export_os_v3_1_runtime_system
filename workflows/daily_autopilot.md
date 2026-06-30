# Daily Autopilot Workflow

## Overview
The daily autopilot is the heartbeat of the Tender + Export OS. It runs every morning and ensures no opportunity is missed, no case stalls, and the owner receives a clear brief before starting their day.

---

## When It Runs
- **Morning Operator Brief:** 08:30 IST via Hermes cron.
- **Midday Opportunity Radar:** 13:00 IST via Hermes cron.
- **Supplier Follow-up Review:** 17:00 IST via Hermes cron.
- **Evening Execution Close:** 20:30 IST via Hermes cron.
- **Manual trigger:** `run daily autopilot`, `scan today`, or task-specific Hermes commands.
- **Duration:** 20-45 minutes for a typical scan/processing run.
- **Notifications:** Delivery uses the configured Hermes gateway. If no gateway is configured, save local reports and surface the path to the owner.

---

## Step-by-Step Autopilot Flow

### Phase 1 — Morning Operator Brief (08:30)
**Agent: Hermes Chief Operator**

1. Read Knowledge Bus registers, Kanban, memory policy, approval queue, source health, and plugin health.
2. Produce one crisp owner brief.
3. Recommend one smallest useful owner action.
4. Do not scan deep sources unless the morning command explicitly includes a scan.

**Output:** Owner brief and current blocker/approval summary.

---

### Phase 2 — Scan (13:00–13:30)
**Agent: Radar Agent**

1. Load `config/sources.gov.yaml` and `config/sources.export.yaml`
2. Skip Broken, Paywalled sources
3. For each active source: extract new opportunities from last 24 hours
4. Dedup against existing master_cases.csv
5. Create new case IDs and rows for unique opportunities
6. Update source_health.csv
7. Log run

**Output:** N new cases with status = NEW

---

### Phase 3 — Filter (13:30–13:45)
**Agent: Fast Kill Agent**

1. Load all cases with status = NEW
2. Apply kill rules from kill_rules.yaml in sequence
3. Update status: REJECTED / WATCHLIST / DEEP_READ
4. Write no_go notes for REJECTED cases
5. Log run

**Output:** Rejected cases closed with reason. Surviving cases passed forward.

---

### Phase 4 — Extract (14:00–14:30)
**Agent: Deep Read Agent**

1. Load all cases with status = DEEP_READ
2. Download and parse all available documents (PDF, web, BOQ)
3. Extract full structured data
4. Compute full opportunity score
5. Recheck kill rules with full data
6. Update status: SUPPLIER_SEARCH (or REJECTED if new kill triggered)
7. Save deep read reports
8. Log run

**Output:** Fully extracted case records, deep read report files

---

### Phase 5 — Source (14:30–15:00)
**Agent: Supplier Engine Agent**

1. Load all cases with status = SUPPLIER_SEARCH
2. Check internal supplier master first
3. Search 3+ source types per case
4. Find 5+ candidates per case
5. Score candidates
6. Prepare shortlist report
7. Prepare draft quote requests (pending approval)
8. Create approval cards for quote request sends
9. Log run

**Output:** Supplier shortlists, draft quote requests, approval cards

---

### Phase 6 — Compliance
**Agent: Compliance Agent** (EXPORT cases only)

1. Load EXPORT cases in SUPPLIER_SEARCH with deep read complete
2. Draft ITC-HS candidate classification
3. Check export policy, SCOMET flags
4. Prepare full compliance note
5. Save compliance drafts
6. Flag SCOMET or Prohibited cases for immediate REJECTED update
7. Log run

---

### Phase 7 — Price
**Agent: Pricing Agent** (parallel with Compliance)

1. Load cases in SUPPLIER_SEARCH with 2+ quotes received
2. Build cost waterfall (GOV or EXPORT)
3. Save pricing reports with 3 price options
4. Update status: PRICING_READY
5. Log run

---

### Phase 8 — Artifact Production
**Agent: Pack Builder**

1. Load PRICING_READY cases
2. Assemble bid pack (GOV) or export quote pack (EXPORT)
3. Flag all unresolved gaps in missing_items file
4. Save pack files
5. Log run
6. Use Codex App-Server Runtime for plugin-heavy document/spreadsheet/PDF/dashboard work

---

### Phase 9 — Approval Cards
**Agent: Approval Desk**

1. Create approval cards for all packed cases
2. Create approval cards for pending supplier quote requests
3. Update status: APPROVAL_REQUIRED
4. Update approvals_receipts.csv
5. Log run

---

### Phase 10 — Evening Execution Close (20:30)
**Agent: Hermes Chief Operator / Owner Briefing Agent**

1. Read all updated data files
2. Update Kanban blockers and next actions
3. Build close-of-day summary if useful
4. Log run

---

## Error Recovery
- If any agent fails: log error, skip that phase for that case, continue with next case
- Never let one bad case break the full pipeline
- Errors always appear in the daily brief under Risks and Blockers

---

## Weekend Mode
On weekends: Run brief only (no new scanning unless manually triggered)
Rationale: Government portals rarely publish on weekends. Avoid redundant runs.
