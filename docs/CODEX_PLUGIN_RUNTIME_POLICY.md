# Codex Plugin Runtime Policy

## Role
Codex is the plugin-powered artifact and runtime factory for Tender Export OS v4.1.

Hermes decides when Codex should run. Codex produces artifacts, scripts, structured patches, and verification evidence. Google Drive stores approved business artifacts.

## Plugin Capability Groups
| Group | Plugin families | Use |
|---|---|---|
| Primary artifact runtime | documents, pdf, presentations, spreadsheets, template-creator | case reports, bid packs, export packs, pricing workbooks, supplier scorecards, approval cards, proposals, decks, dashboards |
| Business and sales | sales, small-business, marketing, operations, finance, google-drive, gmail, Apollo/CRM if authenticated | draft outreach, buyer replies, follow-up sequences, sales assets, invoices, payment terms, pipeline tracking |
| Procurement/export/supplier | product-supplier-sourcing, supplier-performance-manager, profit-margin-analyzer, b2b-payment-terms-optimizer, invoice-generator, 1688-sourcing, browser/chrome | supplier sourcing, comparison, margin checks, invoice drafts, portal inspection |
| Legal/compliance | legal, commercial-legal, regulatory-legal, privacy-legal, product-legal, ai-governance-legal | first-pass risk notes, compliance drafts, terms review, approval risk notes |
| Development/runtime | browser, chrome, computer-use, record-and-replay, build-web-data-visualization, data, database-data-management, codex-security, superpowers, testing | dashboards, parser repair, source adapters, testing, reusable tooling |

## Legal Boundary
Legal plugins may draft notes and risk summaries. They are not final legal advice. Final HSN/ITC-HS, origin, SCOMET, FTA, legal compliance, and tender eligibility conclusions require human or expert approval.

## Record-And-Replay Boundary
Use record-and-replay only for non-sensitive repeatable workflows.

Never record:
- passwords
- bank or UPI pages
- DSC use
- email sending
- bid submission
- payment pages
- private tokens
- sensitive buyer or supplier data

## Health Review
Maintain:
- `data/plugin_health.csv`
- `data/capability_registry.csv`
- `config/plugin_routing.yaml`

Plugin health checks must log source command, timestamp, status, and blocker. Do not assume a plugin is available just because it appears in a policy file.

## Sources
- Local `codex plugin list --available --json`, run on 2026-06-30.
- Local `codex --help`, run on 2026-06-30.
- User upgrade brief: `/Users/raghav/.codex/attachments/50962de5-cb39-48a4-8d6e-31bce3df71ac/pasted-text.txt`
