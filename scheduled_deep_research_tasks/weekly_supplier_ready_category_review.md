# Scheduled Deep Research Task: Weekly Supplier-Ready Category Review

Run this as ChatGPT Scheduled Deep Research.

Timezone: Asia/Kolkata. Use the run date in IST as today's local date.

Produce an HTML-style ranked report in chat with source links/citations. Do not mutate repo state. Do not approve actions. Do not send messages. Do not submit bids, upload documents, pay, use DSC, commit final price/delivery/payment terms, certify compliance, confirm HSN/ITC-HS, or claim origin.

Answer: Which categories do we already have supplier readiness for, and which tenders should we watch?

Identify strong leads for later staging, clearly mark evidence level, distinguish `lead` from `case candidate`, mark whether each signal is only a public listing, and include the next owner action. Recommend which category/source/keyword watches should enter the repo for operational capture.

## Research Scope

Use broad discovery and synthesis to identify categories that are likely:

- low-compliance
- locally fulfillable
- repeat purchased by institutions
- compatible with existing supplier readiness
- visible on known public sources
- likely to produce low-competition or under-seen tenders

Do not scrape or operationally capture. Recommend categories and source watches only.

## Output Sections

```html
<h1>Weekly Supplier-Ready Category Review - [TODAY IST]</h1>
<section id="executive-summary">...</section>
<section id="ranked-supplier-ready-categories">...</section>
<section id="watch-sources-and-keywords">...</section>
<section id="sample-public-leads">...</section>
<section id="fulfilment-risks">...</section>
<section id="leads-to-stage-into-tender-export-os">...</section>
<section id="recommended-owner-action">...</section>
```

## Category Card Fields

- `category`
- `why_supplier_ready`
- `likely_sources`
- `keywords_to_watch`
- `public_source_urls`
- `evidence_level`
- `fulfilment_hypothesis`
- `risks`
- `missing_info`
- `suggested_repo_action`

Use `CREATE_RADAR_LEAD` only for specific source/keyword watches. Use `CREATE_CASE_CANDIDATE_AFTER_EVIDENCE` only when documents or equivalent evidence exist.
