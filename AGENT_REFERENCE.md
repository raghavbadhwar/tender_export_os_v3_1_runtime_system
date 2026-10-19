# Tender Export OS v4.1 - Agent Quick Reference Card

**Purpose:** One-page lookup for all 11 agents — inputs, outputs, triggers, key configs, and quality gates.

---

## Agent Index

| # | Agent | File | Primary Trigger | Status In | Status Out |
|---|-------|------|-----------------|-----------|------------|
| 0 | **Hermes Chief Operator** | `hermes_chief_operator.md` | Cron + Owner + Kanban | — | — |
| 1 | **Radar Agent** | `radar_agent.md` | Daily 05:30 cron | — | `NEW` |
| 2 | **Fast Kill Agent** | `fast_kill_agent.md` | After Radar (06:00) | `NEW` | `REJECTED` / `WATCHLIST` / `DEEP_READ` |
| 3 | **Deep Read Agent** | `deep_read_agent.md` | On `DEEP_READ` cases | `DEEP_READ` | `SUPPLIER_SEARCH` / `WATCHLIST` / `REJECTED` |
| 4 | **Supplier Engine** | `supplier_engine_agent.md` | On `SUPPLIER_SEARCH` | `SUPPLIER_SEARCH` | `PRICING_READY` / `WATCHLIST` |
| 5 | **Pricing Agent** | `pricing_agent.md` | 2+ quote proofs | `PRICING_READY` | `ARTIFACT_PRODUCTION` |
| 6 | **Compliance Agent** | `compliance_agent.md` | Export after Deep Read | `DEEP_READ` | `ARTIFACT_PRODUCTION` |
| 7 | **Pack Builder** | `pack_builder_agent.md` | After Pricing/Compliance | `ARTIFACT_PRODUCTION` | `APPROVAL_REQUIRED` |
| 8 | **Approval Desk** | `approval_desk_agent.md` | After Pack Builder | `APPROVAL_REQUIRED` | `APPROVED` / `CHANGES_REQUESTED` |
| 9 | **Execution Tracker** | `execution_tracker_agent.md` | Daily 17:00 + 30-min | `APPROVED`+ | `SENT_OR_SUBMITTED` → `WON/LOST` |
| 10 | **Owner Briefing** | `owner_briefing_agent.md` | Daily 08:30 cron | — | — |
| 11 | **Codex Plugin Factory** | `codex_plugin_factory_agent.md` | Hermes routes | — | — |

---

## Agent 0 — Hermes Chief Operator (Control Plane)

| Aspect | Detail |
|--------|--------|
| **Role** | COO + Program Manager + Risk Controller |
| **Runs** | Always-on via cron, owner commands, Kanban events |
| **Key Inputs** | `SOUL.md`, `HERMES.md`, `AGENTS.md`, `config/kanban_board.yaml`, `config/hermes_cron.yaml`, `config/approval_policy.yaml`, `data/master_cases.csv`, `data/approvals_receipts.csv`, `data/agent_run_log.csv`, `data/source_health.csv`, `data/plugin_health.csv` |
| **Outputs** | Owner briefs, approval card requests, Kanban routing, source/plugin health notes, staged memory/skill proposals, ChatGPT research tickets, `agent_run_log.csv` rows |
| **Capability Bundle** | `operations`, `productivity`, `enterprise-search`, `data` + `teos-ops` skill bundle |
| **Quality Gates** | One owner action, blockers surfaced, approval gates intact, Kanban current |
| **Stop Conditions** | Approval gate reached, evidence missing, Codex/plugin unavailable, Drive auth unavailable, owner input required |
| **Key Configs** | `config/kanban_board.yaml`, `config/hermes_cron.yaml`, `config/approval_policy.yaml`, `config/memory_policy.yaml` |

---

## Agent 1 — Radar Agent (Discovery)

