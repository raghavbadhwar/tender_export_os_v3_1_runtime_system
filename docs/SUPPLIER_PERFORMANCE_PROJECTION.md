# Supplier Performance Projection

`scripts/supplier_performance_projection.py` builds an internal supplier-performance projection from verified operational evidence. It is advisory and does not mutate `data/supplier_master.csv`.

## Evidence Hierarchy

Strong evidence:

- verified supplier-specific quote responses
- verified delivery or work-order outcomes linked to a selected supplier quote
- verified documentation outcomes
- verified payment outcomes
- verified defects, claims, or returns
- owner corrections with evidence status `VERIFIED` or `EVIDENCE_PRESENT`

Weak evidence:

- public reviews
- marketplace listings
- public B2B directory listings
- public catalogue prices
- founder-known or local-cluster leads without a named verified supplier quote

Weak evidence can help research and sourcing, but it must not count as delivery history, payment history, defect history, or proof of supplier reliability.

## Output

The script writes JSON reports under:

```text
outputs/supplier_performance/
```

When run with `--write`, it appends a `supplier.performance_projected` event to `data/events.jsonl`. The event is an internal receipt only and performs no external action.

## Statuses

- `NO_OPERATIONAL_HISTORY`: no verified quote or operational evidence.
- `WEAK_PUBLIC_SIGNAL_ONLY`: public or marketplace signals exist, but no verified supplier-specific quote or execution evidence exists.
- `QUOTE_VERIFIED`: at least one strict quote response exists, but no delivery/payment/documentation/defect evidence exists yet.
- `OPERATIONAL_EVIDENCE`: verified quote plus execution or owner-correction evidence exists.
- `OWNER_REVIEW`: verified negative correction or defect/claim evidence requires owner review before promotion.

## Boundary

Supplier score changes remain proposals. Do not promote supplier memory, ranking rules, default supplier choices, or blacklist/watchlist changes without owner-approved learning promotion and rollback evidence.
