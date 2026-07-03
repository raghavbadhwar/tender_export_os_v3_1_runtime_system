# V5 Demand Forecasting + Low-Competition Engine Implementation Plan

> **For Codex:** Implement this plan task-by-task. Keep TenderOS v4.1 as the operating kernel. Do not rebuild the runtime. Do not perform any external action. Run the exact validators listed after every phase.

**Goal:** Turn the first V5 demand/low-competition report prototype into a durable, tested TenderOS intelligence module that forecasts likely demand, predicts repeat buying, finds low-competition opportunities, preserves proof gates, and produces founder-ready daily recommendations.

**Architecture:** Add an additive V5 intelligence layer on top of the current event-ledger/CSV-projection runtime. Keep deterministic Python scripts as the execution layer. Use CSV/JSON/HTML/Markdown outputs first; do not introduce a database, graph store, MCP server, or broad agent factory in this implementation.

**Tech Stack:** Python 3 stdlib, existing TenderOS CSV registers, existing validators, YAML config files, Markdown/HTML/JSON reports. Avoid new dependencies unless absolutely necessary.

---

## 0. Current Runtime Context

Canonical runtime folder:

```text
/Users/raghav/Downloads/tender_export_os_v3_1_runtime_system
```

Already created V5 seed artifacts:

```text
docs/V5_DEMAND_FORECASTING_LOW_COMPETITION_ENGINE.md
config/demand_forecasting.yaml
scripts/generate_v5_demand_forecast_low_competition.py
outputs/demand_forecasting/v5_demand_forecast_low_competition_20260702.md
outputs/demand_forecasting/v5_demand_forecast_low_competition_20260702.html
outputs/demand_forecasting/v5_demand_forecast_low_competition_20260702.json
```

The seed generator currently reads:

```text
data/master_cases.csv
data/demand_research.csv
outputs/low_competition_radar/latest JSON
```

The last verified run produced:

```text
active_cases_forecasted: 12
research_lanes_forecasted: 21
low_competition_candidates: 8
```

Known good validation command:

```bash
cd /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system
python3 -m py_compile scripts/generate_v5_demand_forecast_low_competition.py
python3 scripts/generate_v5_demand_forecast_low_competition.py --date 20260702
python3 scripts/validate_register_schemas.py
python3 scripts/validate_case_readiness.py --all
python3 scripts/rebuild_projections_from_events.py
```

Expected current readiness blockers are valid business-proof blockers, not implementation failures:

```text
EXP-20260630-001 BLOCKED because linked RFQ is RAW_LEAD
EXP-20260630-002 BLOCKED because linked RFQ is RAW_LEAD
```

---

## 1. Non-Negotiable Safety Rules

Codex must preserve these boundaries:

1. No buyer contact.
2. No supplier contact.
3. No portal login or credentialed action.
4. No bid/RFQ submission.
5. No payment, EMD, DSC use, or document upload.
6. No final price, delivery, HSN/ITC-HS, origin, tax, or legal/compliance commitment.
7. Forecasts never create bid-ready cases.
8. `PUBLIC_LISTING_ONLY` rows remain leads until document/RFQ/source proof exists.
9. Supplier-specific quote proof is required before pricing-ready treatment.
10. Founder approval is required before any external action.

Every generated report must include a safety line equivalent to:

```text
Internal-only decision support. No buyer/supplier contact, portal login, bid/RFQ submission, payment, DSC use, final price, delivery, HSN/ITC-HS, origin, tax, legal, or compliance commitment executed.
```

---

## 2. Desired End State

After implementation, TenderOS should have a mature V5 Module 1 with:

```text
1. Buyer repeat-purchase forecast
2. Category demand forecast
3. Export demand forecast
4. Low-competition opportunity detection
5. Proof-gap-aware recommendation engine
6. Forecast backtesting
7. Daily Markdown/HTML/JSON report
8. Schema validation for all new projection files
9. Deterministic tests for scoring, filtering, proof gates, and report generation
10. Optional cron hook, disabled or shadow-run safe by default
```

The founder-facing output should answer:

