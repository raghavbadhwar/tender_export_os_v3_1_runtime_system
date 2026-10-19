# Codex Runtime Instructions — Tender Export OS v4

## v4 Runtime Role

Codex is the artifact/runtime factory inside the Hermes-native control plane.

Hermes routes work, owns approvals, tracks Kanban, manages memory/skills, and decides when Codex should run.

Codex handles:
- tender PDF and BOQ parsing
- structured file edits
- spreadsheets, PDFs, DOCX, PPTX, dashboards, invoices, scorecards, bid packs, export quote packs
- source adapter repair and tests
- plugin inventory checks

Prefer Codex App-Server Runtime when Hermes supports it:

```text
/codex-runtime codex_app_server
```

If unavailable, use:

```text
/codex-runtime auto
```

Before assuming exact local commands, run:

```bash
python3 scripts/check_codex_runtime_readiness.py
```

## How to Give Codex Tasks

Use these exact instruction patterns when giving tasks to Codex. Each task type has a standard instruction block.

---

## Agent Loop Guardrails

Before creating, changing, or running a new repeatable automation pattern, check the loop registry:

```bash
python scripts/validate_agent_loops.py
python scripts/validate_loop_schedule.py
```

Loop source of truth:
- Machine-readable registry: `config/agent_loops.json`
- Human-readable handoff: `workflows/agent_loop_runtime.md`

Schedule source of truth:
- Machine-readable schedule: `config/loop_schedule.json`
- Human-readable schedule: `workflows/agent_loop_schedule.md`
- Daily scheduled prompt: `codex/scheduled_daily_autopilot_prompt.md`
- Intra-day scheduled prompt: `codex/scheduled_intraday_monitor_prompt.md`

Every runtime loop must include:
- `case_id`-based state where cases are involved
- explicit stop conditions
- max iteration count and timeout
- approval gates for every external, legal, financial, or DSC action
- append-only `data/agent_run_log.csv` updates
- source citations in generated outputs

If the loop reaches an approval-gated action, stop and create an approval card. Do not execute the action.

Default v4 Hermes cron schedule:
- Morning Operator Brief: 08:30 IST daily
- Midday Opportunity Radar: 13:00 IST daily
- Supplier Follow-up Review: 17:00 IST daily
- Evening Execution Close: 20:30 IST daily
- Weekly Learning Review: Friday 18:00 IST
- Event-driven runs: new documents, quote proofs, owner decisions, approved-action tracking

---

## Task Type 1: Run Daily Autopilot

```
Task: Run daily autopilot for Tender + Export OS
Date: [TODAY'S DATE]

Instructions:
1. Read config/sources.gov.yaml and config/sources.export.yaml
2. Run Radar Agent — scan all Working sources, create NEW cases in master_cases.csv
3. Run Fast Kill Agent on all NEW cases — apply kill_rules.yaml, update status
4. Run Deep Read Agent on all DEEP_READ cases — extract full fields, save case reports
5. Run Supplier Engine on DEEP_READ cases — source 5+ suppliers, save shortlists
6. Run Compliance Agent on EXPORT SUPPLIER_SEARCH cases — save compliance drafts
7. Run Pricing Agent on cases with 2+ confirmed quotes — save pricing reports
8. Run Pack Builder on PRICING_READY cases — save bid/quote packs, create approval cards
9. Run Owner Briefing Agent — generate outputs/daily_briefs/brief_[DATE].html
10. Log all runs to data/agent_run_log.csv

Output required:
- Updated data/master_cases.csv
- All new case report files
- Daily brief HTML
- Any approval card HTML files

Do NOT:
- Send any emails
- Submit any bids
- Contact suppliers externally
- Store credentials
```

---

## Task Type 2: Scan Specific Source

```
Task: Scan [SOURCE NAME] for new opportunities
Source URL: [URL]
Workflow: [GOV / EXPORT]

Instructions:
1. Access the source URL
2. Extract all new opportunities published in the last 24 hours
3. For each: extract title, buyer, deadline, EMD (if shown), value (if shown), category
4. Check against existing master_cases.csv for duplicates
5. Create new case IDs for new opportunities
6. Add rows to master_cases.csv with status = NEW
7. Update data/source_health.csv with today's check result
8. Log run to agent_run_log.csv

Return: Number of new cases created, any source errors
```

---

## Task Type 3: Deep Read a PDF/Document

