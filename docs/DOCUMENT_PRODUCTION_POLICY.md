# Document and Artifact Production Policy

## Role
Codex App-Server Runtime and Codex plugins produce business artifacts. Hermes routes the work and enforces owner approval. Google Drive stores the approved source of truth.

## GOV Artifacts
- tender deep-read report
- eligibility matrix
- compliance matrix
- pricing workbook
- supplier RFQ draft
- supplier scorecard
- clarification letter draft
- bid pack checklist
- approval card

## EXPORT Artifacts
- buyer verification note
- supplier comparison workbook
- export pricing workbook
- export compliance checklist
- buyer reply draft
- proforma invoice draft
- buyer proposal DOCX
- quote pack PDF
- optional buyer deck PPTX
- approval card

## Preferred Plugins/Capabilities
- spreadsheets/XLSX for workbooks and dashboards
- PDF tools for tender extraction and packs
- document/DOCX tools for letters and proposals
- presentation/PPTX tools for decks
- template creators for reusable templates
- invoice generators or spreadsheet templates for invoices
- sales/email tools for follow-up drafts
- approval/receipt builders for audit trail

## Validation
Before marking artifact production complete, verify:
- workbook/document opens or renders
- no formula errors where formulas are used
- `case_id` appears in the artifact
- missing fields are explicitly marked
- no unapproved claim is presented as final
- no external send occurred
- approval card exists if artifact is intended for external use

## Sources
- User upgrade brief: `/Users/raghav/.codex/attachments/50962de5-cb39-48a4-8d6e-31bce3df71ac/pasted-text.txt`