```text
What demand is likely to appear next?
Which buyers/categories repeat?
Which active orders look low competition?
Which opportunities are real vs research-only?
What proof is missing?
What is the one safest internal action today?
```

---

## 3. Files to Create or Modify

### Create

```text
config/schemas/buyer_purchase_history.schema.json
config/schemas/category_demand_history.schema.json
config/schemas/forecast_candidates.schema.json
config/schemas/forecast_backtests.schema.json

data/buyer_purchase_history.csv
data/category_demand_history.csv
data/forecast_candidates.csv
data/forecast_backtests.csv

data/examples/buyer_purchase_history.csv
data/examples/category_demand_history.csv
data/examples/forecast_candidates.csv
data/examples/forecast_backtests.csv

scripts/build_buyer_purchase_history.py
scripts/build_category_demand_history.py
scripts/backtest_v5_demand_forecasts.py
scripts/tests/test_v5_demand_forecast_low_competition.py

docs/V5_DEMAND_FORECASTING_LOW_COMPETITION_RUNBOOK.md
```

### Modify

```text
scripts/generate_v5_demand_forecast_low_competition.py
config/demand_forecasting.yaml
manifest.json
config/hermes_cron.yaml   # only add shadow-run entry; do not enable external delivery
README.md                 # add short pointer only if README already has module list
```

### Do not modify unless tests force it

```text
data/master_cases.csv
data/events.jsonl
data/approvals_receipts.csv
config/approval_policy.yaml
config/credential_policy.yaml
```

---

## 4. Data Model Specification

### 4.1 `data/buyer_purchase_history.csv`

Purpose: one row per buyer/category forecast history.

Required columns:

```text
history_id,buyer_name,buyer_type,department,country_or_state,workflow_type,category_code,category_name,source_names,past_case_count,last_seen_date,first_seen_date,avg_estimated_value,median_estimated_value,avg_emd,repeat_interval_days,next_likely_window_start,next_likely_window_end,buyer_repeat_score,evidence_level,confidence,notes,created_at,updated_at
```

Rules:

- `history_id` format: `BPH-{slug-buyer}-{slug-category}`.
- `workflow_type`: `GOV`, `EXPORT`, or `MIXED`.
- Score fields must be numeric 0–100.
- Dates must be `YYYY-MM-DD` or blank.
- If only one case exists, repeat interval should be blank and confidence should usually be `LOW`.

### 4.2 `data/category_demand_history.csv`

Purpose: one row per category/market trend.

Required columns:

```text
category_history_id,workflow_type,category_code,category_name,country_or_state,source_names,total_signal_count,active_case_count,research_lane_count,verified_rfq_count,low_competition_count,supplier_ready_count,last_seen_date,trend_direction,demand_score,low_competition_fit_score,supplier_readiness_score,confidence,recommended_next_action,created_at,updated_at
```

Rules:

- `trend_direction`: `RISING`, `STABLE`, `DECLINING`, `UNKNOWN`.
- `confidence`: `HIGH`, `MEDIUM`, `LOW`.
- Do not mark `RISING` unless at least 2 independent signals exist.

### 4.3 `data/forecast_candidates.csv`

Purpose: durable projection of current forecasted opportunities.

Required columns:

```text
forecast_id,run_id,forecast_date,horizon,forecast_type,case_or_research_id,workflow_type,buyer_or_market,category_name,product_or_service,source_name,source_url,forecast_score,confidence,repeat_probability,low_competition_score,supplier_readiness_score,evidence_level,proof_gap,next_safe_action,approval_required_before_external_action,kill_or_watch_reason,created_at
```

Rules:

- `forecast_type`: `ACTIVE_CASE`, `RESEARCH_LANE`, `LOW_COMPETITION`, `BUYER_REPEAT`, `CATEGORY_DEMAND`.
- `approval_required_before_external_action` must be `TRUE` for anything that could lead to external action.
- If evidence is `PUBLIC_LISTING_ONLY`, `next_safe_action` must not be external.

### 4.4 `data/forecast_backtests.csv`

Purpose: track forecast quality over time.

Required columns:

