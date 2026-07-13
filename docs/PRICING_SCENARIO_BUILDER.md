# Pricing Scenario Builder

`scripts/pricing_scenario_builder.py` produces internal pricing scenarios for GOV and EXPORT cases.

It always outputs four cases:

- `base`
- `conservative`
- `stress`
- `walk_away`

Each scenario includes:

- cost
- price
- gross margin
- margin percentage
- downside loss
- working-capital need
- quote-validity days
- price-sensitivity percentage
- owner decision threshold
- decision warning
- `final_commitment=false`

## Use

Dry run:

```bash
.venv/bin/python scripts/pricing_scenario_builder.py \
  --case-id EXP-CASE-ID \
  --workflow-type EXPORT \
  --base-cost 1000 \
  --currency USD \
  --target-margin-pct 20 \
  --quote-validity-days 30 \
  --working-capital-need 100 \
  --json
```

Use `--write` only when the base cost comes from a validated GOV pricing draft or EXPORT commercial readiness report. Written reports append a `pricing.scenarios_drafted` event to `data/events.jsonl`.

## Boundary

Scenario reports are internal only. They do not authorize final price, export quotation, bid submission, buyer/supplier contact, delivery commitment, payment-term acceptance, or any external action.
