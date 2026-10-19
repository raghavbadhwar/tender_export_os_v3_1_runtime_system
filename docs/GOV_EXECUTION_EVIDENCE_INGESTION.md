# GOV Owner-Operated Execution Evidence Ingestion

This workflow records evidence after an owner has performed any permitted portal, DSC, payment, or contractual action. It does not operate a portal, upload, submit, use DSC, pay, accept terms, or contact a party.

## Supported milestones

`SUBMISSION_ACKNOWLEDGED`, `TECHNICAL_EVALUATION_STARTED`, `TECHNICAL_QUALIFIED`, `TECHNICAL_DISQUALIFIED`, `FINANCIAL_BID_OPENED`, `L1_DECLARED`, `AWARD_DECLARED`, `WORK_ORDER_RECEIVED`, `DELIVERY_CONFIRMED`, `INVOICE_SUBMITTED`, `PAYMENT_DUE`, and `PAYMENT_RECEIVED`.

Every record has a retained evidence path, SHA-256 hash, observed time, explicit verification status, outcome row, execution receipt, and canonical events. Only `VERIFIED` evidence updates `data/master_cases.csv`'s `execution_sub_status`; `EVIDENCE_PRESENT` remains a logged proof gap.

## Submission acknowledgement

The owner must first have an approved, submission-scoped approval record. Then record the owner-observed acknowledgement only:

```bash
.venv/bin/python scripts/record_gov_execution_milestone.py \
  --case-id GOV-YYYYMMDD-001 \
  --milestone-type SUBMISSION_ACKNOWLEDGED \
  --occurred-at 2026-07-12T10:30:00+05:30 \
  --evidence receipts/owner_supplied/portal_acknowledgement.pdf \
  --verification-status VERIFIED \
  --recorded-by owner \
  --approval-reference APR-... \
  --portal-reference PORTAL-ACK-... \
  --write
```

## Other milestones

For example, a verified L1 notice:

```bash
.venv/bin/python scripts/record_gov_execution_milestone.py \
  --case-id GOV-YYYYMMDD-001 \
  --milestone-type L1_DECLARED \
  --occurred-at 2026-07-20T11:00:00+05:30 \
  --evidence receipts/owner_supplied/l1_notice.pdf \
  --verification-status VERIFIED \
  --recorded-by owner \
  --write
```

Use `EVIDENCE_PRESENT` when an asset is retained but not yet independently checked. The system will retain the evidence but will not advance the execution tracker. The milestone receipt lists the exact event IDs and records `external_actions_executed: false` because ingestion itself has no external effect.
