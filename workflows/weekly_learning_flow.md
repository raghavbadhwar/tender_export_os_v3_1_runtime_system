# Weekly Learning Flow

## Purpose
Review the week as an operating system, not as a loose chat summary. The output is a small set of approved improvements to sources, suppliers, pricing, compliance, prompts, memory, and skills.

## Cadence
Friday 18:00 IST via Hermes cron.

## Runtime
Hermes default runtime, with Codex for table/artifact updates and ChatGPT Project for strategic review when needed.

## Inputs
- `data/master_cases.csv`
- `data/agent_run_log.csv`
- `data/source_health.csv`
- `data/plugin_health.csv`
- `data/supplier_master.csv`
- `data/quote_master.csv`
- approval receipts
- owner corrections
- generated case reports

## Flow
1. Hermes reads closed, rejected, won, lost, and blocked cases.
2. Hermes identifies repeated source, supplier, pricing, compliance, and routing issues.
3. Codex generates `data/chatgpt_snapshot.md` if strategy review is useful.
4. ChatGPT Project reviews bounded strategy questions only.
5. Hermes stages memory updates for durable lessons.
6. Hermes stages skill/rule/config changes for owner approval.
7. Approval cards are created for pricing/compliance skill changes or risky plugin changes.
8. Approved changes are applied by Codex and logged.

## Stop Conditions
- missing source data blocks evidence-backed conclusions
- proposed change affects pricing/compliance/approval boundaries
- ChatGPT output is uncited or too broad to operationalize

## Outputs
- weekly review note
- staged memory updates
- staged skill/config patches
- optional ChatGPT research ticket
- run log row

## Must Not
- store raw tender or supplier tables in memory
- silently patch pricing/compliance rules
- treat strategy output as approval
