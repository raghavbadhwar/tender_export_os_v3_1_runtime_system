# Tender Export OS Worker Plugin Loading

**Status:** Implemented 2026-07-02.
**Policy file:** `config/worker_plugin_policy.yaml`
**Importer:** `scripts/import_external_worker_skills.py`
**Validator:** `scripts/validate_worker_plugin_imports.py`

## What was implemented

Tender Export OS now loads external plugin/capability payloads into Hermes worker profiles as **profile-local skills**, not as one giant shared plugin dump.

The import uses two local capability libraries:

- Accio skills: `/Volumes/RAGHAV2/aios the final/accio_skills`
- Claude plugin skill payloads: `/Volumes/RAGHAV2/aios the final/claude-plugin-files`

Imported skills are written under each worker profile at:

```text
~/.hermes/profiles/<worker>/skills/tender-export-os/plugin-imports/<skill-name>/SKILL.md
```

Every imported skill gets:

- a TEOS-specific skill name, e.g. `teos-accio-product-supplier-sourcing`
- provenance fields showing source kind/path/original name
- a Tender Export OS safety overlay
- `teos_external_actions_allowed: false`

## What was not enabled

This pass did **not** enable runtime Hermes-native plugins or MCP servers.

That is deliberate. Runtime plugins can require credentials or create external side effects. They remain candidate capabilities only until separately approved.

Not enabled in this pass:

- messaging send plugins
- portal/upload/submission plugins
- payment/order/DSC plugins
- credential-heavy browser/search providers
- MCP runtime servers

## Worker-specific loading model

### `hermes-chief-operator`

Loaded COO/program-management/briefing skills:

- Accio: skill creation/vetting, self-improvement, office docs, research, internal comms
- Claude: operations status/risk/runbook, enterprise digest/synthesis

### `gov-tender-radar`

Loaded GOV tender discovery and triage skills:

- Accio: company/org research, market insight, competitor/deep-read, fast-kill viability, PDF/DOCX/XLSX
- Claude: enterprise search strategy/synthesis, risk assessment, data validation

### `export-rfq-radar`

Loaded export buyer/RFQ discovery skills:

- Accio: company/org research, market insight, competitor/deep-read, fast-kill viability, PDF/DOCX/XLSX
- Claude: sales account research, enterprise search/synthesis, data validation

### `supplier-sourcing`

Loaded supplier 5-3-2 and supplier verification skills:

- Accio: product supplier sourcing, supplier performance, company research, 1688 sourcing, AliExpress supplier evaluation
- Claude: vendor review, account research, enterprise search, data validation

### `pricing-compliance`

Loaded pricing waterfall and compliance-draft skills:

- Accio: margin, tariff, international shipping/customs, tax/VAT, B2B payment terms, budget forecast, spreadsheet work
- Claude: price check, margin analyzer, finance variance analysis, compliance tracking, legal/regulatory gap surfacing

### `codex-artifact-factory`

Loaded artifact and runtime production skills:

- Accio: PDF, DOCX, XLSX, PPTX, invoice generator, skill creation/vetting
- Claude: data exploration/visualization/validation, product spec writing, Claude automation recommendation

### `sales-followup`

Loaded draft-only sales/follow-up skills:

- Accio: Gmail assistant, sales negotiator, email automation, lifecycle marketing, copywriting, supplier performance
- Claude: draft outreach, call summary, pipeline review, lead triage, status report

Important: these are draft/support skills only. External sending remains approval-gated.

### `source-health`

Loaded source reliability and trust-scoring skills:

- Accio: supplier performance, company research, review analysis/summarization, competitive landscape
- Claude: source management, search strategy, knowledge synthesis, data validation, risk assessment

### `learning-review`

Loaded continuous improvement skills:

- Accio: self-improvement, skill creator, skill vetter, review analyst
- Claude: process optimization, process documentation, runbook, data validation

### `chatgpt-boardroom-handoff`

Loaded strategic handoff and executive memo skills:

- Accio: PPTX, DOCX, XLSX, internal comms, company research
- Claude: enterprise search/synthesis, competitive brief, status report

## Commands

Dry-run imports:

```bash
python3 scripts/import_external_worker_skills.py --dry-run --json --report
```

Apply imports:

```bash
python3 scripts/import_external_worker_skills.py --write --json
```

Validate imports:

```bash
python3 scripts/validate_worker_plugin_imports.py
```

Check idempotence:

```bash
python3 scripts/import_external_worker_skills.py --dry-run --json
```

Expected after successful import:

```json
"status_counts": {"unchanged": 109}
```

## Safety rule

Imported plugin skills are internal capability aids. They do not override TEOS approval policy.

If any imported plugin/skill suggests sending, posting, uploading, bidding, using DSC, paying, placing an order, or committing final price/origin/classification/delivery/payment terms, the worker must stop and create an approval card or draft.
