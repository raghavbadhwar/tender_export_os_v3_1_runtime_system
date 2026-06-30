# Pricing Proof

Use this skill when preparing draft pricing for a case.

## Inputs
- `data/quote_master.csv`
- `data/master_cases.csv`
- deep read report
- supplier shortlist

## Preconditions
- Minimum 2 quote proofs are required for final pricing.
- If fewer than 2 quote proofs exist, stop and request more quotes.

## GOV Waterfall
Supplier base cost + GST + freight + packaging + installation + warranty reserve + documentation + EMD/BG/working capital + payment delay buffer + penalty risk buffer + margin = final bid price.

## EXPORT Waterfall
Supplier base price + packaging + inland freight + CHA/customs docs + port handling + international freight + insurance if CIF + bank charges + inspection/certification + sample cost + currency buffer + risk buffer + margin = EXW/FOB/CIF quote.

## Procedure
1. Confirm `case_id` and workflow.
2. Verify quote proof count.
3. Build conservative, recommended, and aggressive scenarios.
4. Mark every assumption and uncertain cost line.
5. Save `outputs/case_reports/<case_id>/pricing_<case_id>.md`.
6. Update `price_ready`/`pricing_done` only if evidence supports it.
7. Append `data/agent_run_log.csv`.

## Must Not
- commit final price
- send quotation or bid
- hide margin below threshold
- fabricate freight, insurance, GST, duties, or supplier prices
