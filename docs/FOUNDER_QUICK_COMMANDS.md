# Founder Quick Commands — Tender Export OS v4.1

These commands define the mobile/desktop command palette for the founder. They are intentionally approval-aware: commands may create internal drafts, cards, receipts, tasks, and briefs, but they must not send, submit, pay, use DSC, confirm classification/origin, or commit commercial terms without an approval card and explicit owner decision.

## Daily control

- `show today brief` — render current owner brief from registers, event ledger, Kanban, source health, plugin health, and approvals.
- `show approvals` — list pending approval cards with case IDs and risks.
- `show deadlines` — list active cases by deadline and next action.
- `show kanban` — summarize the Tender Export OS Kanban board.
- `show source health` — summarize source status and degraded/broken sources.
- `show plugin health` — summarize Hermes/Codex/plugin readiness.

## Case control

- `show case <case_id>` — produce a case dossier with evidence, suppliers, pricing/compliance status, approvals, artifacts, and blockers.
- `create case workspace <case_id>` — create `cases/<case_id>/` folders, `HERMES.md`, evidence metadata, and event ledger entry.
- `create task graph <case_id>` — create the Kanban task graph for GOV or EXPORT case execution.
- `capture evidence <case_id>` — create or refresh the evidence bundle and hashes.
- `prepare quote pack <case_id>` — route artifact production internally; final send still requires approval.
- `prepare bid pack <case_id>` — route artifact production internally; final submission/upload/DSC still requires approval.

## Approval control

- `approve case <case_id>` — record owner approval for the pending card and create receipt; only then may the execution tracker proceed.
- `reject case <case_id>` — record owner rejection and route case to safe status.
- `ask changes <case_id>: <changes>` — record change request and route back to the relevant specialist.

## Learning and strategy

- `stage memory update` — propose compact durable memory updates for owner approval.
- `run weekly review` — review outcomes, source quality, supplier quality, owner corrections, and propose SOP/config/skill changes.
- `send to ChatGPT research <topic>` — create a bounded ChatGPT boardroom packet through the Google Drive bridge.

## Safety reminder

If a command touches external communications, money, DSC, final price, delivery, payment terms, origin, HSN/ITC-HS, purchase orders, permanent blacklisting, or public service exposure, Hermes must stop and show an approval card.
