# Weekly Forecast Quality Report

`scripts/build_weekly_forecast_quality_report.py` creates a weekly target-separated prediction quality report.

It reports:

- target populations separated by `target_id + workflow_type`;
- immature rows;
- proof/data gaps;
- calibration state;
- feature schema drift;
- source drift;
- actionable collection gaps.

It explicitly avoids combining GOV and EXPORT into a single probability claim.

Run:

```bash
python3 scripts/build_weekly_forecast_quality_report.py --write --json
```