| Aspect | Detail |
|--------|--------|
| **Role** | Opportunity Intelligence Analyst |
| **Runs** | Daily 05:30 IST (`core_source_agent_browser_radar` cron) |
| **Key Inputs** | `config/sources.gov.yaml`, `config/sources.export.yaml`, `config/low_competition_keywords.yaml`, `config/research_capture_routing.yaml`, staged Deep Research leads, `data/source_health.csv`, `data/master_cases.csv` |
| **Outputs** | New `master_cases.csv` rows (`status=NEW`), updated `source_health.csv`, `agent_run_log.csv` row |
| **Capability Bundle** | `company-research`, `market-insight-product-selection`, `browser/playwright`, `data` |
| **Quality Gates** | Dedupe by URL/title+buyer+deadline, source health updated, no CAPTCHA bypass, `PUBLIC_LISTING_ONLY` ≠ bid-ready |
| **Stop Conditions** | HTTP error 3× → Broken, duplicate case → skip, CAPTCHA → Manual Check |
| **Key Configs** | `config/sources.gov.yaml`, `config/sources.export.yaml`, `config/kill_rules.yaml` (for reference) |
| **Case ID Format** | `GOV-YYYYMMDD-NNN` or `EXP-YYYYMMDD-NNN` |
| **Evidence Levels** | `PUBLIC_LISTING_ONLY` → `DETAIL_PAGE_READ` → `DOCUMENTS_DISCOVERED` → `DOCUMENTS_DOWNLOADED` → `DEEP_READ_COMPLETE` |

---

## Agent 2 — Fast Kill Agent (Triage)

| Aspect | Detail |
|--------|--------|
| **Role** | Bid/No-Bid Triage Committee |
| **Runs** | After Radar (06:00 `morning_opportunity_intelligence_html`) |
| **Key Inputs** | `master_cases.csv` (`status=NEW`), `config/kill_rules.yaml`, `config/scoring_weights.yaml`, `config/categories.yaml`, `config/low_competition_scoring.yaml`, `scripts/gov_fast_kill.py` |
| **Outputs** | Updated `master_cases.csv` (`status` + `kill_reason` + `score_gov/export`), `no_go_reason_note.txt` in `outputs/case_reports/<case_id>/`, `agent_run_log.csv` row |
| **Capability Bundle** | `market-viability-logic-auditor`, `operations`, `data` |
| **Quality Gates** | Hard reject only with cited evidence; missing/ambiguous = `WATCHLIST`; no-go note includes rule ID, evidence, reconsider condition |
| **GOV Kill Rules** | KILL-01: Deadline ≤5d, KILL-02: Turnover > capacity, KILL-03: Experience missing, KILL-04: OEM auth missing, KILL-05: License missing, KILL-06: EMD > threshold → WATCHLIST, KILL-07: Category inactive, KILL-08: Delivery impossible, KILL-09: Unsafe payment → WATCHLIST, KILL-10: No supplier, KILL-11: Security clearance, KILL-12: Local content unmet → WATCHLIST |
| **EXPORT Kill Rules** | KILL-01: SCOMET → REJECTED, KILL-02: Prohibited, KILL-03: Buyer unverifiable, KILL-04: High-risk destination, KILL-05: Unsafe payment, KILL-06: Margin < threshold, KILL-07: Deadline <3d, KILL-08: No supplier, KILL-09: Restricted policy → WATCHLIST, KILL-10: Complex compliance → WATCHLIST |
| **Scoring Thresholds** | ≥60 → `DEEP_READ`, 45-59 → `WATCHLIST`, <45 → `REJECTED` |
| **Stop Conditions** | Ambiguous data → `WATCHLIST`, SCOMET/Prohibited → immediate `REJECTED` + owner alert |

---

## Agent 3 — Deep Read Agent (Extraction)