```text
backtest_id,forecast_id,forecast_date,review_date,case_or_research_id,forecast_type,predicted_action,observed_outcome,outcome_label,score_delta,false_positive_reason,false_negative_reason,learning_note,config_change_recommended,created_at
```

Rules:

- `outcome_label`: `HIT`, `PARTIAL_HIT`, `MISS`, `NOT_ENOUGH_TIME`, `BLOCKED_BY_PROOF`, `KILLED_CORRECTLY`.
- No backtest should mutate source registers; it only writes this backtest projection when run with `--write`.

---

## 5. Implementation Tasks

### Task 1: Establish Baseline and Snapshot

**Objective:** Verify current runtime before changing implementation files.

**Files:** none.

**Steps:**

1. Run:

```bash
cd /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system
python3 scripts/system_health_check.py --runtime
python3 scripts/validate_register_schemas.py
python3 scripts/validate_case_readiness.py --all
python3 scripts/rebuild_projections_from_events.py
python3 scripts/generate_v5_demand_forecast_low_competition.py --date 20260702
```

2. Expected:

```text
Schema validation passed: 10 CSV schemas + event ledger
EXP-20260630-001 and EXP-20260630-002 may remain BLOCKED due to RAW_LEAD
Dry-run projection complete
V5 demand report generated
```

3. If validators fail for reasons unrelated to known RFQ proof blockers, stop and report before implementing.

---

### Task 2: Add Projection Schemas

**Objective:** Add JSON schemas for the four new forecast projection CSVs.

**Files:**

- Create: `config/schemas/buyer_purchase_history.schema.json`
- Create: `config/schemas/category_demand_history.schema.json`
- Create: `config/schemas/forecast_candidates.schema.json`
- Create: `config/schemas/forecast_backtests.schema.json`

**Implementation guidance:**

Follow the style of existing schemas in `config/schemas/*.schema.json`. Include:

```json
{
  "file": "data/forecast_candidates.csv",
  "primary_key": "forecast_id",
  "required_columns": [],
  "required_fields": [],
  "enums": {},
  "date_fields": [],
  "numeric_fields": [],
  "url_fields": []
}
```

Use the column definitions from Section 4.

**Verification:**

Run:

```bash
python3 scripts/validate_register_schemas.py
```

Expected: schema validation still passes, or it fails because CSVs do not exist yet. If it requires CSVs immediately, proceed to Task 3 before judging.

---

### Task 3: Add Empty Data and Example CSVs

**Objective:** Add headers-only production projection files and example files for tests.

**Files:**

- Create: `data/buyer_purchase_history.csv`
- Create: `data/category_demand_history.csv`
- Create: `data/forecast_candidates.csv`
- Create: `data/forecast_backtests.csv`
- Create matching `data/examples/*.csv`

**Steps:**

1. Create each production file with the exact header row from Section 4.
2. Create each example file with header + 1–2 realistic rows.
3. Do not add private data or credentials.

**Verification:**

```bash
python3 scripts/validate_register_schemas.py
```

Expected:

```text
Schema validation passed: 14 CSV schemas + event ledger
```

The exact count may differ if the validator counts only configured schemas, but all new schemas must pass.

---

### Task 4: Refactor Common Forecast Utilities Safely

**Objective:** Keep the current generator working while extracting reusable helpers only if useful.

**Files:**

- Modify: `scripts/generate_v5_demand_forecast_low_competition.py`
- Optional create: `scripts/v5_forecast_utils.py`
- Test: `scripts/tests/test_v5_demand_forecast_low_competition.py`

**Guidance:**

YAGNI rule: if extraction creates risk, keep helpers inside the current script. Do not break the working generator for purity.

Core functions that must remain testable:

```text
safe_float
clamp
confidence
forecast_horizon
evidence_score_from_case
supplier_readiness_score
repeat_pattern_score
low_comp_signal_from_case
active_case_forecasts
demand_research_forecasts
low_competition_candidates
choose_recommended_actions
```

**Verification:**

```bash
python3 -m py_compile scripts/generate_v5_demand_forecast_low_competition.py
python3 scripts/generate_v5_demand_forecast_low_competition.py --date 20260702
```

Expected: same output paths generated.

---

