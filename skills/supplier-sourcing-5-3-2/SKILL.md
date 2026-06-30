# Supplier Sourcing 5-3-2

Use this skill when sourcing suppliers for a GOV tender or EXPORT RFQ.

## Rule
- Minimum 5 candidate suppliers.
- Minimum 3 source types.
- Minimum 2 quote proofs before final pricing.

Exceptions require explicit specialized-category or owner-approved exception notes.

## Inputs
- `data/master_cases.csv`
- `data/supplier_master.csv`
- `config/sources.supplier.yaml`
- `config/categories.yaml`
- product spec, quantity, delivery location, workflow

## Procedure
1. Confirm `case_id`.
2. Read existing supplier history first.
3. Search at least 3 source types.
4. Exclude blacklisted suppliers and log why.
5. Score identity, product fit, capacity, certificates, quote clarity, response speed, experience, price, payment terms, delivery, history, and communication.
6. Save shortlist to `outputs/case_reports/<case_id>/supplier_shortlist_<case_id>.md`.
7. Draft quote requests only as internal artifacts.
8. Create approval card before any supplier contact.
9. Append `data/agent_run_log.csv`.

## Stop Conditions
- fewer than 5 candidate suppliers
- supplier source requires restricted access or CAPTCHA bypass
- quote not received after 48 hours

## Must Not
- send quote requests without approval
- commit to supplier, purchase order, payment, delivery, or final price

## Sources
Cite supplier source pages, supplier master rows, quote proofs, and config files used.