| Aspect | Detail |
|--------|--------|
| **Role** | Tender/RFQ Document Analyst |
| **Runs** | On cases with `status=DEEP_READ` (after Fast Kill promotes) |
| **Key Inputs** | Downloaded PDFs/BOQs/corrigenda/RFQs, `master_cases.csv`, `config/scoring_weights.yaml`, `config/kill_rules.yaml`, `data/historical_tender_notices.csv`, `data/historical_awards.csv` |
| **Outputs** | `deep_read_<case_id>.json/.md` in `outputs/case_reports/<case_id>/`, `case.deep_read_recorded` event, recommended status (`SUPPLIER_SEARCH`/`WATCHLIST`/`REJECTED`), `agent_run_log.csv` row |
| **Capability Bundle** | `pdf`, `docx`, `xlsx` + `pdf-viewer`, `pdf-server-mcp`, `pdf-filler-simple`, `ms_office_word` |
| **Quality Gates** | All docs/corrigenda listed, risky clauses quoted verbatim, no eligibility claim without document proof, every fact has doc path + page number |
| **GOV Extraction Fields** | Identity, Eligibility (turnover, experience, MSME, OEM, licenses, local content), Financial (EMD, BG, performance sec), BOQ (items, qty, delivery, inspection, warranty), Payment (advance, milestones, retention), Penalties (late delivery, cap, termination), Compliance docs required |
| **EXPORT Extraction Fields** | Buyer details, product spec, HS code, quantity, packaging, labelling, quality standard, Incoterms, payment terms, delivery deadline, sample req, inspection, destination requirements (SPS/TBT, certifications, COO) |
| **Stop Conditions** | Corrupt/password PDF → flag + manual upload, eligibility clearly not met → `REJECTED`, SCOMET found → immediate `REJECTED` + escalate |
| **Validation** | `scripts/gov_deep_read_contract.py` validates against `config/schemas/gov_deep_read.schema.json` |

---

## Agent 4 — Supplier Engine (Sourcing)

| Aspect | Detail |
|--------|--------|
| **Role** | Strategic Sourcing & Procurement Specialist |
| **Runs** | After Deep Read (`status=SUPPLIER_SEARCH`) |
| **Key Inputs** | `master_cases.csv`, `supplier_master.csv`, `config/sources.supplier.yaml`, `config/categories.yaml`, Deep Read report |
| **Outputs** | New/updated `supplier_master.csv`, `quote_master.csv` (quote requests = `PENDING_APPROVAL`), `supplier_shortlist_<case_id>.md`, `supplier_candidates_<case_id>.json`, status → `PRICING_READY` (when 2+ quotes), `agent_run_log.csv` row |
| **Capability Bundle** | `product-supplier-sourcing`, `supplier-performance-manager`, `company-research`, `1688-sourcing`, `browser`, `data` |
| **Quality Gates** | **5-3-2 Rule**: 5 candidates min, 3 source types min, 2 quote proofs min; blacklist/watchlist + cert checks recorded; marketplace listing ≠ quote proof |
| **GOV Sources** | GeM Seller Directory, IndiaMART, NSIC Portal, local Google Maps |
| **EXPORT Sources** | IndiaMART, APEDA/EPC directory, local clusters, Alibaba (benchmark only) |
| **Scoring Factors** | Identity(10), Product fit(15), Capacity(10), Certificates(10), Quote clarity(8), Response speed(5), Export/tender exp(8), Price competitiveness(10), Payment terms(7), Delivery(7), On-time(5), Defect(3), Communication(2) |
| **Stop Conditions** | <5 candidates after exhaustive → `WATCHLIST` + owner notify, all blacklisted → `REJECTED`, quotes > budget → owner decision |
| **5-3-2 Gate** | `scripts/gov_supplier_532_gate.py` must produce `PASS` with case-scoped manifest |

---

## Agent 5 — Pricing Agent (Cost Waterfall)

| Aspect | Detail |
|--------|--------|
| **Role** | Commercial Finance & Pricing Analyst |
| **Runs** | After 2+ quote proofs received (`status=PRICING_READY`) |
| **Key Inputs** | `quote_master.csv` (≥2 received), `master_cases.csv`, Deep Read report, market freight rates |
| **Outputs** | `pricing_<case_id>.json/.md` in `outputs/case_reports/<case_id>/`, `agent_run_log.csv` row |
| **Capability Bundle** | `profit-margin-analyzer`, `tariff-search`, `international-shipping-customs`, `sales-tax-vat-automator`, `b2b-payment-terms-optimizer`, `xlsx`, `finance`, `data` |
| **Quality Gates** | Complete cost waterfall (no invisible costs), unknown = conservative + flagged, price stays draft until owner approval, `scripts/gov_pricing_contract.py` validates |
| **GOV Waterfall (A→O + P)** | A: Supplier base, B: GST purchase, C: Inward freight, D: Packaging, E: Outbound freight, F: Labour, G: Installation, H: Warranty reserve, I: Inspection, J: Documentation, K: EMD/BG finance, L: Working capital, M: Payment delay buffer, N: Penalty reserve, O: Overhead, P: Target margin |
| **EXPORT Waterfall (A→O + P)** | A: Supplier base, B: GST purchase, C: Inland freight, D: Export packaging, E: CHA/docs, F: Port handling, G: Pre-ship inspection, H: COO/other docs, I: Sample cost, J: Bank charges, K: Currency buffer, L: Working capital, M: Risk buffer, O: Overhead → FOB → +Freight +Insurance = CIF |
| **Stop Conditions** | <2 quote proofs → wait, margin < threshold → flag strongly, FX >5% off live → conservative buffer + flag |
| **Output Formats** | Conservative / Recommended / Aggressive pricing options with confidence level and assumptions list |

