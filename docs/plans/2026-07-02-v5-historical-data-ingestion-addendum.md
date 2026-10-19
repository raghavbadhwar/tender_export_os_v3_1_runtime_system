# V5 Historical Data Ingestion Addendum

> **For Codex:** Add this to the V5 Demand Forecasting + Low-Competition Engine implementation. Historical data is the path from simple rule-based scoring to real forecasting. Do not start with ML. First build clean historical datasets, provenance, backtests, and conservative scoring.

**Runtime:** `/Users/raghav/Downloads/tender_export_os_v3_1_runtime_system`

**Current audit note:** As of this plan, the runtime has current operating CSVs such as `master_cases.csv`, `buyer_master.csv`, `rfq_master.csv`, `supplier_master.csv`, `quote_master.csv`, and `demand_research.csv`, but no dedicated historical tender/award/bidder/winner/L1 data files. Searches for `*history*`, `*award*`, and content terms like `award|winner|bidder|L1|historical` in the current runtime returned no existing historical dataset. So Codex must add this as a new ingestion/projection layer.

---

## 1. Why Historical Data Matters

Historical data lets TenderOS move from:

```text
This looks promising because of current signals.
```

to:

```text
This buyer/category has repeated 6 times, tends to come every 45-75 days, usually has low EMD, commonly awards to small suppliers, has low bidder count, and retenders often convert.
```

Historical data improves:

1. Buyer repeat prediction.
2. Category demand prediction.
3. Low-competition detection.
4. Crowding/competition estimates.
5. Price and order-size priors.
6. Fast-kill rules.
7. Backtesting and rule calibration.

---

## 2. Historical Data Tiers

Build in tiers. Do not wait for perfect data.

### Tier 0 — Internal operating history

Available immediately from existing TenderOS registers:

```text
data/master_cases.csv
data/buyer_master.csv
data/rfq_master.csv
data/supplier_master.csv
data/quote_master.csv
data/approvals_receipts.csv
data/source_health.csv
data/events.jsonl
outputs/projections/*.csv
```

Use this to answer:

```text
What did TenderOS already see?
What did it reject?
What did it deep-read?
What got supplier proof?
Which sources were noisy/useful?
```

### Tier 1 — Historical tender notices

Public tender history without award outcome.

Use for:

```text
buyer/category cadence
repeated descriptions
value ranges
EMD ranges
eligibility friction
seasonality
retender/corrigendum frequency
```

### Tier 2 — Award/outcome history

Past award data, where available.

Use for:

```text
winner names
awarded amount
bidder count
L1/L2 where available
small-supplier feasibility
incumbent lock-in risk
competition intensity
```

### Tier 3 — External market/import history

For exports and Western lanes.

Use for:

```text
country/product demand
buyer/importer recurrence
seasonality
price bands
compliance barriers
repeat buyer/product lanes
```

Do not treat generic import data as buyer-specific RFQ proof.

---

## 3. Data Sources to Explore

Codex should create source adapters only after checking source accessibility and terms. Start with read-only public pages and CSV/manual import.

### Government tender historical sources

Potential source families:

```text
GeM public bid history / bid search pages
CPPP / eProcure archived tenders
State eProcurement archive pages
Department procurement result pages
Tender award / AOC / contract award PDFs
Bid opening summaries where public
Corrigendum and retender histories
```

### Export / institutional historical sources

Potential source families:

```text
UNGM procurement notices and awards
UNDP/UNICEF/WFP procurement award pages
World Bank / ADB procurement awards
Embassy/commercial tender archives
Trade promotion bodies and buyer directories
Import/export market datasets, if legally accessible
```

### Manual upload lane

Because many sources are messy, add a manual ingestion path:

```text
historical tender CSV upload
historical award CSV upload
historical buyer/category CSV upload
historical import demand CSV upload
```

Manual import is acceptable if schema-validated and source-provenanced.

---

## 4. New Historical Data Files

Create these files:

```text
data/historical_tender_notices.csv
data/historical_awards.csv
data/historical_buyer_category_stats.csv
data/historical_competition_signals.csv
data/historical_import_demand.csv
```

Also create example files:

```text
data/examples/historical_tender_notices.example.csv
data/examples/historical_awards.example.csv
data/examples/historical_buyer_category_stats.example.csv
data/examples/historical_competition_signals.example.csv
data/examples/historical_import_demand.example.csv
```

And schemas:

```text
config/schemas/historical_tender_notices.schema.json
config/schemas/historical_awards.schema.json
config/schemas/historical_buyer_category_stats.schema.json
config/schemas/historical_competition_signals.schema.json
config/schemas/historical_import_demand.schema.json
```

---

## 5. Schema: `historical_tender_notices.csv`

Required columns:

```text
historical_tender_id,source_name,source_url,source_captured_at,workflow_type,buyer_name,buyer_type,department,country_or_state,location,category_code,category_name,product_or_service,title,description,notice_date,deadline_date,estimated_value,currency,emd_amount,eligibility_summary,document_available,corrigendum_count,retender_flag,date_extension_flag,evidence_level,raw_reference,notes,created_at,updated_at
```

