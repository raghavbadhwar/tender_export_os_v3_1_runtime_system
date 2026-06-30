# Tender Export OS v4.1.2 Phasewise Implementation Plan

Source of truth: `/Users/raghav/Downloads/Tender_Export_OS_v4_1_2_Phasewise_Development_Mandate.md`.

Baseline findings before implementation:
- `python3 scripts/validate_agent_loops.py` passes with 9 loops.
- `python3 scripts/validate_loop_schedule.py` passes with 4 schedules and 18 entries.
- `python3 scripts/validate_register_schemas.py` currently fails because `data/events.jsonl` contains newer source-adapter and pricing events that are missing from `config/schemas/event.schema.json`.
- `pytest` is declared in `requirements.txt`, but is not installed in the active Python environment.
- Working tree started with pre-existing changes: modified `data/agent_run_log.csv` and untracked `outputs/daily_briefs/intraday_monitor_20260630233339.md`.

## Phase Plan

| Phase | Files to modify | Files to create | Tests to add/update | Commands and expected output | Risks and rollback |
|---|---|---|---|---|---|
| 0. Public/private split | `.gitignore`, `scripts/system_health_check.py` | `scripts/check_no_private_runtime_data.py`, `config/public_scan_allowlist.yaml`, `data/examples/*`, `outputs/examples/*`, `receipts/examples/*` | `tests/test_no_private_data_committed.py` | private scan and public health pass without requiring live data | Risk: live operational files already exist. Rollback: revert `.gitignore` and scanner changes only; do not delete live files. |
| 1. Schema and state contracts | `config/schemas/*.schema.json`, live CSV headers as projections | `config/schemas/event_types.yaml`, `scripts/validate_event_type_registry.py`, `scripts/lib/idempotency.py` | schema, registry, idempotency tests | register schemas and registry validators pass | Risk: projection headers drift. Rollback: restore schema JSON and CSV headers from backup/git. |
| 2. ChatGPT return contract | `scripts/stage_chatgpt_return.py` | `config/schemas/chatgpt_return_schema.md`, `scripts/validate_chatgpt_return.py`, fixtures | staging validation tests | good fixture accepted, bad fixtures rejected | Risk: overly strict validator blocks useful advisory text. Rollback: relax validator checks, not staging safety. |
| 3. Portal access reality | `agents/radar_agent.md`, source configs if compatible | `config/portal_access_reality.yaml`, `scripts/recommend_source_weights.py` | source recommendation dry-run test | dry-run writes recommendation artifact only | Risk: source-weight advice mistaken for config mutation. Rollback: keep recommendations output-only. |
| 4. Source adapter hardening | GeM, CPPP, UNGM adapters and selectors | `scripts/source_runtime/portal_adapter_base.py`, `scripts/source_runtime/selector_extractor.py` | GeM, CPPP, UNGM selector fixture tests | safe adapter harness passes or returns structured blockers | Risk: live portals change. Rollback: selector configs can be updated without architecture change. |
| 5. Browser/download/evidence safety | browser manager, downloader, evidence store, runtime config | blocker and forbidden-action guard modules | blocker, guard, download mock, evidence privacy tests | browser safety tests pass | Risk: false-positive blockers. Rollback: tune blocker patterns while keeping forbidden actions blocked. |
| 6. Parser and field evidence | parser and field extractor dataclasses | `scripts/source_runtime/table_classifier.py` | PDF/table, field evidence, unreadable document tests | critical fields carry evidence or blocker status | Risk: optional PDF libs absent. Rollback: parser returns structured parse failure. |
| 7. Case creation/dedupe/IST | case creation, dedupe | none unless helper needed | config threshold, IST date, dedupe tests | low confidence/expired/duplicates route to intelligence, not cases | Risk: existing UTC case IDs. Rollback: keep old IDs, use IST only going forward. |
| 8. Trader fast kill | kill rules, scoring, Fast Kill doc | none | trader kill-rule test | fixture case scores/watchlists correctly | Risk: rejecting on missing evidence. Rollback: missing evidence stays WATCHLIST. |
| 9. Compliance by category | compliance agent doc | `config/compliance_by_category.yaml` | compliance config test | categories validate with draft-only warnings | Risk: fake compliance certainty. Rollback: preserve draft-only warnings. |
| 10. Pricing realism | pricing agent doc | `scripts/gov_tender_pricing_model.py`, `scripts/export_landed_cost_calculator.py`, `config/pricing_assumptions.yaml` | pricing, L1, export landed-cost tests | working-capital, EMD, L1 outputs calculated | Risk: numbers look final. Rollback: label outputs internal draft until approval. |
| 11. Corrigenda | Deep Read, Execution Tracker, brief docs/schema | `scripts/check_corrigenda.py` | corrigenda test | change detection emits safe event payloads | Risk: false change hash. Rollback: review-only status until confirmed. |
| 12. Supplier pipeline | supplier matcher/schema | supplier source adapter package | supplier quote-proof and GeM gate tests | listing prices marked indicative, not quote proof | Risk: marketplace listing treated as quote. Rollback: hard gate selected pricing. |
| 13. Buyer/export intelligence | buyer schema/verification flow | buyer risk, policy, incoterms scripts and shipment profiles | buyer and shipment profile tests | marketplace-only buyers cannot be ready | Risk: weak leads promoted. Rollback: require explicit RFQ evidence. |
| 14. Past award intelligence | master schema support | `scripts/past_award_intelligence.py` | past-award test | recurrence metrics generated from fixture data | Risk: incomplete public data. Rollback: mark unknown, not confident. |
| 15. Compliance matrix | Pack Builder doc | matrix docs/templates | matrix template test | required columns present | Risk: XLSX generation dependency. Rollback: markdown template remains canonical fallback. |
| 16. Approval timeout/lifecycle | approval policy, schemas, Approval/Execution docs | none unless helper needed | timeout and lifecycle tests | no auto-approval, sub-status enums validate | Risk: timeout misread as rejection. Rollback: timeout only notifies/watchlists. |
| 17. Owner brief metrics | daily brief script and agent doc | none | owner-brief metrics test | `--dry-run` works and 30-day metrics calculate | Risk: brief overwrites live report. Rollback: use dry-run/no-log for validation. |
| 18. Drive setup/locking | Drive setup naming where needed | `scripts/setup_drive_folders.py`, `scripts/lib/drive_writer.py`, `scripts/lib/shared_brain_write_lock.py` | Drive lock test | dry-run only, no Drive writes | Risk: concurrent lock leftovers. Rollback: timeout event and manual cleanup path. |
| 19. Errors/CI/regression | key scripts import shared error handling where scoped | `scripts/lib/pipeline_error.py`, `scripts/run_full_safe_regression.py`, `.github/workflows/ci.yml` | runner/CI structural checks | full safe regression passes or reports blockers | Risk: CI depends on optional live runtime. Rollback: public-template safe path only. |
| 20. Dependency reproducibility | requirements docs | `requirements.lock.txt` if needed | covered by regression | install and regression commands documented | Risk: local Python lacks packages. Rollback: use local venv and documented install. |
| 21. Edge-case matrix | parser/source/browser tests | edge-case fixtures as needed | edge-case tests | every edge case returns result, blocker, watchlist, or reject | Risk: fixture overbreadth. Rollback: keep tests deterministic and internal-only. |

## Final Validation Commands

Required final commands:

```bash
python3 scripts/check_no_private_runtime_data.py --public-template
python3 scripts/system_health_check.py --public-template
python3 scripts/validate_register_schemas.py
python3 scripts/validate_event_type_registry.py
python3 scripts/validate_chatgpt_return.py --input tests/fixtures/chatgpt_returns/good_return.md
python3 scripts/test_source_adapters.py --safe --limit 5
python3 scripts/setup_drive_folders.py --dry-run
python3 scripts/run_full_safe_regression.py
pytest
```

Optional private-runtime checks:

```bash
python3 scripts/system_health_check.py --private-runtime
python3 scripts/sync_to_drive.py --mode private-runtime --dry-run
```

Safety rule for all phases: internal scan/read/download/parse/draft/report may proceed; send/submit/pay/sign/upload/commit/certify remains approval-gated or owner-manual.