---

## Agent 6 — Compliance Agent (Draft-Only)

| Aspect | Detail |
|--------|--------|
| **Role** | Export Compliance Drafter |
| **Runs** | Export cases after Deep Read |
| **Key Inputs** | `master_cases.csv`, Deep Read report, DGFT Export Policy, SCOMET List, Indian Trade Portal |
| **Outputs** | `compliance_draft_<case_id>.md/.json` in `outputs/case_reports/<case_id>/`, `compliance.matrix_drafted` event, `agent_run_log.csv` row |
| **Capability Bundle** | `international-shipping-customs`, `tariff-search`, `regulatory-legal`, `commercial-legal`, `corporate-legal`, `privacy-legal`, `data` |
| **Quality Gates** | **DRAFT ONLY** — HSN/ITC-HS = candidate, origin = candidate, SCOMET suspicion = immediate stop + escalate, DGFT/SCOMET/destination sources cited |
| **Compliance Matrix** | Every clause gets `position`: `COMPLIES` / `DOES_NOT_COMPLY` / `UNKNOWN` / `OWNER/EXPERT_REVIEW` (last two = blockers) |
| **Structure** | 1. HSN/ITC-HS Candidate, 2. Export Policy (Free/Restricted/Prohibited/SCOMET), 3. SCOMET Flag, 4. Destination Requirements, 5. Certificate of Origin, 6. Incoterms Recommendation, 7. IEC/GST/e-RCMC Checklist, 8. Documentation Pack, 9. Freight/Insurance Assumptions, 10. Summary + Owner Flags |
| **Stop Conditions** | SCOMET detected → `REJECTED` + owner alert, Prohibited export → `REJECTED`, ITC-HS undetermined → `WATCHLIST` |
| **Validation** | `scripts/compliance_matrix_contract.py` validates matrix format |

---

## Agent 7 — Pack Builder (Assembly)

| Aspect | Detail |
|--------|--------|
| **Role** | Bid/Proposal Production Manager |
| **Runs** | After Pricing + Compliance (`status=ARTIFACT_PRODUCTION`) |
| **Key Inputs** | `master_cases.csv`, all case reports (deep_read, pricing, supplier, compliance), `templates/` |
| **Outputs** | **GOV:** `outputs/bid_packs/<case_id>/` (9 files) **EXPORT:** `outputs/export_quote_packs/<case_id>/` (8 files), status → `APPROVAL_REQUIRED`, approval card created, `agent_run_log.csv` row |
| **Capability Bundle** | `pdf`, `docx`, `xlsx`, `pptx`, `invoice-generator` + doc/PDF/presentation plugins |
| **GOV Bid Pack (9 files)** | 1. bid_cover, 2. boq_filled, 3. compliance_matrix, 4. eligibility_declaration_draft, 5. supplier_summary, 6. emd_plan, 7. delivery_plan, 8. risk_register, 9. missing_items |
| **EXPORT Quote Pack (8 files)** | 1. quote_cover, 2. proforma_invoice_draft, 3. product_spec_sheet, 4. compliance_summary, 5. supplier_summary, 6. pricing_breakdown (EXW/FOB/CIF), 7. payment_terms_proposal, 8. missing_items |
| **Quality Gates** | Pack includes cover + source list + risk register + missing-items list; every artifact opened/rendered/tested; no pack approval-ready unless gaps resolved OR listed in missing_items |
| **Compliance Matrix** | Every tender clause → row with requirement, position, document, gap status, owner-decision flag (per `docs/COMPLIANCE_MATRIX_FORMAT.md`) |
| **Stop Conditions** | Missing pricing report → wait, critical compliance gap → flag in missing_items, SCOMET/Prohibited → escalate, matrix missing evidence refs → not approval-ready |

