# Mobile Approval Protocol

This protocol is prepared for a future private owner channel. It does not enable a channel or store credentials.

## Accepted decision formats

- `APPROVE <approval_id>`
- `REJECT <approval_id> <reason>`
- `CHANGES <approval_id> <requested_change>`

Ambiguous replies are rejected and routed to a local exception card.

## Delivery boundary

The channel may deliver only:

- owner briefs;
- exception alerts;
- internal Kanban updates;
- approval cards.

It must not send buyer or supplier outreach, final quotes, invoices, tender submissions, portal uploads, payment instructions, DSC/e-signatures, or commercial commitments.

## Activation requirements

A channel cannot be enabled until all of the following exist:

1. explicit owner platform selection;
2. profile-local secret reference, with the value absent from repository and receipts;
3. owner-only user/chat/topic allowlist;
4. typed Approve/Reject/Changes interaction;
5. harmless owner-only delivery canary;
6. successful readback receipt;
7. local fallback and failure exception behavior;
8. fresh validation from `scripts/validate_owner_channel_delivery.py`.

A mobile approval creates a decision receipt only. Any external business action remains a separate approval-gated connector operation. No mobile reply can authorize an action outside its exact case, action, scope hash, expiry, and unused-receipt constraints.