### Task 5: Add Deterministic Unit Tests

**Objective:** Test scoring, filtering, and proof gates without relying on live files.

**Files:**

- Create: `scripts/tests/test_v5_demand_forecast_low_competition.py`

**Tests to include:**

1. `test_public_listing_only_is_not_bid_ready`
   - Input: low-competition radar item with `evidence_level=PUBLIC_LISTING_ONLY`.
   - Expected: candidate exists but `bid_ready` is false and proof gap mentions documents/RFQ/source proof.

2. `test_mock_and_fixture_rows_are_filtered`
   - Input: item with `case_id=MOCK-GOV-001` and item with buyer/title containing `Fixture`.
   - Expected: neither appears in candidates.

3. `test_zero_score_placeholder_without_case_id_is_filtered`
   - Input: item without `case_id` and score `0`.
   - Expected: filtered.

4. `test_research_lane_stays_research_only`
   - Input: demand research row for handicrafts/UK.
   - Expected: evidence label `RESEARCH_ONLY_NOT_RFQ`; proof gap includes buyer-specific RFQ/source detail.

5. `test_forecast_never_recommends_external_action_for_raw_lead`
   - Input: export case with RAW_LEAD/MISSING evidence.
   - Expected: next action is internal proof capture/deep-read, not send/quote/contact.

6. `test_low_competition_signal_detects_retender_or_corrigendum`
   - Input: case title/notes containing retender/corrigendum/date extension.
   - Expected: low-competition score is materially higher than baseline.

**Test command:**

Try stdlib first:

```bash
python3 -m unittest scripts.tests.test_v5_demand_forecast_low_competition -v
```

If the repo already uses pytest, add compatibility but do not require a new dependency.

---

### Task 6: Build Buyer Purchase History Projection

**Objective:** Generate buyer/category repeat-purchase history from current cases and, if safe, event/projection data.

**Files:**

- Create: `scripts/build_buyer_purchase_history.py`
- Modify/write output: `data/buyer_purchase_history.csv` only when `--write` is passed

**Behavior:**

Default mode must be dry-run.

CLI:

```bash
python3 scripts/build_buyer_purchase_history.py
python3 scripts/build_buyer_purchase_history.py --write
```

Input priority:

1. `data/master_cases.csv`
2. `outputs/projections/master_cases.csv` if production master is missing
3. `data/examples/master_cases.csv` only for tests, never for production output unless explicitly passed

Fields to compute:

```text
past_case_count
first_seen_date
last_seen_date
avg_estimated_value
median_estimated_value
avg_emd
repeat_interval_days
buyer_repeat_score
confidence
next_likely_window_start
next_likely_window_end
```

Scoring baseline:

```text
buyer_repeat_score = min(100, past_case_count * 20 + category_repeat_bonus + recent_seen_bonus)
```

Confidence:

```text
HIGH if past_case_count >= 4 and at least 2 dates exist
MEDIUM if past_case_count >= 2
LOW otherwise
```

**Verification:**

```bash
python3 -m py_compile scripts/build_buyer_purchase_history.py
python3 scripts/build_buyer_purchase_history.py
python3 scripts/build_buyer_purchase_history.py --write
python3 scripts/validate_register_schemas.py
```

---

### Task 7: Build Category Demand History Projection

**Objective:** Generate category/market demand trends from active cases + demand research + low-competition radar.

**Files:**

- Create: `scripts/build_category_demand_history.py`
- Modify/write output: `data/category_demand_history.csv` only when `--write` is passed

**Behavior:**

Compute per category/country/state:

```text
total_signal_count
active_case_count
research_lane_count
verified_rfq_count
low_competition_count
supplier_ready_count
trend_direction
demand_score
low_competition_fit_score
supplier_readiness_score
confidence
recommended_next_action
```

Trend rules:

```text
RISING: >= 3 total signals and >= 2 independent source names
STABLE: >= 2 total signals
DECLINING: only if historical data supports it; otherwise do not use
UNKNOWN: default
```

**Verification:**

```bash
python3 -m py_compile scripts/build_category_demand_history.py
python3 scripts/build_category_demand_history.py
python3 scripts/build_category_demand_history.py --write
python3 scripts/validate_register_schemas.py
```