---

## Agent 8 — Approval Desk (Decision Interface)

| Aspect | Detail |
|--------|--------|
| **Role** | Executive Decision Designer |
| **Runs** | After Pack Builder creates pack (`status=APPROVAL_REQUIRED`) |
| **Key Inputs** | Bid/Quote pack, `master_cases.csv`, all case reports, `config/approval_policy.yaml` |
| **Outputs** | `receipts/approvals/<case_id>_approval_card.html`, `approvals_receipts.csv` row (`status=PENDING`), Hermes notification, `agent_run_log.csv` row |
| **Capability Bundle** | `sales-negotiator`, `operations`, `legal`, `data` |
| **Required Card Fields (12)** | 1. case_id, 2. workflow_type, 3. proposed_action, 4. business_object, 5. amount_or_price, 6. expected_benefit, 7. concrete_risk, 8. recovery_rollback_path, 9. documents_sources_used, 10. confidence_score (0-100), 11. missing_information, 12. approval_options [Approve/Reject/Ask Changes] |
| **Action Types** | Supplier quote request, buyer RFQ reply, export quotation, submit tender bid (DSC), pay EMD, confirm HSN/origin, commit delivery, accept payment terms |
| **Quality Gates** | Decision in <2 minutes, benefit/risk/recovery/missing explicit, status stays `PENDING` until explicit owner decision receipt |
| **Timeout Policy** | Default 48h → `CHANGES_REQUESTED`; never infer approval from silence |
| **Stop Conditions** | Pack has critical unresolved gaps → no card, SCOMET/Prohibited → escalation note only |

---

## Agent 9 — Execution Tracker (Post-Approval Monitor)

| Aspect | Detail |
|--------|--------|
| **Role** | Operations Follow-Up Controller |
| **Runs** | Daily 17:00 (`supplier_followup_review`) + Buyer Reply Monitor every 30min 09:00-21:59 |
| **Key Inputs** | `master_cases.csv` (approved+), `approvals_receipts.csv`, `quote_master.csv` |
| **Outputs** | Status transitions, receipts in `receipts/submissions/`, `receipts/supplier_quotes/`, `receipts/owner_decisions/`, follow-up flags in `agent_run_log.csv`, daily brief contributions |
| **Capability Bundle** | `supplier-performance-manager`, `gmail-assistant`, `email-automation-flow-builder`, `operations`, `productivity`, `enterprise-search` |
| **Tracks** | Supplier quote response (48h), bid submission ack, bid opening/result, export quote validity (7d/24h alerts), delivery deadline (7d/3d alerts), payment due (3d overdue escalate) |
| **GOV Milestones** | `scripts/record_gov_execution_milestone.py` — SUBMISSION_ACK, TECH_EVAL, FINANCIAL_OPEN, L1, AWARD, WORK_ORDER, DELIVERY, INVOICE, PAYMENT_DUE, PAYMENT_RECEIVED |
| **EXPORT Milestones** | `scripts/record_export_execution_milestone.py` — ORDER_RECEIVED, SAMPLE, PRODUCTION, INSPECTION, PACKING, DISPATCH, CUSTOMS, SHIPMENT, DELIVERY, INVOICE, PAYMENT, CLAIM/RETURN, REPEAT_INQUIRY |
| **Evidence States** | `EVIDENCE_PRESENT` (fact recorded, no status change) → `VERIFIED` (advances execution_sub_status) |
| **Quality Gates** | Receipts evidence-backed, overdue escalated not auto-sent, WON/LOST requires evidence, never re-execute without new approval |
| **Stop Conditions** | Escalation needs external action → flag for owner, never re-submit without new approval |

---

## Agent 10 — Owner Briefing Agent (Intelligence)

