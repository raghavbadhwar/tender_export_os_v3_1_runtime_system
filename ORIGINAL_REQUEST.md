# Original User Request

## Initial Request — 2026-07-06T03:14:13+05:30

Maturing and hardening the Tender Export OS v4.1 runtime system by addressing architectural weaknesses, implementing selector fallbacks, improving state synchronization, expanding source scanning capabilities, and maximizing Hermes control-plane automation.

Working directory: /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system
Integrity mode: development

## Requirements

### R1. State Synchronization and Drift Prevention
Automate state synchronization and conflict reconciliation across local registers (CSVs), Google Drive projections, and the Hermes Kanban board, ensuring `data/events.jsonl` remains the canonical source of truth.

### R2. Source Adapter Resiliency and Fallback
Implement page-text keyword extraction and regex parsing fallbacks in `scripts/source_adapters/gem_adapter.py` and `scripts/source_adapters/cppp_adapter.py` to handle scenarios where the default CSS selectors fail due to external portal changes.

### R3. Automated Health Verification
Extend the verification framework to validate fallback pathways and sync reconciliation rules under mock conditions.

### R4. Extended Opportunity Radar (Gov, Commercial, and Export)
Implement and scale source adapters for UNGM (multilateral/export), India Business Portal, and Indian Trade Portal (commercial/B2B export) to crawl and parse opportunities. Target unnoticed or low-competition leads using specialized keywords (e.g., retender, corrigendum, niche B2B categories, and maintenance contracts).

### R5. Hermes Control Plane Maximization & Mobile Gateways
Harness the full potential of Hermes's native capabilities by automating:
1. Mobile push notifications: Configure webhook notification setups using `scripts/render_mobile_approval_payload.py` and `scripts/check_cron_gateway_reliability.py`.
2. Learning Loops: Build a CLI helper for Hermes to ingest qualitative Obsidian-style logs and generate structured memory updates for the rules files (`AGENTS.md` and category configs).

## Acceptance Criteria

### State Synchronization
- [ ] `scripts/reconcile_hermes_kanban.py` runs and resolves drifts between the local register and Kanban state projections without data loss.

### Adapter Fallback
- [ ] GeM and CPPP adapters fallback to text-based extraction when DOM selectors fail, successfully capturing key fields (Tender ID, Buyer, and Deadline) from static text fixtures.

### Opportunity Radar (Gov, Commercial, Export)
- [ ] UNGM and India Business Portal adapters successfully search and parse multilateral, commercial, and export leads from their respective HTML fixtures.
- [ ] Export and B2B keywords are integrated into the Low-Competition Radar rules configuration.

### Hermes Control Plane
- [ ] Hook the mobile approval renderer scripts into a test webhook endpoints and confirm payload structures parse correctly.
- [ ] Run the learning loop generator and verify it outputs valid, structured `staged_memory` entries into `data/events.jsonl`.

### Health & Validation
- [ ] `scripts/system_health_check.py --runtime` runs successfully and reports 0 failures.
- [ ] Core unit test suite under `tests/` executes and passes via pytest.