---

### Task 8: Make Forecast Generator Write `forecast_candidates.csv`

**Objective:** Persist the forecast output as a structured projection, not only report files.

**Files:**

- Modify: `scripts/generate_v5_demand_forecast_low_competition.py`
- Modify/write output: `data/forecast_candidates.csv` only with `--write-candidates`

**CLI requirement:**

Existing behavior remains read-only/report-only by default:

```bash
python3 scripts/generate_v5_demand_forecast_low_competition.py --date 20260702
```

New behavior:

```bash
python3 scripts/generate_v5_demand_forecast_low_competition.py --date 20260702 --write-candidates
```

When `--write-candidates` is passed:

- Write rows from active forecasts, research forecasts, low-comp candidates, and optionally buyer/category projections.
- Each row must have a stable `forecast_id`, e.g.:

```text
FC-{date}-{forecast_type}-{case_or_research_id_slug}
```

- Do not append duplicates for same `run_id` + `case_or_research_id` + `forecast_type`; rewrite the projection safely.

**Verification:**

```bash
python3 scripts/generate_v5_demand_forecast_low_competition.py --date 20260702 --write-candidates
python3 scripts/validate_register_schemas.py
```

---

### Task 9: Add Forecast Backtesting

**Objective:** Let TenderOS learn whether forecasts later became useful, without overclaiming accuracy.

**Files:**

- Create: `scripts/backtest_v5_demand_forecasts.py`
- Modify/write output: `data/forecast_backtests.csv` only with `--write`

**CLI:**

```bash
python3 scripts/backtest_v5_demand_forecasts.py
python3 scripts/backtest_v5_demand_forecasts.py --write
```

**Backtest labels:**

```text
HIT
PARTIAL_HIT
MISS
NOT_ENOUGH_TIME
BLOCKED_BY_PROOF
KILLED_CORRECTLY
```

**Initial outcome logic:**

- `HIT`: forecasted case advanced to `DEEP_READ`, `SUPPLIER_SEARCH`, `PRICING_READY`, or approval with stronger evidence.
- `BLOCKED_BY_PROOF`: case remained blocked due to missing RFQ/document/supplier proof.
- `KILLED_CORRECTLY`: case was rejected with a kill reason matching a forecast proof/risk gap.
- `NOT_ENOUGH_TIME`: less than horizon window elapsed.
- `MISS`: forecast got no progress, no new proof, and no justified kill after enough time.

Do not calculate precision/recall until enough rows exist. Start with row-level review.

**Verification:**

```bash
python3 -m py_compile scripts/backtest_v5_demand_forecasts.py
python3 scripts/backtest_v5_demand_forecasts.py
python3 scripts/backtest_v5_demand_forecasts.py --write
python3 scripts/validate_register_schemas.py
```

---

### Task 10: Strengthen Report Output

**Objective:** Make the report founder-ready and not just a table dump.

**Files:**

- Modify: `scripts/generate_v5_demand_forecast_low_competition.py`
- Modify generated output templates inside the script or create template files if existing report style supports templates.

**Report sections required:**

```text
1. Founder snapshot
2. Recommended internal actions
3. Top active demand forecasts
4. Top low-competition candidates
5. Top repeat-buyer/category predictions
6. Top export research lanes
7. Killed/not-ready reasons
8. Proof gaps
9. Backtest/learning notes, if available
10. Guardrails
```

**Founder snapshot format:**

```text
Today’s V5 engine found:
- X active forecasts
- Y low-competition candidates
- Z demand research lanes
- N candidates requiring document/RFQ proof before action
- M cases blocked by RAW_LEAD or missing buyer proof

Best internal move today: [case/lane + action]
```

**Verification:**

```bash
python3 scripts/generate_v5_demand_forecast_low_competition.py --date 20260702
open outputs/demand_forecasting/v5_demand_forecast_low_competition_20260702.html
```

If browser/open is not available, read the Markdown and inspect the HTML file exists.

---

### Task 11: Add Shadow Cron Entry