| Aspect | Detail |
|--------|--------|
| **Role** | Daily Intelligence Officer |
| **Runs** | Daily 08:30 IST (`morning_operator_brief` cron) |
| **Key Inputs** | `master_cases.csv`, `agent_run_log.csv` (yesterday/today), `approvals_receipts.csv`, `source_health.csv`, `outputs/case_reports/`, `outputs/deep_research_staging/`, `config/scoring_weights.yaml` |
| **Outputs** | `outputs/daily_briefs/brief_YYYYMMDD.html`, `agent_run_log.csv` row |
| **Capability Bundle** | `company-research`, `internal-comms`, `pptx`, `docx`, `xlsx`, `data`, `productivity`, `enterprise-search` |
| **Brief Sections (9)** | 1. New Opportunities (GOV/EXPORT counts), 2. Auto-Rejected (top reasons), 3. Best Opportunities (Top 3 by score), 4. Pending Supplier Proof, 5. Approval Required (with buttons), 6. Risks & Blockers, 7. Low-Competition Radar, 8. Deep Research Intelligence (optional), 9. **ONE Recommended Owner Action** |
| **Quality Gates** | Signal over noise, top approvals/blockers/deadlines, ONE action only, trailing 30-day metrics block |
| **Stop Conditions** | No active cases → "Consider running Radar scan", agent errors → include in Risks |

---

## Agent 11 — Codex Plugin Factory (Artifact Production)

| Aspect | Detail |
|--------|--------|
| **Role** | Artifact/Runtime Production Lead |
| **Runs** | Hermes routes + on-demand for artifact production |
| **Key Inputs** | `config/plugin_routing.yaml`, `data/capability_registry.csv`, `data/plugin_health.csv`, case reports, pricing, compliance, templates |
| **Outputs** | Artifacts under `outputs/`, plugin receipts under `receipts/plugin_runs/`, updated `plugin_health.csv`, `agent_run_log.csv` row |
| **Capability Bundle** | All doc/sheet/pres plugins + `claude-code-setup`, `claude-md-management`, `github`, `context7`, `engineering`, `testing-automation` |
| **Runtime Procedure** | 1. Confirm case_id, 2. Check plugin health/routing, 3. Prefer Codex App-Server Runtime, 4. Fallback bridge only if documented, 5. Produce under `outputs/`, 6. Validate (open/render, case_id present, no unapproved claims), 7. GOV: manifest + missing-items + plugin receipt → `verify-bid-pack` → Approval Desk, 8. EXPORT: draft manifest + commercial-readiness + plugin receipt → `verify-export-quote-pack` → Approval Desk |
| **GOV Bid-Pack Gate** | `codex_task_runner.py --verify-bid-pack --write-receipt` must pass: complete manifest, all mandatory artifacts, missing-items list, plugin receipt, open/render/parse checks |
| **EXPORT Quote-Pack Gate** | `codex_task_runner.py --verify-export-quote-pack --write-receipt` must pass: DRAFT_READY commercial-readiness, 2 strict quote proofs, EXW/FOB/CIF inputs, draft-only classification/origin, plugin receipt |
| **Quality Gates** | Plugin choice recorded, artifact validated, receipt saved, bid-pack/quote-pack verification receipts match current manifest |
| **Stop Conditions** | Runtime unavailable + fallback not approved, plugin unavailable/unauthenticated, artifact would need unapproved claim, source evidence missing |

---

## Quick Config Reference

| Config | Controls |
|--------|----------|
| `approval_policy.yaml` | What requires owner approval (Mode A/B/C) |
| `agent_capability_routing.yaml` | Best-in-class capability bundles per agent |
| `kanban_board.yaml` | Board, statuses, profiles, routing, task templates |
| `hermes_cron.yaml` | 20 scheduled jobs with cadence/runtime/purpose |
| `kill_rules.yaml` | Ordered kill rules for Fast Kill |
| `scoring_weights.yaml` | Scoring factors for all agents |
| `sources.gov.yaml` / `sources.export.yaml` / `sources.supplier.yaml` | Source portals and health |
| `categories.yaml` | Product categories, active flags, SCOMET |
| `plugin_routing.yaml` / `codex_runtime_policy.yaml` | Plugin + Codex runtime rules |
| `memory_policy.yaml` | Memory/skill write approvals |
| `sync_policy.yaml` | Google Drive sync rules |
| `compliance_by_category.yaml` | Category-specific compliance requirements |

