# Compliance Matrix Format

The compliance matrix is the owner-review bridge between Deep Read, Pricing, Pack Builder, and Approval Desk. It is a draft artifact only. It must never claim final legal, HSN/ITC-HS, origin, eligibility, price, or delivery compliance without owner and specialist approval where required.

## Required Columns

| Column | Purpose |
|---|---|
| `clause_id` | Tender/RFQ clause number, section, page, or buyer note reference. |
| `requirement_text` | Exact short paraphrase of the requirement. |
| `requirement_type` | Eligibility, technical, commercial, delivery, compliance, document, financial, or other. |
| `our_position` | Compliant, gap, conditional, not applicable, or needs review. |
| `evidence_source` | File, page, URL, register row, quote proof, or report used. |
| `evidence_page_or_cell` | Page number, table row, spreadsheet cell, or evidence map reference. |
| `gap_status` | `NONE`, `OPEN`, `OWNER_DECISION`, `SPECIALIST_REVIEW`, or `BLOCKER`. |
| `owner_decision_needed` | `YES` when the matrix row affects external action, price, compliance, eligibility, origin, or delivery commitment. |
| `notes` | Short operational note, assumption, or missing item. |

## Rules

- Every mandatory clause gets one row.
- Missing evidence is an `OPEN` gap, not an inferred pass.
- SCOMET, prohibited, origin, final classification, legal certification, DSC, payment, and final price items are approval or specialist gates.
- A pack can be built with open gaps only if those gaps are listed in `missing_items_<case_id>.md` and the approval card.
- The matrix cites source files and evidence references; it does not embed private credentials, cookies, bank details, DSC files, or raw portal sessions.
