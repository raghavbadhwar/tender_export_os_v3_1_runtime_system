# Max-Capability Upgrade Roadmap — Tender Export OS v4.1

## Goal

Turn Tender Export OS from a healthy local runtime into a living, evidence-backed, approval-gated operating system that runs daily, creates durable case task graphs, captures evidence, produces repeatable artifacts, and keeps the founder in control through mobile-ready approvals.

## Implemented upgrade primitives

1. Live operating rhythm: scheduled Hermes cron jobs for morning brief, opportunity radar, supplier review, evening close, and weekly learning review.
2. Case workspaces: `cases/<case_id>/` with per-case `HERMES.md`, dossier stub, evidence, supplier, pricing, compliance, artifact, approval, and follow-up folders.
3. Evidence bundles: metadata and SHA-256 manifests for captured files.
4. Kanban task graphs: GOV and EXPORT templates that create linked task plans and can execute through `hermes kanban create/link`.
5. Structured approval cards: HTML plus JSON card output and schema for downstream mobile approval flows.
6. Founder quick commands: canonical command vocabulary for mobile/TUI/desktop usage.
7. Expanded event taxonomy: evidence, workspace, task graph, approval decision, memory proposal, and skill proposal events.

## Next productization layers

- Gateway/mobile delivery for cron outputs and approval decisions.
- Dashboard/control room for cases, approvals, source health, plugin health, and artifacts.
- Webhook intake for Drive uploads, sheet rows, RFQ emails, and supplier quote form events.
- MCP integrations for Google Workspace, document parsing/OCR, email, CRM/accounting where useful.
- Weekly skill/memory curator loop with explicit owner approval.

## Non-negotiables

- `case_id` remains the primary key.
- `data/events.jsonl` remains the canonical append-only state stream.
- CSVs, Drive files, daily briefs, and Kanban cards are projections or working views.
- No external, financial, legal, DSC, classification, origin, quote, supplier commitment, or public-exposure action proceeds without explicit owner approval and receipt.
