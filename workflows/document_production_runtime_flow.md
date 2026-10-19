# Document Production Runtime Flow

## Purpose
Produce GOV bid artifacts and EXPORT quote artifacts through Codex runtime/plugins while Hermes enforces routing, approval, and receipt discipline.

## Runtime Split
- Hermes routes and checks approval boundaries.
- Codex App-Server Runtime produces files and validates artifacts.
- Google Drive stores reviewed outputs.

## GOV Flow
1. Confirm `case_id` and status is `PRICING_READY` or `ARTIFACT_PRODUCTION`.
2. Read deep read report, supplier shortlist, quote proofs, pricing report, and approval policy.
3. Produce bid cover page, BOQ draft, compliance matrix, eligibility declaration draft, supplier summary, EMD/security plan, timeline, risk register, and missing items list.
4. Save under `outputs/bid_packs/<case_id>/`.
5. Create approval card for submission/upload/DSC/price commitment if proposed.
6. Log run.

## EXPORT Flow
1. Confirm `case_id` and status is `PRICING_READY` or `ARTIFACT_PRODUCTION`.
2. Read buyer verification, compliance draft, supplier shortlist, quote proofs, and pricing report.
3. Produce proforma invoice draft, product specification sheet, supplier summary, pricing waterfall, Incoterms note, payment terms proposal, and missing items list.
4. Save under `outputs/export_quote_packs/<case_id>/`.
5. Create approval card for buyer reply/export quote/invoice send if proposed.
6. Log run.

## Validation
- artifact opens or renders
- `case_id` appears in each artifact
- missing fields are explicit
- no unapproved claim is final
- no external send occurred
- sources are cited

## Stop Conditions
- missing supplier proof
- missing mandatory compliance notes
- fewer than 2 quote proofs for final pricing
- approval-gated action requested
