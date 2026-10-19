# Hermes Kanban Board

## Board
Slug: `tender-export-os`

Name: `Tender Export OS`

Purpose: Durable operating board for government tender, export RFQ, supplier sourcing, pricing, compliance, document production, approvals, execution tracking, source health, plugin health, and weekly learning.

## Statuses
- `triage`
- `todo`
- `ready`
- `running`
- `blocked`
- `done`
- `archived`

## Worker Profiles
| Profile | Role |
|---|---|
| `tender-export-os` | Owner-facing chief console, approvals, Codex artifact routing, and final readiness review |
| `teos-orchestrator` | Routing-only decomposition into typed specialist tasks |
| `gov-tender-intelligence` | GOV discovery, fast-kill critique, deep read, source health, corrigenda, and repeat-buyer intelligence |
| `export-buyer-intelligence` | Market research, buyer verification, RFQ proof, and demand hypotheses |
| `supplier-commercial` | Supplier 5-3-2, candidate verification, and strict quote-proof readiness |
| `pricing-risk` | Cost waterfall, working capital, L1 sensitivity, margin, and scenarios |
| `compliance-due-diligence` | Draft-only eligibility, DGFT/SCOMET, candidate classification, origin, and compliance gaps |
| `relationship-ops` | Approved communication packets, reply classification, opt-outs, and follow-up timing; no send authority |
| `learning-evaluation` | Outcomes, source/supplier performance, forecast evaluation, and governed learning proposals |

Only `teos-orchestrator` may decompose top-level tasks. Only `tender-export-os`
owns owner-facing approval cards. Legacy specialist command names are 30-day
compatibility wrappers and are invalid Kanban assignees.

## Task Templates
- GOV Tender Intake
- GOV Deep Read
- Export RFQ Intake
- Export Buyer Verification
- Supplier Sourcing
- Pricing Proof
- Compliance Review
- Artifact Production
- Approval Required
- Execution Tracking
- Weekly Review
- Source Health Issue
- Plugin Health Issue
- ChatGPT Research Request

## Required Task Fields
Every task must include:
- `case_id`
- `workflow_type`
- `source`
- `status`
- `assignee`
- `next_action`
- `deadline`
- `owner_approval_needed`
- `drive_artifact_links`
- `comments_or_handoff_notes`

## Setup
Use:

```bash
bash scripts/setup_hermes_kanban_board.sh
```

The script prints the intended Hermes commands and writes a local setup receipt. It does not fabricate success if Hermes CLI syntax differs.

## Source Notes
- Local `hermes --help` confirmed `kanban` support on 2026-06-30.
- Hermes Agent documentation: https://hermes-agent.nousresearch.com/docs/