```
Task: Deep read tender document for case [CASE_ID]
Documents: [List of PDF files or URLs]

Instructions:
1. Read all provided documents carefully — including corrigenda if present
2. Extract all fields from the Deep Read Agent instruction file
3. Check corrigenda dates — later corrigenda override earlier documents
4. Flag any ambiguous eligibility clauses verbatim
5. Compute full opportunity score using scoring_weights.yaml
6. Check if any new kill rules are triggered after deep read
7. Save deep read report to outputs/case_reports/[CASE_ID]/deep_read_[CASE_ID].md
8. Update master_cases.csv with all extracted fields
9. Update status to SUPPLIER_SEARCH (or REJECTED if new kill triggered)
10. Log to agent_run_log.csv

Do NOT: Interpret ambiguous eligibility as met
```

---

## Task Type 4: Source Suppliers for a Case

```
Task: Source suppliers for case [CASE_ID]
Product: [PRODUCT NAME]
Specs: [KEY SPECS FROM DEEP READ]
Quantity: [QTY AND UNIT]
Delivery Location: [LOCATION]
Workflow: [GOV / EXPORT]

Instructions:
1. Check data/supplier_master.csv for known suppliers matching product
2. Search IndiaMART, TradeIndia, GeM (for GOV), APEDA (for agri export)
3. Search at least 3 different source types
4. Find minimum 5 candidate suppliers
5. Check each against blacklist in supplier_master.csv
6. Score each supplier using supplier scoring factors
7. Shortlist top 3 for quote request
8. Prepare quote request drafts using templates/supplier_quote_request.txt
9. Save shortlist report to outputs/case_reports/[CASE_ID]/supplier_shortlist_[CASE_ID].md
10. Add new suppliers to supplier_master.csv
11. Create approval card for sending quote requests
12. Log to agent_run_log.csv

Do NOT: Actually send any quote requests — approval required first
```

---

## Task Type 5: Build Pricing for a Case

```
Task: Build pricing for case [CASE_ID]
Quotes available: [N quotes in quote_master.csv]
Workflow: [GOV / EXPORT]

Instructions:
1. Verify: minimum 2 quote proofs received in quote_master.csv
2. Read deep read report for specs, delivery, payment terms
3. Build complete cost waterfall (GOV or EXPORT template from pricing_agent.md)
4. Show 3 price options: Conservative, Recommended, Aggressive
5. Flag every assumption and uncertain cost line
6. Save to outputs/case_reports/[CASE_ID]/pricing_[CASE_ID].md
7. Update master_cases.csv: pricing_done = TRUE, status = PRICING_READY
8. Log to agent_run_log.csv

Return: Recommended price, margin %, confidence score
```

---

## Task Type 6: Generate Daily Brief

```
Task: Generate daily owner brief
Date: [TODAY'S DATE]
Output file: outputs/daily_briefs/brief_[DATE].html

Instructions:
1. Read data/master_cases.csv — all active cases
2. Read data/agent_run_log.csv — today's runs
3. Read data/approvals_receipts.csv — pending approvals
4. Read data/source_health.csv
5. Build brief using format in agents/owner_briefing_agent.md
6. Use templates/daily_brief.html as the HTML template
7. Fill all 7 sections
8. Save HTML to outputs/daily_briefs/brief_[DATE].html
9. Log to agent_run_log.csv

Do NOT: Include raw tender text, unscored leads, or agent run details in the brief
```

---

## Task Type 7: Create Approval Card

```
Task: Create approval card for case [CASE_ID]
Action requiring approval: [ACTION]
Data sources: [List relevant files]

Instructions:
1. Read case data from master_cases.csv
2. Read relevant case reports from outputs/case_reports/[CASE_ID]/
3. Build approval card using approval_card.html template
4. Fill ALL required fields from approval_policy.yaml
5. Compute confidence score honestly (lower if data is thin)
6. List all missing information explicitly
7. Save to receipts/approvals/[CASE_ID]_approval_card.html
8. Add row to data/approvals_receipts.csv (status = PENDING)
9. Update master_cases.csv: status = APPROVAL_REQUIRED
10. Log to agent_run_log.csv

Do NOT: Pre-fill the approval decision. Do NOT execute any action.
```

---

## Error Handling Rules

| Error | Action |
|---|---|
| PDF unreadable / password | Log as error, flag in brief, do not guess |
| Source returns 403/CAPTCHA | Log as Manual Check Required in source_health |
| Fewer than 5 supplier candidates | Flag case as WATCHLIST, do not proceed to pricing |
| Fewer than 2 quote proofs | Do not run pricing, log gap |
| Kill rule triggered after deep read | Update to REJECTED, write no_go note |
| SCOMET detected | Immediate REJECTED, escalate in brief |
