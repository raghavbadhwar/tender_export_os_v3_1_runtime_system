# Mobile Approval Protocol

Accepted reply formats:

- `APPROVE <approval_id>`
- `REJECT <approval_id> <reason>`
- `CHANGES <approval_id> <requested_change>`

Rules:
- Ambiguous replies are rejected.
- A mobile approval creates a decision receipt only.
- Execution remains a separate approval-safe step.
- No external send, submit, upload, pay, DSC, price commitment, HSN/ITC-HS confirmation, or origin claim happens automatically.
