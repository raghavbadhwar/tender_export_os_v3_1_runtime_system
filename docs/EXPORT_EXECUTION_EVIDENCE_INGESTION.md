# Export Execution Evidence Ingestion

`scripts/record_export_execution_milestone.py` records owner-observed evidence for an export case. It does not send a quotation, accept a PO, dispatch goods, clear customs, invoice, pay, or contact a party.

Supported milestones are order received, sample sent, production started, inspection completed, packing completed, dispatched, customs cleared, shipped, delivery confirmed, invoice submitted, payment due, payment received, claim/return, and repeat inquiry.

Use dry-run first:

```bash
python3 scripts/record_export_execution_milestone.py \
  --case-id <CASE_ID> --milestone-type ORDER_RECEIVED \
  --occurred-at 2026-07-12T10:00:00+05:30 --evidence <local-evidence-file> \
  --verification-status VERIFIED --recorded-by owner \
  --approval-reference <APPROVED_QUOTE_OR_RFQ_REPLY_CARD>
```

Add `--write` only after checking the dry-run. A verified order requires an approved buyer-facing quotation/RFQ-reply card. Later verified milestones require verified order evidence. `EVIDENCE_PRESENT` is recorded without moving `execution_sub_status`; only `VERIFIED` evidence updates the projection.

The script appends canonical outcome and milestone events, writes a local receipt under `receipts/executions/`, and records an agent-run row. It does not consume any credentials or execute external effects.
