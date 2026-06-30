# Architecture Critique and v4.1 Implementation

## Executive Verdict

Tender Export OS v4 is a strong one-founder operating architecture. The control split is correct:

- Hermes is the owner-facing control plane.
- Codex is the file, plugin, parser, and artifact runtime.
- ChatGPT Project is the deep research boardroom.
- Google Drive is the shared knowledge bus.
- Paperclip stays out unless Hermes Kanban proves insufficient.

The architecture is viable for semi-autonomous daily use after the current hardening pass. The biggest risk was state drift: CSV registers, Drive copies, Kanban cards, approval receipts, and generated artifacts could diverge unless one canonical event/state layer controlled all projections. v4.1 now implements that state-hardening layer through `data/events.jsonl`, schema validation, projection rebuilds, owner-decision receipts, readiness gates, artifact manifests, source-adapter fixtures, and plan-only Hermes Kanban reconciliation.

## What Works Well

1. The approval boundary is explicit.
   External sends, DSC use, final quote submission, HSN/ITC-HS confirmation, origin claims, payments, delivery promises, and supplier commitments are all approval-gated.

2. `case_id` is the right system key.
   Every tender, RFQ, quote, approval card, report, and receipt can be joined around one stable identifier.

3. The workflow stages are operationally realistic.
   `Find -> Fast Kill -> Deep Read -> Supplier Proof -> Pricing Proof -> Approval -> Execution -> Receipt` is the right order. It avoids wasting effort on weak leads while still preserving compliance and proof gates before owner action.

4. The Hermes/Codex split is pragmatic.
   Hermes should coordinate owner rhythm, approvals, Kanban, memory, and reminders. Codex should do heavy file work, document generation, parser repair, spreadsheet edits, and runtime testing.

5. The non-fabrication rules are correctly broad.
   The architecture prevents the common failure mode in tender/export automation: inventing eligibility, supplier proof, certifications, classification, origin, or pricing.

## Breakpoints Found and Fixed

| Area | Problem | Fix Applied |
|---|---|---|
| Daily brief delivery | `generate_daily_brief.py` tried to send via Telegram by default | Added local-only default plus explicit `--send-gateway` and `--gateway` flags |
| Status updates | `update_master_case.py` notified Telegram by default | Added explicit `--notify`; default is now local register update only |
| Autopilot loop | Daily autopilot sent gateway notifications by default | Added local-only default and explicit gateway flags |
| Daily brief template | Template contained static sample approval/case data | Replaced with dynamic placeholders and generator-rendered sections |
| Approval card template | Template contained static missing-item text and stale footer | Replaced with dynamic missing-info rendering and v4 footer |
| Today stats | Brief compared `YYYYMMDD` input against ISO `created_at` dates | Added date normalization |
| HTML output | Case and approval data were not escaped | Added HTML escaping |
| Approval rendering | Generator expected fields not present in the approval CSV schema | Added schema-compatible action and amount lookup |
| Export value display | Export cases could prefer INR over USD | Made export outputs prefer USD where available |
| Status flow | v4 `ARTIFACT_PRODUCTION` was missing from transition rules | Added valid transitions through artifact production and approval |
| Missing approval cards | Pending approvals pointed to files that did not exist | Added `generate_approval_cards.py` and generated current cards |
| CSV integrity | `quote_master.csv` header and row shapes did not match | Added missing header fields and repaired malformed row alignment |
| Approval integrity | Pending approval carried `approved_by` / `approved_at` values | Cleared decision fields while status remains `PENDING` |
| Cross-register integrity | Approvals and quotes referenced `EXP-20260630-002`, missing from master cases | Restored a conservative master case row from local registers with explicit evidence gaps |
| Runtime verification | No single command checked system health end to end | Added `scripts/system_health_check.py` |

## Current Test Status

The current system passes the new health check:

```bash
python3 scripts/system_health_check.py --runtime
```

Result:

```text
Tender Export OS v4 System Health
Passes: 16
PASS: All required v4 files exist
PASS: JSON files parse
PASS: YAML files parse with Ruby: 14
PASS: CSV rows match their headers
PASS: All master case statuses are valid v4 statuses
PASS: Approval rows reference known cases
PASS: Quote rows reference known cases
PASS: Quote rows reference known suppliers
PASS: Pending approval cards exist
PASS: Pending approvals do not contain approval decision fields
PASS: Templates do not contain known stale sample data
PASS: Daily brief template has dynamic v4 placeholders
PASS: Python compile and loop validators pass
PASS: Safe dry-run commands pass
PASS: Generated brief and approval cards have no unreplaced placeholders
PASS: Hermes/Codex runtime readiness passes
```

The safe dry-run checks include:

- case ID generation
- supplier scoring
- ChatGPT snapshot generation
- Drive sync manifest dry run
- Drive import plan dry run
- daily brief generation
- Codex task runner
- Python compilation
- loop contract validation
- runtime readiness validation

## Remaining Architecture Risks

1. Multiple state stores can still drift.
   `data/*.csv`, generated HTML, Hermes Kanban, Google Drive, and receipts are related but not yet controlled by one append-only event ledger.

2. The agents are mostly instruction contracts, not executable adapters.
   This is acceptable for v4, but v4.1 should add actual adapter interfaces and fixtures for Radar, Deep Read, Supplier Engine, Pricing, Approval, and Execution Tracker.

