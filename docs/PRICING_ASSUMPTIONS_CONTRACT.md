# Pricing Assumptions Contract

`config/pricing_assumptions.yaml` is the versioned registry for draft pricing assumptions used by GOV and EXPORT pricing workflows.

Each active assumption records:

- `assumption_id`
- workflow type
- cost component key
- source
- observed date
- expiry date
- currency
- tax treatment
- default value
- conservative value
- responsible profile
- status

If a default value is zero, the assumption must include `zero_value_reason`. This prevents unknown costs from being silently priced as zero.

## Enforcement

`scripts/pricing_assumptions.py` validates the registry and exposes helpers used by:

- `scripts/gov_pricing_contract.py`
- `scripts/export_commercial_readiness.py`

For GOV pricing, every `ASSUMED` cost-waterfall component must cite an active versioned assumption matching the workflow and component key.

For EXPORT commercial readiness, every non-supplier-base landed-cost component must cite an active versioned assumption before `DRAFT_READY` is allowed. `supplier_base` remains quote-derived and must come from strict supplier quote proof.

## Boundary

Assumptions are internal draft pricing inputs. They do not authorize final bid price, export quotation, tax treatment, HSN/ITC-HS, origin, delivery, payment terms, supplier commitment, buyer contact, or any external action.
