# Pricing + Compliance Gate Check — RUN-20260630131218

## Result

No case is currently at `PRICING_READY` in `data/master_cases.csv`; no pricing sheet or final quote/bid price was produced.

This run did not commit a price, HSN/ITC-HS classification, origin claim, delivery term, buyer/supplier communication, payment, submission, or DSC action.

## Case gate table

| case_id | workflow | status | pricing_done | quote proofs | quote IDs | pending approvals | HSN/ITC-HS candidate | decision |
|---|---|---|---|---:|---|---|---|---|
| GOV-20260630-001 | GOV | SUPPLIER_SEARCH | FALSE | 1 | Q-001 | APR-002 | - | pricing gate blocked: 1 quote proof(s), minimum 2 required |
| GOV-20260630-002 | GOV | REJECTED | FALSE | 0 | - | - | - | not in pricing scope |
| EXP-20260630-001 | EXPORT | SUPPLIER_SEARCH | FALSE | 1 | Q-002 | APR-003 | 0910.30.30 draft | pricing gate blocked: 1 quote proof(s), minimum 2 required |
| EXP-20260630-002 | EXPORT | APPROVAL_REQUIRED | TRUE | 1 | Q-003 | APR-001 | 8306 candidate only | audit warning: pricing_done TRUE / approval stage but quote_master has fewer than 2 quote proofs |

## Required next actions

- `GOV-20260630-001`: wait for owner decision on `APR-002` and at least one additional quote proof before pricing.
- `EXP-20260630-001`: wait for owner decision on `APR-003` supplier quote/clarification drafts and at least one additional quote proof before pricing; keep HSN/ITC-HS as draft-only until human/expert approval.
- `EXP-20260630-002`: do not use this pricing run to create or send external pricing; status is already `APPROVAL_REQUIRED`, buyer/source identity remains incomplete, and `quote_master.csv` shows only one quote proof despite `pricing_done=TRUE`.

## Sources cited

- `data/master_cases.csv`
- `data/quote_master.csv`
- `data/approvals_receipts.csv`
- `scripts/validate_case_readiness.py`
- `agents/pricing_agent.md`
- `AGENTS.md`
- `HERMES.md`
- `SOUL.md`
