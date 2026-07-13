# Source and Supplier Recommendation Proposals

Source-weight and supplier-ranking recommendations are advisory proposals, not automatic changes.

Every recommendation must include:

- proposal id and proposal status;
- sample size;
- observation window;
- uncertainty;
- false-positive impact;
- false-negative impact;
- rollback plan;
- `automatic_change_allowed: false`.

Implemented paths:

- `scripts/recommend_source_weights.py`
- `scripts/supplier_performance_projection.py`

Any future actual source-weight change, supplier shortlist promotion, blacklist, or operational routing change must pass owner approval and the relevant learning/proposal gate.
