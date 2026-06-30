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
| `hermes-chief-operator` | Overall orchestration, owner briefing, approvals, routing, memory, learning |
| `gov-tender-radar` | Find and fast-kill Indian government/public procurement tenders |
| `export-rfq-radar` | Find export buyer RFQs and foreign/multilateral procurement opportunities |
| `supplier-sourcing` | Apply 5-3-2 supplier sourcing and supplier verification |
| `pricing-compliance` | Pricing waterfall, draft HSN/ITC-HS notes, tariff/routing, payment risk, compliance checklist |
| `codex-artifact-factory` | Use Codex App-Server Runtime and plugins to create workbooks, PDFs, DOCX, PPTX, dashboards, reports, invoices, and packs |
| `sales-followup` | Draft buyer/supplier outreach and follow-up sequences with no send without approval |
| `source-health` | Track broken, paywalled, login-required, low-relevance, high-quality, or restricted sources |
| `learning-review` | Weekly review, memory and skill update proposals, rule improvement |
| `chatgpt-boardroom-handoff` | Prepare snapshots and prompts for ChatGPT deep research and strategy |

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
