# Export Quote Pack Production

Use this skill to assemble an export quote pack draft.

## Inputs
- buyer verification note
- deep read/RFQ extraction
- supplier shortlist
- pricing proof
- export compliance draft

## Pack Includes
- proforma invoice draft
- product specification sheet
- compliance notes summary
- supplier summary
- pricing waterfall
- Incoterms and delivery terms
- payment terms proposal
- missing items list
- approval card if buyer send is proposed

## Validation
- `case_id` appears in every artifact.
- HSN/ITC-HS and origin are marked draft only.
- Freight, insurance, and currency assumptions are visible.
- No buyer reply or quotation is sent without approval.

## Must Not
- send export quote
- commit delivery date
- accept payment terms
- claim origin or final classification