Rules:

- `workflow_type`: `GOV`, `EXPORT`, or `OTHER`.
- `retender_flag` and `date_extension_flag`: `TRUE`/`FALSE`.
- `evidence_level`: `PUBLIC_NOTICE`, `DOCUMENT_CAPTURED`, `SOURCE_DETAIL_CAPTURED`, `PARTIAL`, `UNKNOWN`.
- Do not infer awards from notices.

---

## 6. Schema: `historical_awards.csv`

Required columns:

```text
historical_award_id,historical_tender_id,source_name,source_url,source_captured_at,buyer_name,department,country_or_state,category_code,category_name,product_or_service,award_date,winner_name,winner_location,awarded_value,currency,bidder_count,l1_price,l2_price,incumbent_detected,small_supplier_possible,award_document_available,evidence_level,raw_reference,notes,created_at,updated_at
```

Rules:

- `bidder_count`, `l1_price`, `l2_price` may be blank if unavailable.
- `small_supplier_possible` should be `TRUE`, `FALSE`, or `UNKNOWN`.
- Do not guess winner names or prices.
- If only a tender notice exists, do not create an award row.

---

## 7. Schema: `historical_buyer_category_stats.csv`

This is a projection generated from notices + awards.

Required columns:

```text
buyer_category_stat_id,buyer_name,department,country_or_state,workflow_type,category_code,category_name,notice_count,award_count,first_seen_date,last_seen_date,median_notice_interval_days,avg_estimated_value,median_estimated_value,avg_awarded_value,median_awarded_value,avg_emd,avg_bidder_count,retender_rate,date_extension_rate,small_supplier_win_rate,incumbent_risk_score,competition_intensity_score,buyer_repeat_score,next_likely_window_start,next_likely_window_end,confidence,created_at,updated_at
```

Core derived scores:

```text
buyer_repeat_score
competition_intensity_score
incumbent_risk_score
small_supplier_win_rate
retender_rate
date_extension_rate
```

---

## 8. Schema: `historical_competition_signals.csv`

One row per buyer/category/source signal.

Required columns:

```text
competition_signal_id,source_kind,source_record_id,buyer_name,category_code,category_name,signal_type,signal_strength,signal_direction,competition_impact,confidence,evidence_text,source_url,created_at
```

Example signals:

```text
LOW_BIDDER_COUNT
SINGLE_BID
RETENDER
DATE_EXTENSION
CORRIGENDUM
OEM_REQUIRED
HIGH_TURNOVER
HIGH_EMD
INCUMBENT_REPEAT_WINNER
SMALL_SUPPLIER_WIN
BORING_CONSUMABLE
BADLY_TITLED
```

`competition_impact`:

```text
LOWER_COMPETITION
HIGHER_COMPETITION
UNKNOWN
```

---

## 9. Schema: `historical_import_demand.csv`

For export forecasting.

Required columns:

```text
import_demand_id,source_name,source_url,source_captured_at,country,product_or_service,hs_code,category_name,buyer_or_importer_name,buyer_visible,period_start,period_end,demand_metric,demand_value,currency_or_unit,trend_direction,compliance_notes,evidence_level,notes,created_at,updated_at
```

Rules:

- This is market demand, not buyer-specific RFQ proof unless buyer/RFQ details are explicit.
- `evidence_level` must distinguish `MARKET_DATA_ONLY` from `BUYER_SPECIFIC`.

---

## 10. Scripts to Create

### 10.1 `scripts/import_historical_tenders.py`

Purpose: normalize one or more CSV/manual inputs into `data/historical_tender_notices.csv`.

CLI:

```bash
python3 scripts/import_historical_tenders.py --input path/to/file.csv
python3 scripts/import_historical_tenders.py --input path/to/file.csv --write
```

Default: dry-run.

### 10.2 `scripts/import_historical_awards.py`

Purpose: normalize award/winner/bidder history into `data/historical_awards.csv`.

CLI:

```bash
python3 scripts/import_historical_awards.py --input path/to/file.csv
python3 scripts/import_historical_awards.py --input path/to/file.csv --write
```

Default: dry-run.

### 10.3 `scripts/build_historical_buyer_category_stats.py`

Purpose: derive buyer/category stats from historical notices and awards.

CLI:

```bash
python3 scripts/build_historical_buyer_category_stats.py
python3 scripts/build_historical_buyer_category_stats.py --write
```

### 10.4 `scripts/extract_historical_competition_signals.py`

Purpose: derive competition signals from historical notices, awards, and text fields.

CLI:

```bash
python3 scripts/extract_historical_competition_signals.py
python3 scripts/extract_historical_competition_signals.py --write
```

### 10.5 `scripts/import_historical_import_demand.py`

Purpose: normalize export/import demand datasets.

CLI:

```bash
python3 scripts/import_historical_import_demand.py --input path/to/file.csv
python3 scripts/import_historical_import_demand.py --input path/to/file.csv --write
```

---

## 11. How Historical Data Changes Forecasting

Modify `scripts/generate_v5_demand_forecast_low_competition.py` to optionally read:

```text
data/historical_buyer_category_stats.csv
data/historical_competition_signals.csv
data/historical_import_demand.csv
```

New scoring inputs:

```text
historical_repeat_score
historical_competition_score
historical_small_supplier_score
historical_retender_rate
historical_bidder_count_score
historical_import_demand_score
```

Updated demand forecast formula:

```text
25% buyer/category repeat history
20% current source/proof level
15% historical competition intensity
15% low-competition live signal
10% supplier readiness
10% value/EMD/deadline actionability
5% forecast backtest reliability
```

Updated export forecast formula:

```text
25% buyer/RFQ proof
20% historical import demand
15% supplier readiness
15% compliance readiness
10% landed-margin potential
10% repeatability
5% forecast backtest reliability
```

Keep hard gates:

```text
Historical demand alone cannot make a case bid-ready.
Historical import demand alone cannot make an export RFQ verified.
Award history alone cannot authorize external action.
```

---

## 12. Backtesting Historical Forecasts

Once history exists, backtest with time splits:

```text
Train window: old historical notices/awards
Prediction window: later notices/awards
Question: did buyer/category demand actually recur?
```

Add a script later:

```text
scripts/backtest_historical_demand_model.py
```

Minimum backtest questions:

1. Did predicted buyer/category pairs recur in the next 30/60/90 days?
2. Did predicted low-competition categories have lower bidder counts?
3. Did retender/date-extension signals correlate with fewer bidders?
4. Did small suppliers win this category historically?
5. Did high-score categories produce actionable cases in the current pipeline?

---

## 13. ML Readiness Gate

Do not build ML until these minimums exist:

```text
500+ historical tender notices
100+ historical awards
50+ rows with bidder_count or competition proxy
100+ forecast_candidates rows
30+ backtest rows with HIT/MISS/PARTIAL labels
```

Before those thresholds, deterministic scoring is safer.

When thresholds are met, start with simple models only:

```text
logistic regression / random forest style tabular classifier
or deterministic calibrated scoring tables
```

Predictions allowed:

```text
repeat_purchase_probability
low_competition_probability
proof_conversion_probability
```

Predictions not allowed:

```text
guaranteed win probability
final bid price
legal/compliance certainty
```

---

## 14. Historical Data Development Tasks for Codex

Add these tasks before the original plan's ML/backtesting expansion.

### Task H1: Add historical schemas and empty CSVs

Create the files from Sections 4-9 and validate schemas.

Command:

```bash
python3 scripts/validate_register_schemas.py
```

### Task H2: Add import scripts for manual CSVs

Create:

```text
scripts/import_historical_tenders.py
scripts/import_historical_awards.py
scripts/import_historical_import_demand.py
```

Each must default to dry-run and only write with `--write`.

### Task H3: Add projection scripts

Create:

```text
scripts/build_historical_buyer_category_stats.py
scripts/extract_historical_competition_signals.py
```

### Task H4: Integrate historical projections into V5 generator

Modify:

```text
scripts/generate_v5_demand_forecast_low_competition.py
config/demand_forecasting.yaml
```

Do not break report generation if historical files are empty.

### Task H5: Add tests

Create tests for:

```text
manual import mapping
award rows not guessed from notices
repeat-score calculation
competition signal extraction
historical data not overriding proof gates
empty historical files do not break report generation
```

### Task H6: Add runbook section

Update:

```text
docs/V5_DEMAND_FORECASTING_LOW_COMPETITION_RUNBOOK.md
```

Add:

```text
How to import historical tender data
How to import award data
How to validate source provenance
How to use history without overclaiming
```

---

## 15. Verification Commands

Run after implementation:

```bash
cd /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system
python3 -m py_compile scripts/import_historical_tenders.py
python3 -m py_compile scripts/import_historical_awards.py
python3 -m py_compile scripts/import_historical_import_demand.py
python3 -m py_compile scripts/build_historical_buyer_category_stats.py
python3 -m py_compile scripts/extract_historical_competition_signals.py
python3 -m py_compile scripts/generate_v5_demand_forecast_low_competition.py
python3 scripts/validate_register_schemas.py
python3 scripts/build_historical_buyer_category_stats.py
python3 scripts/extract_historical_competition_signals.py
python3 scripts/generate_v5_demand_forecast_low_competition.py --date 20260702
python3 scripts/validate_case_readiness.py --all
python3 scripts/system_health_check.py --runtime
```

Expected:

```text
No schema failures.
No external actions.
Forecast report still generates with or without historical rows.
RAW_LEAD/PUBLIC_LISTING_ONLY proof gates remain intact.
```

---

## 16. Founder-Level Summary

Yes, the forecasting engine should use historical data. But historical data must be ingested as evidence, not magic.

The correct path is:

```text
historical notices
→ historical awards
→ buyer/category stats
→ competition signals
→ calibrated forecasts
→ backtesting
→ only later optional ML
```

This gives TenderOS a real edge:

```text
not just “what is open today”
but “what will likely repeat, where competition is weak, and what proof is still missing.”
```
