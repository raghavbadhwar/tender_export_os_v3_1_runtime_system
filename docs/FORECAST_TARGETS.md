# Forecast Target Registry

`config/forecast_targets.yaml` defines the prediction contracts Hermes is allowed to use for internal prioritization.

The registry separates GOV, EXPORT, SUPPLIER, and SOURCE targets. A probability from one target must not be mixed with another target, and GOV and EXPORT probabilities must never be merged into one business claim.

Each target declares:

- `target_id`
- workflow and horizon
- exact label rule
- eligible population
- allowed pre-outcome features
- leakage exclusions
- maturity gates
- business use, allowed use, and forbidden use

The maturity standard is intentionally strict:

- at least 30 mature, time-separated observations before reporting calibration;
- at least 100 mature observations before model training;
- at least 20 positive and 20 negative examples before training;
- no champion promotion while the target remains `PRIOR_UNCALIBRATED`.

Run validation:

```bash
python3 scripts/validate_forecast_targets.py --json
```

This registry does not authorize external sends, portal actions, bid/RFQ submission, DSC use, payments, final pricing, final delivery commitments, or final legal/compliance claims.
