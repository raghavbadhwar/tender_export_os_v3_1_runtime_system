# Scheduled Deep Research Task: Daily Low-Competition Order Radar

Run this as ChatGPT Scheduled Deep Research.

Timezone: Asia/Kolkata. Use the run date in IST as today's local date.

Produce an HTML-style report in chat with source links/citations. Do not mutate repo state. Do not approve actions. Do not send messages. Do not submit bids, upload documents, pay, use DSC, commit final price/delivery/payment terms, certify compliance, confirm HSN/ITC-HS, or claim origin.

Your role is broad discovery and synthesis. Identify strong leads for later operational capture by Tender Export OS. Distinguish a lead from a case candidate. Recommend which leads should enter the repo for staging, but do not create cases.

Every lead must clearly mark evidence level, whether it is only a public listing, the next owner action, and whether the correct repo action is `WATCH`, `MANUAL_SOURCE_CHECK`, `MANUAL_DOCUMENT_UPLOAD`, `CREATE_RADAR_LEAD`, or `CREATE_CASE_CANDIDATE_AFTER_EVIDENCE`.

## Search Focus

Find legally public/accessibly discoverable low-competition opportunities, not hidden, restricted, paywalled, or illegal orders.

Search for:

- retenders, re-tenders, cancelled and recalled tenders
- corrigenda, date extensions, revised BOQs, technical bid extensions
- low EMD, clear BOQ, local/simple delivery
- repeat buyers and boring institutional orders
- badly titled tenders
- AMC, repair, maintenance
- RO/water filters
- record scanning, digitisation, data entry, MIS dashboard
- pest control, cleaning supplies, stationery, printing, toner, printer AMC
- linen, hospital non-medical consumables
- university, hospital, municipal, and district procurement pages

## Evidence Rules

- `PUBLIC_LISTING_ONLY` = lead, not bid-ready case.
- `DETAIL_PAGE_READ` = stronger lead, still not bid-ready unless documents/terms are clear.
- `DOCUMENTS_DISCOVERED` = possible operational capture target.
- `DOCUMENTS_DOWNLOADED` or manually uploaded evidence = possible case candidate.
- Never treat a public listing, marketplace teaser, or aggregator snippet as a bid-ready case.

## Output Sections

```html
<h1>Daily Low-Competition Order Radar - [TODAY IST]</h1>
<section id="executive-summary">...</section>
<section id="best-opportunities-today">...</section>
<section id="retender-corrigenda-date-extension-alerts">...</section>
<section id="repeat-buyer-signals">...</section>
<section id="supplier-ready-category-signals">...</section>
<section id="under-seen-source-discoveries">...</section>
<section id="avoid-list">...</section>
<section id="leads-to-stage-into-tender-export-os">...</section>
<section id="recommended-owner-action">...</section>
```

## Lead Card Fields

For each lead card include:

- `lead_title`
- `source_url`
- `buyer`
- `buyer_type`
- `category`
- `location`
- `deadline_if_visible`
- `evidence_level`
- `why_low_competition`
- `why_easy_or_not_easy_to_fulfil`
- `risks`
- `missing_info`
- `suggested_repo_action`

Allowed `suggested_repo_action` values:

- `IGNORE`
- `WATCH`
- `MANUAL_SOURCE_CHECK`
- `MANUAL_DOCUMENT_UPLOAD`
- `CREATE_RADAR_LEAD`
- `CREATE_CASE_CANDIDATE_AFTER_EVIDENCE`

Do not use `SUBMIT`, `SEND_QUOTE`, `PAY`, `UPLOAD`, `USE_DSC`, `COMMIT_PRICE`, or `CERTIFY_COMPLIANCE`.

## Staging Guidance

Recommend staging only when there is a source URL and enough public evidence for Python/Playwright to prove or reject the lead later. Mark weak items as `WATCH` or `MANUAL_SOURCE_CHECK`.
