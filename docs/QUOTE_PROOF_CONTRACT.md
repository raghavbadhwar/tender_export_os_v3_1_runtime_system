# Quote Proof Contract

This contract defines what counts as a strict supplier-specific quote proof for GOV pricing, EXPORT commercial readiness, monitoring, and business-state validation.

Strict quote proof is intentionally narrower than public price evidence. Marketplace listings, public catalogues, comparable prices, and generic benchmarks may support research or weak price intelligence, but they do not unlock pricing-ready treatment.

## Required Fields

A quote row satisfies `scripts/quote_proof.py::strict_quote_proofs()` only when all of the following are present and current:

- `case_id`
- `supplier_id` and `supplier_name`
- `quote_received_at` as an ISO-8601 timestamp
- supplier-specific `quote_proof_type`
- retained `quote_proof_path`
- 64-character `quote_proof_sha256`
- `quote_verification_status=VERIFIED`
- `case_spec_match=TRUE`
- product description tied to the case requirement
- positive quoted quantity or MOQ
- currency
- tax treatment, GST rate, or price basis
- positive quoted unit or total price
- positive lead time
- delivery terms
- payment terms
- quote validity date or positive validity days that has not expired at readiness time

## Explicit Non-Proofs

The following signals must not satisfy strict quote proof:

- marketplace listing
- public listing
- public catalogue
- catalogue price
- public price list
- generic benchmark
- comparable price
- TradeIndia, IndiaMART, Alibaba, or similar generic listing price
- indicative-only price
- quote with missing proof asset or hash
- quote with missing supplier identity
- quote with `case_spec_match=FALSE` or `UNKNOWN`
- expired quote

## Operational Use

All readiness gates should call the canonical strict proof function instead of reimplementing quote checks:

```python
from scripts.quote_proof import strict_quote_proofs
```

Pricing-ready GOV and EXPORT states require two distinct supplier-specific strict quote proofs unless a separately documented specialized-category exception is added and approved. This contract does not authorize supplier contact, quote requests, purchase orders, final price commitments, delivery commitments, or external sends.
