# V5 Demand Forecasting + Low-Competition Engine

Created: 2026-07-02
Owner system: Tender Export OS v4.1 runtime
Status: V5 Module 1 specification + first deterministic report generator

## Short verdict

This is the first V5 intelligence module. It should sit before Western expansion, dashboards, custom MCP, or a large agent factory.

The engine’s job is not to say “here are more tenders.” Its job is:

> Predict where demand is likely to appear, identify low-competition orders early, prove only the real ones, kill weak leads, and give the founder 1–2 exact actions per day.

## Runtime anchors already present

Current TenderOS already has usable primitives:

- `data/demand_research.csv` — category/country/source demand research lanes.
- `outputs/buyer_demand/` — verified buyer demand briefs.
- `outputs/demand_signals/` — active demand signal digests.
- `scripts/low_competition_order_radar.py` — existing low-competition radar.
- `config/low_competition_keywords.yaml` — retender/corrigenda/AMC/boring-order signals.
- `config/low_competition_scoring.yaml` — first scoring rules.
- `config/low_competition_categories.yaml` — beginner-friendly categories.
- `data/master_cases.csv` — active GOV/EXPORT cases and proof fields.

This module extends those; it does not replace them.

## Non-negotiable boundary

Forecasting never creates a bid-ready case by itself.

Flow must remain:

```text
Forecast signal
→ watchlist / research lane
→ source proof
→ document or RFQ proof
→ fast kill
→ deep read
→ supplier proof
→ pricing proof
→ approval card
→ external action only after approval
```

Forecast confidence is decision support, not a guarantee.

## What demand forecasting means here

Demand forecasting means evidence-backed prediction over 7 / 30 / 60 / 90 day horizons using:

- repeat buyer behavior
- category repetition
- source reliability
- RFQ / tender proof level
- tender cadence
- retender/corrigenda/date-extension signals
- supplier readiness
- seasonality / budget-cycle proxies where available
- historical award/outcome data when available

It does **not** mean magical win prediction. Win prediction requires award history, bidder count, L1 prices, competitors, supplier proof, and outcomes.

## Forecast layers

### 1. Government Buyer Repeat Forecast

Answers:

- Which buyers are likely to buy again?
- What categories repeat?
- What size orders do they issue?
- What eligibility/EMD/payment friction is typical?
- Which buyers are beginner-friendly?

Required projection fields:

```text
buyer_name
department
category
past_tender_count
similar_category_awards
last_seen_date
average_order_value
average_emd
buyer_repeat_score
next_likely_purchase_window
forecast_confidence
```

### 2. Category Demand Forecast

Answers:

- Which boring categories are repeatedly demanded?
- Which are rising?
- Which are supplier-ready?
- Which are crowded or margin-killing?

First priority categories:

```text
office stationery / printing / conference material
RO / water purifier AMC / filter replacement
digitisation / scanning / record management
cleaning / housekeeping consumables
printer toner / cartridge / AMC
linen / bedsheets / towels
pest control
badly titled operational consumables
```

### 3. Export Demand Forecast

Answers:

- Which product-country-buyer-source lanes are promising?
- Which are only research lanes?
- Which have verified buyer-specific RFQ proof?
- Which are blocked by compliance, certificates, tariff, or buyer proof?

Current V5 wedge:

```text
Primary: premium Indian handicrafts / small décor / artisan textiles / gifting
Markets: UK, USA, Canada, Germany
Second: compliant spices / condiments into UK + USA/Canada importer channels
Watchlist: engineering parts / fasteners / fittings only with exact RFQ + supplier certificates
```

## Low-competition detection

Low competition should be a scored signal, not a promise.

### Strong positive signals

```text
retender / re-tender / recalled tender
date extension / corrigendum / revised BOQ
shortfall of bidders / single bid received
AMC / maintenance / repair / refilling / replacement
rate contract / local purchase
badly titled: misc item, supply of item, material required
boring consumables: stationery, toner, linen, bins, filters
local delivery + low EMD + no OEM + no past-experience requirement
```