**Objective:** Make the V5 engine runnable daily without replacing the current owner brief.

**Files:**

- Modify: `config/hermes_cron.yaml`

**Rules:**

- Add a `shadow` or `disabled` entry if the config supports it.
- Do not replace existing morning owner brief.
- Do not deliver externally from TUI context.
- The cron command should only run internal scripts and write local outputs.

Suggested entry shape, adjusted to existing config style:

```yaml
- name: v5_demand_forecast_low_competition_shadow
  enabled: false
  schedule: "15 7 * * *"
  command: "python3 scripts/generate_v5_demand_forecast_low_competition.py"
  description: "Shadow-run V5 demand forecast + low-competition report. Internal-only; no external actions."
```

**Verification:**

Run whatever existing cron/config validator exists. If no validator exists, at least run:

```bash
python3 scripts/system_health_check.py --runtime
```

Do not schedule live Hermes cron from Codex unless the owner explicitly asks.

---

### Task 12: Add Runbook

**Objective:** Document how the owner/Hermes/Codex should operate this module.

**Files:**

- Create: `docs/V5_DEMAND_FORECASTING_LOW_COMPETITION_RUNBOOK.md`

**Runbook sections:**

```text
Purpose
Inputs
Outputs
Daily run command
Shadow-run procedure
How to read the report
What counts as forecast vs proof
What to do with low-competition candidates
What not to do
Troubleshooting
Validation checklist
```

Include exact commands:

```bash
python3 scripts/build_buyer_purchase_history.py --write
python3 scripts/build_category_demand_history.py --write
python3 scripts/generate_v5_demand_forecast_low_competition.py --date YYYYMMDD --write-candidates
python3 scripts/backtest_v5_demand_forecasts.py --write
python3 scripts/validate_register_schemas.py
python3 scripts/validate_case_readiness.py --all
```

---

### Task 13: Update Manifest and README Pointers

**Objective:** Make the new module discoverable without changing architecture doctrine.

**Files:**

- Modify: `manifest.json`
- Optional modify: `README.md`

**Manifest additions:**

Add new docs/config/scripts/data files wherever the manifest tracks them. Keep naming consistent with existing manifest structure.

**README pointer:**

Add a short section only if README has module documentation:

```text
V5 Demand Forecasting + Low-Competition Engine
- Spec: docs/V5_DEMAND_FORECASTING_LOW_COMPETITION_ENGINE.md
- Runbook: docs/V5_DEMAND_FORECASTING_LOW_COMPETITION_RUNBOOK.md
- Generator: scripts/generate_v5_demand_forecast_low_competition.py
```

**Verification:**

```bash
python3 scripts/system_health_check.py --runtime
```

---

### Task 14: Full Verification Pass

**Objective:** Prove the implementation is working and safe.

Run:

```bash
cd /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system
python3 -m py_compile scripts/generate_v5_demand_forecast_low_competition.py
python3 -m py_compile scripts/build_buyer_purchase_history.py
python3 -m py_compile scripts/build_category_demand_history.py
python3 -m py_compile scripts/backtest_v5_demand_forecasts.py
python3 -m unittest scripts.tests.test_v5_demand_forecast_low_competition -v
python3 scripts/build_buyer_purchase_history.py --write
python3 scripts/build_category_demand_history.py --write
python3 scripts/generate_v5_demand_forecast_low_competition.py --date 20260702 --write-candidates
python3 scripts/backtest_v5_demand_forecasts.py --write
python3 scripts/validate_register_schemas.py
python3 scripts/validate_case_readiness.py --all
python3 scripts/rebuild_projections_from_events.py
python3 scripts/system_health_check.py --runtime
```

Expected:

- Python compile passes.
- Unit tests pass.
- New projection CSVs validate.
- Known RAW_LEAD cases remain blocked.
- Reports regenerate.
- Dry-run projections complete.
- System health check passes.

If any command fails, Codex must fix the root cause or report the blocker directly. Do not fabricate passing output.

---

## 6. Acceptance Criteria

Implementation is complete only when all are true:

