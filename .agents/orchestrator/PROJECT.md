# Project: Tender Export OS v4.1 Maturation & Hardening

## Architecture
- **Control Plane**: Hermes Chief Operator, Kanban board mapping.
- **State Registry**: CSV master registers (`data/master_cases.csv`, `data/approvals_receipts.csv`, etc.) and `data/events.jsonl` canonical ledger.
- **Source Adapters**:
  - Gov: `gem_adapter.py`, `cppp_adapter.py`
  - Multilateral/Export: `ungm_adapter.py`
  - Commercial/B2B Export: `india_business_portal_adapter.py`, `indian_trade_portal_adapter.py`
- **Verification Framework**: `scripts/system_health_check.py` and pytest test suite.
- **Mobile Gateway**: `render_mobile_approval_payload.py`, `check_cron_gateway_reliability.py`.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Baseline Assessment | Explore codebase, execute initial tests, identify failures | None | DONE |
| 2 | R1 State Sync | Mature `reconcile_hermes_kanban.py` & reconcile CSV/Kanban/events | M1 | DONE |
| 3 | R2 Adapter Fallback | Page-text extraction and regex fallbacks for GeM and CPPP | M1 | DONE |
| 4 | R3 Verification | Add tests for fallback pathways and sync reconciliation rules | M2, M3 | DONE |
| 5 | R4 Radar Expansion | UNGM/IBP/ITP crawl/parse & low-competition config integration | M1 | DONE |
| 6 | R5 Hermes Maximization| Mobile webhook Renderer configurations & Obsidian learning CLI helper | M1 | DONE |
| 7 | Final E2E Health Check | Validate entire system and test suite (all green) | M2-M6 | DONE |

## Interface Contracts
### `reconcile_hermes_kanban` ↔ Event Ledger
- `reconcile_hermes_kanban.py` reads `data/master_cases.csv` and kanban board snapshot.
- Appends `kanban.reconciliation_planned` event to `data/events.jsonl`.
- Output: `outputs/system_health/hermes_kanban_reconciliation_plan.json`.

### Source Adapters ↔ Radar / System
- Output: Opportunity dictionaries containing `case_id` (or target fields like `Tender ID`, `Buyer`, `Deadline`).
- Static page-text fallback triggered when DOM parsing fails to find selectors.
