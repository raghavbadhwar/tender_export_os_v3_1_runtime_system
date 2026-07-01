# Hybrid Research + Operational Capture Model

Tender Export OS uses a hybrid model: Deep Research finds opportunity theses, and the local runtime proves and operationalizes only the evidence-backed parts.

## 1. ChatGPT Scheduled Deep Research Owns

ChatGPT Scheduled Deep Research owns broad discovery, market/category/source intelligence, reasoning, synthesis, and cited reports. Use it for:

- broad market discovery
- low-competition category discovery
- export country and buyer-market research
- supplier market research
- buyer pattern discovery
- competitor and operator landscape
- past-award landscape research
- source discovery and new source scouting
- strategic opportunity theses and weekly intelligence

ChatGPT output is advisory. It does not mutate registers, approve actions, submit bids, send messages, certify compliance, or commit price/delivery/payment terms.

## 2. Python/Playwright Owns

Python and Playwright own exact repeatable capture from known sources and structured operational work:

- known-source monitoring
- exact portal monitoring
- public listing capture
- owner-authorized browser-session evidence capture
- document downloading where allowed
- PDF, BOQ, Excel, and table parsing
- corrigenda diffing
- document hashing
- dedupe and case ID generation
- event-ledger updates
- scoring and readiness validation
- supplier, buyer, quote-proof, and approval gates
- schema validation and regression tests
- HTML reports from stored data

Python must not become a broad general-purpose web researcher across arbitrary websites. It proves and tracks evidence after a source, category, or lead is selected.

## 3. Hermes Owns

Hermes is the control plane. It owns:

- daily owner rhythm
- approval routing and discipline
- Kanban coordination
- owner briefings
- source/plugin health routing
- scheduled-task governance
- one smallest useful recommended owner action

Hermes decides whether work should go to ChatGPT Deep Research, Codex/Python capture, or the owner approval lane.

## 4. Event Ledger Owns

`data/events.jsonl` owns memory and audit trail. It records or reconstructs:

- case state and register projections
- supplier, buyer, RFQ, and quote changes
- approval receipts and owner decisions
- evidence manifests and artifact creation
- validation and staging events

CSV files, Drive folders, Kanban cards, and briefs are projections or working views.

## 5. Owner Must Approve

The owner must approve external, money, legal, portal, DSC, compliance, and final commercial commitments:

- supplier outreach and buyer replies
- bid or RFQ submission
- tender document upload
- EMD/security/advance/supplier payment
- DSC use
- final price, delivery, payment terms, or supplier PO
- final HSN/ITC-HS classification
- country-of-origin claims
- legal/tax/compliance certification

## 6. Must Never Be Automated

Never automate or bypass:

- bid submission
- tender portal upload
- DSC signing
- EMD/security payment
- buyer quotation sending
- supplier PO placement
- supplier/buyer external outreach without approval
- final price or delivery commitment
- final HSN/ITC-HS classification
- country-of-origin claim
- legal/tax/compliance certification
- CAPTCHA, OTP, MFA, paywall, or portal-term bypass
- credential, session, cookie, token, DSC, or bank-detail storage in repo files

## 7. Broad Discovery

Broad discovery means the task requires judgment across unknown or changing sources, categories, markets, buyers, competitors, or source landscapes. It answers questions like:

- What categories should we watch?
- Which buyer markets look promising?
- Which institutions repeatedly buy boring operational items?
- Which source families are under-seen?
- Which retender/corrigenda patterns suggest lower competition?

Broad discovery belongs to ChatGPT Scheduled Deep Research.

## 8. Operational Capture

Operational capture means the source and task are known enough to repeat exactly. It captures evidence, validates it, dedupes it, hashes documents, updates state, and runs tests. It answers questions like:

- Did this known portal publish a new matching listing?
- Did this tender's corrigendum change the deadline or BOQ?
- Did we download and parse the document?
- Does this lead duplicate an existing case?
- Does the evidence support Fast Kill or Deep Read?

Operational capture belongs to Python/Playwright with approval boundaries.

## 9. Correct Routing Examples

Workflow A: New category discovery

1. Deep Research finds low-competition categories.
2. Owner selects categories.
3. Repo adds source or keyword watch.
4. Python scans known sources repeatedly.

Workflow B: Specific tender proof

1. Deep Research flags a possible retender.
2. Lead is staged.
3. Python/Playwright checks the known source.
4. Documents/evidence are captured.
5. Case enters Fast Kill or Deep Read only if evidence supports it.

Workflow C: Export opportunity

1. Deep Research identifies a buyer/product market.
2. Lead is staged.
3. Repo validates buyer evidence, supplier readiness, compliance category, and quote-proof gates.
4. Owner approves any external buyer/supplier action.

## 10. Wrong Routing Examples

- Wrong: Python searches the open internet for "best export markets this week" and writes cases directly.
- Wrong: ChatGPT Deep Research says a lead is attractive, so the repo marks it bid-ready.
- Wrong: A public listing-only lead is promoted to Deep Read without source detail, document, evidence bundle, or owner-approved manual source check.
- Wrong: A browser script logs into a portal, bypasses CAPTCHA/OTP, downloads restricted documents, or clicks submit.
- Wrong: A Deep Research report recommends sending a quote and the repo treats that as approval.

## Decision Rule

If the task needs broad judgment across unknown sources → ChatGPT Deep Research.
If the task needs exact repetition on known sources → Python/Playwright.
If the task needs login/session/download/BOQ parsing → Python/Playwright with approval boundaries.
If the task needs market/category/source discovery → ChatGPT Deep Research.
If the task needs memory, dedupe, approvals, tests → repo/Python.

## Low-Competition Orders

Deep Research finds the low-competition thesis and source/category signals.
Python proves, tracks, dedupes, scores, and stores the shortlisted evidence.

For low-competition orders:

- `PUBLIC_LISTING_ONLY` means lead, not bid-ready case.
- `DOCUMENTS_DISCOVERED` means operational capture can attempt proof.
- `DOCUMENTS_DOWNLOADED`, manually uploaded documents, source detail capture, or a structured evidence bundle can support case-candidate review.
- Low competition is a prioritization signal only; it never overrides eligibility, supplier proof, compliance, quote-proof, or approval gates.
