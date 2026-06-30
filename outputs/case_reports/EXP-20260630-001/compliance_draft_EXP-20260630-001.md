# Export Compliance Draft: EXP-20260630-001

Generated: 2026-06-30
Workflow: EXPORT
Product: Organic turmeric powder, 5000 KG monthly
Destination: Dubai, UAE
Status: Draft only. Human/export-expert approval required before using classification, origin, export policy, labels, invoice, or quote externally.

## Compliance Stop State

Do not issue a buyer quote yet. Two facts require clarification:

1. `data/master_cases.csv` listed HSN/ITC-HS candidate `0902.30`, which appears inconsistent with turmeric powder. `0902.30` maps to black tea in common HS references, not turmeric.
2. The only supplier quote, `Q-002`, describes "Organic Turmeric Powder 95% Curcumin." If the item is actually curcumin extract, oleoresin, nutraceutical ingredient, or standardized extract, it may need a different classification and certificate set than plain turmeric powder.

## Draft Classification

Candidate classification for plain turmeric powder:

- HS/ITC-HS candidate: `0910.30.30` - Turmeric (Curcuma): Powder.
- Parent heading: `0910` - Ginger, saffron, turmeric (curcuma), thyme, bay leaves, curry and other spices.
- This is a draft candidate only. Do not confirm externally until the supplier confirms product form and a human/export expert approves.

Do not use current register candidate `0902.30` externally.

## Export Policy and SCOMET

- Local category file marks "Spices and Condiments" as active, export policy "Free", and SCOMET `false`.
- For plain turmeric powder, no SCOMET concern is apparent from the local case facts.
- If the product is an extract/concentrate or a formulated health/nutraceutical product, re-check classification, export policy, and destination import requirements before proceeding.
- DGFT ITC-HS lookup must be checked again at the point of approval because export policy can change.

## India-Side Checklist

Required or likely required before export:

- IEC in the exporter name. DGFT states IEC is mandatory for export/import unless exempted.
- GST registration and export invoice readiness.
- FSSAI license with exporter/manufacturer category where applicable.
- Spices Board exporter registration/CRES or relevant spices export registration check.
- Organic claim support through NPOP/India Organic/TraceNet documents or equivalent recognized certification if "organic" appears on quote, PI, labels, or buyer-facing documents.
- Supplier COA for curcumin percentage, moisture, microbiology, heavy metals, pesticide residues, and adulterants if buyer asks for food-grade evidence.
- Batch traceability and packing declaration.

## UAE/Dubai Destination Notes

Draft requirements to verify with buyer/importer:

- Arabic-only or Arabic/English label is expected for UAE retail food labels.
- Production and expiry dates should be on the original manufactured label; do not assume they can be added after import.
- Dubai Municipality food item registration / label assessment may be required before sale in Dubai.
- Buyer/importer should confirm its UAE trade license and food import ability before shipment.
- For organic claims, buyer should confirm whether UAE-recognized organic certificate proof is required.

## Incoterms and Shipping Draft

- Proposed Incoterm in master case: FOB.
- Supplier quotes should request both EXW and FOB nearest Indian port so landed pricing can be built later.
- Current quote `Q-002` states FOB Kochi at USD 1.25/kg, but this cannot be used as final pricing because proof count is short and product description is ambiguous.
- Freight, insurance, port handling, CHA, inspection/certification, bank charges, currency buffer, and risk buffer remain unpriced.

## Draft Document Checklist

Do not generate final documents yet. Future pack should include:

- Draft proforma invoice.
- Commercial invoice draft.
- Packing list.
- Product specification sheet.
- COA, organic certificate, FSSAI license, IEC/GST, Spices Board/CRES evidence as applicable.
- Label artwork review with Arabic/English fields.
- Certificate of origin assessment.
- Supplier quote proofs and selected supplier rationale.

## Missing Information

- Buyer RFQ attachment/specification.
- Buyer importer license/food registration capability proof.
- Whether buyer needs retail pack, bulk food-service pack, or reprocessing raw material.
- Plain turmeric powder vs 95% curcumin extract clarification.
- COA and pesticide/heavy metal/microbiology requirements.
- Final approved HSN/ITC-HS.
- Confirmed export policy from DGFT for the final classification.
- Organic certificate type and country recognition.
- FOB port, freight lane, insurance requirement, and target delivery date.

## Sources

Local:
- `data/master_cases.csv`
- `data/quote_master.csv`
- `data/supplier_master.csv`
- `config/categories.yaml`
- `skills/export-compliance-review/SKILL.md`

External:
- DGFT ITC-HS import/export lookup: https://www.dgft.gov.in/CP/?opt=itchs-import-export
- DGFT IEC profile management: https://www.dgft.gov.in/CP/?opt=iec-profile-management
- Indian Trade Portal Chapter 0910 product tree: https://indiantradeportal.in/vs.jsp?pid=2&productID=4544
- Spices Board India: https://www.indianspices.com/
- APEDA NPOP: https://npop.apeda.gov.in/
- FoSCoS/FSSAI exporter license guide: https://foscos.fssai.gov.in/assets/docs/fbo/Howtoapplylicenseforexporters.pdf
- UAE labeling/marking requirements: https://www.trade.gov/knowledge-product/united-arab-emirates-labelingmarking-requirements
- Dubai Municipality food safety services: https://www.dm.gov.ae/municipality-business/food-safety-department-2/important-information-to-food-establishment/
