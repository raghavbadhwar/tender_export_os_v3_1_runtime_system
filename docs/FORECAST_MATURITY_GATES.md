# Forecast Maturity Gates

Forecast probabilities remain expert-prior decision support until enough verified, time-separated outcomes exist for the exact target and workflow.

The enforced gates are:

- 30 mature observations for the exact `target_id + workflow_type` before calibration metrics are reported.
- 100 mature observations before any learned model can be registered as a candidate.
- 20 positive and 20 negative mature examples before training/candidate promotion.
- No mixed GOV/EXPORT/CROSS_WORKFLOW probability claims.

Validation commands:

```bash
python3 scripts/evaluate_forecast_calibration.py --json
python3 scripts/validate_model_registry_gates.py --json
```

`scripts/evaluate_forecast_calibration.py` reports target-level maturity. `scripts/validate_model_registry_gates.py` prevents model registry rows from claiming `CALIBRATED`, `CANDIDATE`, or `CHAMPION` status before the matching target gates are met.