---

## Key Scripts by Agent

| Agent | Primary Scripts |
|-------|-----------------|
| Radar | `run_agent_browser_core_sources.py`, `run_source_adapter.py` |
| Fast Kill | `gov_fast_kill.py`, `run_morning_opportunity_intelligence.py` |
| Deep Read | `gov_deep_read_contract.py`, `check_corrigenda.py`, `gov_historical_intelligence.py` |
| Supplier Engine | `gov_supplier_532_gate.py`, `supplier_matcher_from_tender.py` |
| Pricing | `gov_tender_pricing_model.py`, `gov_pricing_contract.py`, `export_landed_cost_calculator.py` |
| Compliance | `compliance_matrix_contract.py`, `compliance_source_policy.py`, `gov_pricing_contract.py` |
| Pack Builder | `codex_bid_pack_contract.py`, `codex_export_quote_pack_contract.py` |
| Approval Desk | `generate_approval_cards.py`, `process_owner_decision.py` |
| Execution Tracker | `generate_intraday_monitor.py`, `generate_buyer_reply_monitor.py`, `record_gov_execution_milestone.py`, `record_export_execution_milestone.py` |
| Owner Briefing | `generate_daily_brief.py`, `generate_operating_desk_report.py` |
| Codex Factory | `hermes_create_codex_task.py`, `codex_task_runner.py`, `check_codex_runtime_readiness.py` |
| Hermes | `teos_job_supervisor.py`, `system_health_check.py`, `reconcile_hermes_kanban.py`, `validate_register_schemas.py` |

---

## Status Flow Quick Reference

```
NEW
  │
  ├─► FAST_KILL ──► REJECTED (hard kill with evidence)
  │
  └─► FAST_KILL ──► WATCHLIST (borderline/missing data)
                        │
                        └─► [Human review / more data] ──► DEEP_READ
                                                              │
                                                              ├─► SUPPLIER_SEARCH ──► PRICING_READY
                                                              │                        │
                                                              │                        ├─► ARTIFACT_PRODUCTION
                                                              │                        │       │
                                                              │                        │       └─► APPROVAL_REQUIRED
                                                              │                        │               │
                                                              │                        │       ├─► APPROVED ──► SENT_OR_SUBMITTED
                                                              │                        │       │                  │
                                                              │                        │       │                  ├─► FOLLOW_UP ──► WON → ARCHIVED
                                                              │                        │       │                  │
                                                              │                        │       │                  └─► FOLLOW_UP ──► LOST → ARCHIVED
                                                              │                        │       │
                                                              │                        │       └─► CHANGES_REQUESTED ──► [loop to relevant stage]
                                                              │                        │
                                                              │                        └─► [Fail 5-3-2/quotes] ──► WATCHLIST
                                                              │
                                                              └─► [Eligibility fail] ──► REJECTED
```

---

## Approval Gate Quick Reference

| Mode | Actions | Approval |
|------|---------|----------|
| **A - Autopilot** | Scan, extract, score, create cases, fast kill, deep read, identify suppliers, draft pricing/compliance, briefs, internal updates, Kanban tasks, artifact drafts | ❌ No |
| **B - Approval-Gated** | Send supplier quote, supplier clarification, supplier follow-up, request price, portal login/signup/creds, send buyer reply, send buyer outreach, send export quote, **submit bid**, upload docs, commit price, commit delivery, accept payment terms, confirm HSN, claim origin, pay EMD, pay deposit, pay advance, place PO, **use DSC**, send invoice, blacklist supplier, patch pricing/compliance skill, enable cred-heavy plugin, expose service | ✅ Yes + Card |
| **C - Execution Tracker** | Track responses, track bid status, track buyer follow-up, track validity, track delivery, track payment, record receipts, update status, internal reminders, update Kanban, sync to Drive | Auto post-approval |

---

*Keep this card handy for quick agent routing and quality gate checks.*