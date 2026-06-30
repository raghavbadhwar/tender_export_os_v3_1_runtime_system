# RFQ Evidence Intake — EXP-20260630-002

Generated at: 2026-06-30T13:06:43+05:30
Workflow: EXPORT
Task: Intake RFQ evidence
Evidence status: PARTIAL / INTERNAL-ONLY

## Intake conclusion

The available evidence for EXP-20260630-002 is reconstructed from local Tender Export OS registers and approval artifacts only. No original RFQ source URL, buyer legal identity, buyer message, buyer document, screenshot, or uploaded RFQ file is present in the current case evidence folder or case report manifest.

Do not send the export quotation or treat the buyer/RFQ as verified until buyer/source evidence is captured and approval card APR-001 is corrected.

## Case register evidence

- case_id: EXP-20260630-002
- opportunity: Brass Decorative Items - Mixed Set
- product_or_service: Brass Decorative Items
- quantity: 200 Pieces
- buyer recorded: Unknown UK buyer - see approval register
- buyer country: United Kingdom
- source_name: Recovered local registers
- source_url: MISSING
- status: APPROVAL_REQUIRED
- approval_status: PENDING
- HSN/ITC-HS: 8306 candidate only
- export_policy: Draft review required
- SCOMET flag: FALSE
- incoterms proposed: FOB
- FOB price in register: 4.56
- notes: Recovered from data/approvals_receipts.csv APR-001, data/quote_master.csv Q-003, data/supplier_master.csv SUP-004, and agent_run_log RUN-005/RUN-006. Buyer identity/source URL missing; do not send externally until approval card is corrected.

Source: data/master_cases.csv

## Approval evidence

- approval_id: APR-001
- proposed action: send_export_quotation
- proposed by: pack_builder_agent
- amount_inr: 56000
- amount_usd: 680
- approval_status: PENDING
- approval card: receipts/approvals/EXP-20260630-002_approval_card.html
- JSON confidence score: 60
- JSON missing information:
  - Expected benefit not fully quantified in approval register.
  - Concrete risk not fully specified in approval register.
  - HSN/ITC-HS is candidate only until expert approval.

Sources: data/approvals_receipts.csv; receipts/approvals/EXP-20260630-002_approval_card.json; receipts/approvals/EXP-20260630-002_approval_card.html

## Supplier and quote evidence

Current quote register rows for EXP-20260630-002: 1

- quote_id: Q-003
- supplier_id: SUP-004
- supplier_name: Artisan Craft India
- quote request sent at: 2026-06-20T10:00:00
- quote received at: 2026-06-21T18:00:00
- response hours: 32
- product description: Brass Decorative Items - Mixed Set
- quantity: 200 Pieces
- unit_price_inr: 380
- total_price_inr: 76000
- GST rate / amount: 12% / 9120
- price including GST: 85120
- lead time days: 21
- delivery terms: Ex-Jaipur
- payment terms offered: 50% advance
- validity days: 30
- certificate included: FALSE
- sample available / cost: TRUE / 2000
- incoterms: FOB
- FOB price USD: 4.56
- packaging details: Bubble wrap + wooden box sets
- quality grade: Handmade Grade A
- selected_for_pricing: FALSE
- quote notes: Slower response. Higher price. Backup supplier.

Supplier row summary:

- supplier_id: SUP-004
- supplier_name: Artisan Craft India
- city/state/country: Jaipur, Rajasthan, India
- source_type/platform: local_cluster / Google Maps
- products supplied: Brass Figurines; Handicrafts; Home Decor
- HSN codes: 8306,6913,7117
- IEC code present: YES
- GSTIN present: NO
- export experience: TRUE
- total supplier score: 80
- blacklisted/watchlisted: FALSE / FALSE
- supplier notes: Local Jaipur artisan cluster contact. Good for small export orders.

Sources: data/quote_master.csv; data/supplier_master.csv

## Reconciliation findings

- Supported quote proof count in data/quote_master.csv: 1
- Artifact manifest open gate quote_proof_count: 1
- RUN-005 note: Pricing complete for EXP-20260630-002. 2 quote proofs received.
- RUN-006 note: Pack built for EXP-20260630-002. Approval card created.

Finding: RUN-005 says pricing completed with 2 quote proofs, but the current quote register and artifact manifest support only one received quote proof for EXP-20260630-002 (Q-003). Treat the earlier "2 quote proofs" note as unsupported until a second quote proof is located and captured.

## Evidence gaps blocking external use

- Original buyer/RFQ source URL is missing.
- Buyer legal identity and credibility score are missing.
- Buyer message/RFQ document/screenshot is missing.
- Approval card risk and recovery fields are placeholders.
- Compliance remains draft-only; HSN/ITC-HS 8306 is candidate-only.
- Supplier proof is thin: one quote proof only; Q-003 is marked selected_for_pricing=FALSE.

## Allowed next steps

- Continue internal buyer/source verification for EXP-20260630-002.
- Ask changes on APR-001 unless the missing buyer/RFQ evidence is supplied.
- Update approval card APR-001 only after buyer/source evidence, concrete risk, recovery path, and compliance notes are corrected.

## Hard stop

No external quote, supplier/buyer message, HSN/ITC-HS confirmation, origin claim, price commitment, delivery commitment, or payment-term acceptance may be made from this evidence intake. Owner approval is still pending, and the evidence package is incomplete.

## Sources used

- data/master_cases.csv
- data/approvals_receipts.csv
- data/quote_master.csv
- data/supplier_master.csv
- data/agent_run_log.csv
- receipts/approvals/EXP-20260630-002_approval_card.json
- receipts/approvals/EXP-20260630-002_approval_card.html
- outputs/case_reports/EXP-20260630-002/artifact_manifest.json
- cases/EXP-20260630-002/HERMES.md
