# Pack Readiness Validation

`scripts/validate_pack_readiness.py` is the approval-facing validator for GOV bid packs and EXPORT quote packs.

It runs after the lower-level pack verifier:

- GOV: `scripts/codex_bid_pack_contract.py`
- EXPORT: `scripts/codex_export_quote_pack_contract.py`

It then adds approval-readiness checks for:

- explicit `approval_scope`
- source citations
- two quote-proof receipt references
- empty `unresolved_unknowns`
- prohibited final-claim phrases
- `external_actions_executed=false`

## Required Manifest Additions

Pack manifests should include:

```json
{
  "approval_scope": {
    "proposed_action": "send_export_quotation",
    "approval_boundary": "owner_decision_required_before_external_action",
    "scope_hash": "...",
    "final_claims_approved": false,
    "external_actions_executed": false
  },
  "source_citations": [],
  "quote_proof_receipts": [],
  "unresolved_unknowns": []
}
```

## Boundary

Passing pack readiness only means the internal pack is ready for owner review or approval-card routing. It does not send, submit, upload, commit price, confirm compliance, claim origin, accept payment terms, or perform any external action.