### Strong negative signals

```text
manufacturer-only / OEM required
past government experience mandatory
high turnover requirement
high EMD / PBG / long payment cycle
short deadline
remote delivery / impossible SLA
unclear BOQ or missing documents
regulated category without certificates
crowded commodity keywords: laptops, CCTV, manpower, civil work, solar plant
```

## Scoring model

### Demand Forecast Score

```text
30% repeat buyer/category pattern
20% source reliability
15% evidence density / proof level
15% low-competition signal
10% supplier readiness
10% actionability / deadline window
```

### Low-Competition Opportunity Score

```text
25% low-competition keyword/situation signal
20% beginner-friendly category fit
15% supplier readiness
15% low capital / low EMD
10% document / BOQ clarity
10% no visible hard eligibility blocker
5% repeat-buyer or learning value
```

### Export Forecast Score

```text
25% product-country demand signal
20% buyer/RFQ proof
15% supplier readiness
15% compliance readiness
15% landed margin potential
10% repeatability
```

## Confidence levels

```text
HIGH
- buyer-specific source/RFQ/tender evidence exists
- source reliability strong
- proof gaps explicit
- supplier/pricing path known

MEDIUM
- strong research lane or public listing evidence
- buyer/source visible but documents or proof incomplete

LOW
- generic market thesis only
- masked marketplace lead
- missing buyer identity, documents, quantity, or deadline
```

## Output contract

Daily report must include:

1. Top predicted demand lanes.
2. Top low-competition active orders.
3. Verified RFQ/tender demand vs research-only demand.
4. Why each item surfaced.
5. Proof gaps.
6. Kill/watch reasons.
7. Next safe action.
8. Whether owner approval is required before any external action.

Founder-facing wording:

```text
Here are the 1–2 demand/low-competition moves worth your time today.
Here is why the rest are not ready.
Here is what proof is missing.
Here is the exact internal next action.
No external action has been taken.
```

## First implementation created

Initial deterministic generator:

```text
scripts/generate_v5_demand_forecast_low_competition.py
```

Outputs:

```text
outputs/demand_forecasting/v5_demand_forecast_low_competition_YYYYMMDD.md
outputs/demand_forecasting/v5_demand_forecast_low_competition_YYYYMMDD.html
outputs/demand_forecasting/v5_demand_forecast_low_competition_YYYYMMDD.json
```

It reads current runtime data and the latest low-competition radar output. It performs internal analysis only; it never sends, logs into portals, submits, pays, uses DSC, or commits prices/compliance/origin.

## Build sequence from here

### Phase 1 — Report layer

- Generate daily V5 forecast + low-competition report from existing data.
- Keep it separate from current owner brief for shadow-running.

### Phase 2 — Proof-quality hardening

- Public listing price must not count as supplier-specific quote proof.
- `PRICING_READY` / A+ gates require supplier-specific quote evidence.

### Phase 3 — Forecast projections

Add projections from events and cases:

```text
data/buyer_purchase_history.csv
data/category_demand_history.csv
data/forecast_candidates.csv
data/forecast_backtests.csv
```

### Phase 4 — Backtesting

Every evening/weekly:

- Did forecasted lanes produce real cases?
- Which sources created noise?
- Which low-competition signals were false positives?
- Which categories should be promoted, demoted, or killed?

### Phase 5 — Integration into daily brief

Only after one week of shadow-run evidence, merge the top section into the morning owner report.

## Acceptance gates

Before this module becomes part of the main brief:

- Existing validators pass.
- Generated report links every claim to case/source/research row where possible.
- Low-competition candidates with `PUBLIC_LISTING_ONLY` remain not bid-ready.
- No forecast item bypasses proof/approval gates.
- The module reduces owner decision time or weak-case noise during at least one week of shadow runs.

## Recommended daily action rule

The report should always end with one action:

```text
Recommended action: deep-read/prove the highest-scoring low-competition case whose proof gap is smallest.
```