1. New projection schemas exist and validate.
2. New projection CSVs exist and are safe to regenerate.
3. Buyer purchase history generator works in dry-run and `--write` modes.
4. Category demand history generator works in dry-run and `--write` modes.
5. V5 forecast generator still produces Markdown, HTML, and JSON reports.
6. V5 generator can write `forecast_candidates.csv` when explicitly asked.
7. Forecast backtest script works in dry-run and `--write` modes.
8. Unit tests cover proof gates, mock filtering, research-only lanes, and low-competition signal detection.
9. Reports do not include mock/fixture/zero-score placeholder rows.
10. Reports do not recommend external action for RAW_LEAD, MISSING, PARTIAL, MARKETPLACE_MASKED, or PUBLIC_LISTING_ONLY rows.
11. `validate_register_schemas.py` passes.
12. `validate_case_readiness.py --all` passes with expected business blockers only.
13. No external action was performed.
14. No credential/token/private browser/session data was added to docs, data, reports, manifest, or examples.

---

## 7. Historical Data Addendum

Historical data should be added before any ML-style prediction. Codex must read and incorporate:

```text
docs/plans/2026-07-02-v5-historical-data-ingestion-addendum.md
```

That addendum adds the historical-data lane:

```text
historical tender notices
historical awards / winners / bidder counts / L1-L2 prices where available
historical buyer/category stats
historical competition signals
historical import demand for export lanes
```

The key rule remains: historical data improves forecast confidence, but it never bypasses proof gates. Historical demand alone cannot make a live case bid-ready, and import-market demand alone cannot make an export RFQ verified.

---

## 8. What Codex Must Not Build Yet

Do not implement these in this round:

```text
custom MCP server
Neo4j/Postgres/graph database migration
ML model or LLM prediction service
20-agent Hermes profile expansion
automated supplier outreach
automated buyer quote sending
portal-login automation
bid submission automation
final HSN/ITC-HS/origin/tax/legal claim automation
```

Reason: the current priority is evidence-backed deterministic forecasting and proof-aware founder recommendations.

---

## 9. Recommended Commit Sequence

If using git, commit in small steps:

```bash
git add config/schemas data data/examples
git commit -m "feat: add V5 forecast projection schemas"

git add scripts/build_buyer_purchase_history.py scripts/tests/test_v5_demand_forecast_low_competition.py
git commit -m "feat: add buyer repeat forecast projection"

git add scripts/build_category_demand_history.py
git commit -m "feat: add category demand history projection"

git add scripts/generate_v5_demand_forecast_low_competition.py
git commit -m "feat: persist V5 forecast candidates"

git add scripts/backtest_v5_demand_forecasts.py
git commit -m "feat: add V5 forecast backtesting"

git add docs/V5_DEMAND_FORECASTING_LOW_COMPETITION_RUNBOOK.md manifest.json README.md config/hermes_cron.yaml
git commit -m "docs: document V5 demand forecasting operations"
```

Do not commit generated reports unless the repo already tracks outputs intentionally.

---

## 10. Final Codex Handoff Prompt

Use this as the exact prompt to Codex:

```text
You are Codex working inside /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system.

Implement docs/plans/2026-07-02-v5-demand-forecasting-low-competition-codex-implementation-plan.md task-by-task.

Rules:
- Keep TenderOS v4.1 as the kernel; do not rebuild.
- Do not perform external actions, portal login, outreach, bid/RFQ submission, payment, DSC use, or final price/compliance/origin commitments.
- Keep everything deterministic and local-first.
- Prefer Python stdlib; avoid new dependencies.
- Add schemas, projection CSVs, generators, tests, backtesting, runbook, manifest pointers.
- Run the verification commands in Task 14.
- Report exact files changed, commands run, outputs, and any blockers.
```

---

## 11. Founder Summary

This implementation converts the current prototype from “one report script” into a real V5 intelligence subsystem:

```text
Demand signals → repeat/category forecasts → low-competition candidates → proof gaps → safe next action → backtest learning
```

It should make TenderOS better at answering:

```text
What should I look at today?
Why this order?
Is it real or just a lead?
What proof is missing?
Is the buyer/category likely to repeat?
Is competition likely lower than usual?
What is the safest next internal move?
```