3. Approval decisions need a dedicated processor.
   Approval cards exist, but there should be one script that records `Approve`, `Reject`, or `Ask Changes`, validates the current status, updates the case, writes a receipt, and never performs external action unless the approved action explicitly allows it.

4. Quote-proof enforcement is not centralized.
   The 5-3-2 rule and two-quote pricing gate exist in policy, but v4.1 should enforce them through a readiness validator before `PRICING_READY` or `APPROVAL_REQUIRED`.

5. Drive and Kanban are projection targets, not canonical state.
   That is good, but the code should make it impossible for a stale Drive copy or Kanban card to overwrite the local case register without reconciliation.

6. Source adapters need formal contracts.
   The architecture says Radar should scan sources, but each source type needs a safe adapter contract: no login bypass, no CAPTCHA bypass, no paywall scraping, cite links, dedupe by source reference, and return structured opportunities.

7. Compliance output must stay draft-only.
   HSN/ITC-HS, export policy, SCOMET, origin, certificates, and destination requirements should remain candidate/draft outputs until expert/human approval is recorded.

## v4.1 Upgrade Implemented

### Phase 1 - State Hardening

Implemented an append-only event ledger:

```text
data/events.jsonl
```

Every meaningful change should be represented as an event:

- `case.created`
- `case.status_changed`
- `source.scanned`
- `source.blocked`
- `supplier.candidate_added`
- `quote.proof_received`
- `approval.card_created`
- `approval.owner_decision_recorded`
- `artifact.generated`
- `receipt.created`

CSV registers, Kanban updates, Drive manifests, and daily briefs now have a canonical ledger to cite or project from. CSV files remain operational projections, not the root of truth.

### Phase 2 - Schema Enforcement

Implemented machine-readable schemas:

```text
config/schemas/master_cases.schema.json
config/schemas/approvals_receipts.schema.json
config/schemas/quote_master.schema.json
config/schemas/supplier_master.schema.json
config/schemas/event.schema.json
```

`scripts/system_health_check.py` now calls schema validation and runs v4.1 dry-run commands.

### Phase 3 - Approval Decision Processor

Implemented:

```text
scripts/process_owner_decision.py
```

Behavior:

- accepts `case_id` or `approval_id` plus a decision
- validates pending approval state and card existence
- validates approval card exists
- writes an owner-decision receipt
- updates approval status and case status
- never sends, submits, uploads, pays, or commits anything by itself

### Phase 4 - Readiness Gates

Implemented:

```text
scripts/validate_case_readiness.py
```

It answers whether a case is allowed to move to the next stage:

- `DEEP_READ` requires readable source documents or explicit manual-upload blocker
- `SUPPLIER_SEARCH` requires product spec, quantity, and delivery location/destination
- `PRICING_READY` requires at least two quote proofs
- quote-request sending requires owner approval
- export quote pack requires draft compliance notes
- final export send requires owner approval and unresolved compliance gaps list

### Phase 5 - Artifact Manifests

Every case can now have:

```text
outputs/case_reports/<case_id>/artifact_manifest.json
```

The manifest lists generated reports, source documents, supplier proofs, pricing sheets, approval cards, receipts, and open gates. This gives Hermes, Codex, and Drive one shared artifact map.

### Phase 6 - Source Adapter Framework

Implemented a source adapter interface and fixture-backed mock adapter:

```text
scripts/source_adapters/base.py
scripts/source_adapters/mock_adapter.py
scripts/source_adapters/gov_portal_adapter.py
scripts/source_adapters/export_rfq_adapter.py
tests/fixtures/sources/
```

Each adapter returns structured opportunities with source links and blocker status. No adapter should bypass login, CAPTCHA, paywalls, or restricted access.

### Phase 7 - Hermes/Kanban Reconciliation

Implemented a reconciliation planner:

```text
scripts/reconcile_hermes_kanban.py
```

It compares local canonical state against an optional Hermes Kanban snapshot and produces a plan before writing anything. Kanban should mirror the register, not override it silently.

## Recommended Next Build Order

1. Use `python3 scripts/system_health_check.py --runtime` as the acceptance gate.
2. Review `outputs/system_health/projections/` before any projection write-back.
3. Use `scripts/process_owner_decision.py` for approvals, rejects, and ask-changes decisions.
4. Build real source adapters only after extending the fixture-backed adapter tests.
5. Keep Hermes Kanban writes plan-only until connector auth and conflict handling are explicit.

This order matters because it hardens the source of truth first. Once state and approval decisions are reliable, live scanning and external connector work become much safer.

## Sources Used

- `AGENTS.md`
- `README.md`
- `manifest.json`
- `docs/FINAL_ARCHITECTURE.md`
- `config/agent_loops.json`
- `config/loop_schedule.json`
- `data/master_cases.csv`
- `data/approvals_receipts.csv`
- `data/quote_master.csv`
- `data/supplier_master.csv`
- `templates/daily_brief.html`
- `templates/approval_card.html`
- `scripts/generate_daily_brief.py`
- `scripts/update_master_case.py`
- `scripts/run_daily_autopilot_pseudocode.py`
- `scripts/generate_approval_cards.py`
- `scripts/system_health_check.py`
- Local verification command: `python3 scripts/system_health_check.py --runtime`
