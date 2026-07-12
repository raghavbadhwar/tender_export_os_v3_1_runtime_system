# plan.md — Project Orchestrator Plan

## Overview
This plan defines the approach to maturate and harden the Tender Export OS v4.1 runtime system by implementing requirements R1 through R5.

## Methodology: Project Pattern
1. **Parallel Tracks**:
   - **E2E Testing Track**: Build and extend tests for R1-R5 to establish independent validation before/during implementation.
   - **Implementation Track**: Fix/maturate the python scripts and adapters to pass the tests.
2. **Sequential Milestones**:
   - **Milestone 1**: State Sync and Drift Prevention (`reconcile_hermes_kanban.py`).
   - **Milestone 2**: Adapter Fallback (`gem_adapter.py`, `cppp_adapter.py`).
   - **Milestone 3**: Automated Health Verification (add mock verification tests).
   - **Milestone 4**: Extended Opportunity Radar (`ungm_adapter.py`, `india_business_portal_adapter.py`, and low-competition keywords).
   - **Milestone 5**: Hermes Control Plane (mobile webhook setups and Obsidian learning loop).
3. **Validation & Integrity Verification**:
   - Every implementation milestone will be checked by a worker, reviewed by a reviewer, and audited by a Forensic Auditor (`teamwork_preview_auditor`).
   - A final regression test will run `scripts/system_health_check.py --runtime` and all pytest tests.

## Planned Timeline & Actions
- **Action 1**: Initialize Project metadata (`plan.md`, `progress.md`, `BRIEFING.md`).
- **Action 2**: Create `PROJECT.md` defining architecture, milestones, code layout, and interfaces.
- **Action 3**: Dispatch Explorer to analyze all requirements in detail and provide technical context.
- **Action 4**: Dispatch E2E testing track to set up test infra and mock data fixtures.
- **Action 5**: Dispatch Implementation milestones sequentially or in parallel depending on dependencies.
- **Action 6**: Verify all work using Forensic Auditor and pytest.
