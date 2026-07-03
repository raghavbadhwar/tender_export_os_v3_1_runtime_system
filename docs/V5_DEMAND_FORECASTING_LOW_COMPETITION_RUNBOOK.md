# V5 Demand Forecasting + Low-Competition Runbook

## Purpose

The V5 Demand Forecasting + Low-Competition Engine is an additive intelligence layer on top of the v4.1 event-ledger and CSV projection runtime. It forecasts likely repeat demand, category demand, export research lanes, and low-competition candidates while preserving proof gates.

Safety boundary: Internal-only decision support. No buyer/supplier contact, portal login, bid/RFQ submission, payment, DSC use, final price, delivery, HSN/ITC-HS, origin, tax, legal, or compliance commitment is executed by this module.

## Inputs

- `data/master_cases.csv`
- `data/demand_research.csv`
- `data/rfq_master.csv`
- `outputs/low_competition_radar/latest JSON`
- `data/buyer_purchase_history.csv`
- `data/category_demand_history.csv`
- `data/forecast_candidates.csv`
- `data/forecast_backtests.csv`

## Outputs

- `data/buyer_purchase_history.csv`
- `data/category_demand_history.csv`
- `data/forecast_candidates.csv`
- `data/forecast_backtests.csv`
- `outputs/demand_forecasting/v5_demand_forecast_low_competition_YYYYMMDD.md`
- `outputs/demand_forecasting/v5_demand_forecast_low_competition_YYYYMMDD.html`
- `outputs/demand_forecasting/v5_demand_forecast_low_competition_YYYYMMDD.json`

## Daily Run Command

```bash
python3 scripts/build_buyer_purchase_history.py --write
python3 scripts/build_category_demand_history.py --write
python3 scripts/generate_v5_demand_forecast_low_competition.py --date YYYYMMDD --write-candidates
python3 scripts/backtest_v5_demand_forecasts.py --write
```

## Shadow-Run Procedure

The Hermes cron entry `v5_demand_forecast_low_competition_shadow` is disabled by default in `config/hermes_cron.yaml`.

To run it manually, use the daily commands above from the repository root. Do not create a live Hermes schedule or delivery route unless the owner explicitly asks.

## How To Read The Report

Read the founder snapshot first. It answers:

- how many active forecasts, research lanes, and low-competition candidates exist
- how many rows still require document/RFQ/source proof
- how many cases are blocked by RAW_LEAD or missing buyer proof
- the single safest internal move today

Then use the tables:

- active demand forecasts show current case-level opportunity quality
- low-competition candidates show under-seen or easier-to-capture leads
- repeat-buyer/category predictions show future watch windows
- export research lanes stay research-only until buyer-specific proof exists
- killed/not-ready reasons show why rows cannot advance

## What Counts As Forecast Vs Proof

A forecast is an internal prediction based on signals. It does not create a bid-ready case.

Proof means source evidence such as a downloaded document, manually saved source detail, structured evidence bundle, verified RFQ, or owner-approved manual source check. `PUBLIC_LISTING_ONLY` is still a lead. `RESEARCH_ONLY_NOT_RFQ` is still research. Supplier-specific quote proof is required before pricing-ready treatment.

## What To Do With Low-Competition Candidates

Use low-competition rows to decide which internal proof-capture task to run next:

1. Capture public source detail or documents.
2. Run deep-read/fast-kill.
3. Check supplier-specific proof requirements.
4. Prepare approval cards only after the proof gate is clear.

Do not send supplier quote requests, buyer replies, export quotations, bid submissions, portal uploads, payments, DSC actions, or final commitments from this module.

## What Not To Do

Do not use this module for:

- buyer contact
- supplier contact
- portal login or credentialed portal action
- bid/RFQ submission
- payment, EMD, DSC, or document upload
- final price, delivery, HSN/ITC-HS, origin, tax, legal, or compliance commitments
- treating `PUBLIC_LISTING_ONLY` as bid-ready
- treating marketplace pricing as supplier quote proof

## Troubleshooting

If schemas fail, inspect the row and schema field named in the validator output:

```bash
python3 scripts/validate_register_schemas.py
```

If the report has no repeat/category predictions, build projections first:

```bash
python3 scripts/build_buyer_purchase_history.py --write
python3 scripts/build_category_demand_history.py --write
```

If backtests show zero rows, write forecast candidates first:

```bash
python3 scripts/generate_v5_demand_forecast_low_competition.py --date YYYYMMDD --write-candidates
```

If bare `python3 scripts/system_health_check.py --runtime` fails on local Python dependencies, the health check now runs subcommands through `.venv/bin/python` when the repo venv exists.

## Validation Checklist

```bash
python3 -m py_compile scripts/generate_v5_demand_forecast_low_competition.py
python3 -m py_compile scripts/build_buyer_purchase_history.py
python3 -m py_compile scripts/build_category_demand_history.py
python3 -m py_compile scripts/backtest_v5_demand_forecasts.py
python3 -m unittest scripts.tests.test_v5_demand_forecast_low_competition -v
python3 scripts/build_buyer_purchase_history.py --write
python3 scripts/build_category_demand_history.py --write
python3 scripts/generate_v5_demand_forecast_low_competition.py --date YYYYMMDD --write-candidates
python3 scripts/backtest_v5_demand_forecasts.py --write
python3 scripts/validate_register_schemas.py
python3 scripts/validate_case_readiness.py --all
python3 scripts/rebuild_projections_from_events.py
python3 scripts/system_health_check.py --runtime
```
