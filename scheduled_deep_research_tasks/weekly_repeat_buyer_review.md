# Scheduled Deep Research Task: Weekly Repeat Buyer Review

Run this as ChatGPT Scheduled Deep Research.

Timezone: Asia/Kolkata. Use the run date in IST as today's local date.

Produce an HTML-style ranked report in chat with source links/citations. Do not mutate repo state. Do not approve actions. Do not send messages. Do not submit bids, upload documents, pay, use DSC, commit final price/delivery/payment terms, certify compliance, confirm HSN/ITC-HS, or claim origin.

Answer: Which buyers repeatedly buy things we can fulfil?

Identify strong leads for later staging, clearly mark evidence level, distinguish `lead` from `case candidate`, mark whether each signal is only a public listing, and include the next owner action. Recommend which buyer/source/category signals should enter the repo for operational capture.

## Research Scope

Find repeat institutional buyers across public procurement pages, award summaries, tender histories, and public notices. Focus on buyers who repeatedly buy low-compliance, supplier-ready, boring operational items.

## Output Sections

```html
<h1>Weekly Repeat Buyer Review - [TODAY IST]</h1>
<section id="executive-summary">...</section>
<section id="ranked-repeat-buyers">...</section>
<section id="repeat-categories">...</section>
<section id="buyer-risk-notes">...</section>
<section id="sources-to-monitor">...</section>
<section id="leads-to-stage-into-tender-export-os">...</section>
<section id="recommended-owner-action">...</section>
```

## Buyer Card Fields

- `buyer_name`
- `buyer_type`
- `public_source_urls`
- `repeat_categories`
- `observed_purchase_pattern`
- `evidence_level`
- `why_this_buyer_matters`
- `risks`
- `missing_info`
- `suggested_repo_action`

Distinguish lead from case candidate. `PUBLIC_LISTING_ONLY` remains a lead. Recommend repo staging only for buyer/source/category watches that Python can monitor later.
