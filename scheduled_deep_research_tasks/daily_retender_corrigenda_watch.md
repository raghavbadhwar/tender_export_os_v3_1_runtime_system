# Scheduled Deep Research Task: Daily Retender/Corrigenda Watch

Run this as ChatGPT Scheduled Deep Research.

Timezone: Asia/Kolkata. Use the run date in IST as today's local date.

Produce an HTML-style report in chat with source links/citations. Do not mutate repo state. Do not approve actions. Do not send messages. Do not submit bids, upload documents, pay, use DSC, commit final price/delivery/payment terms, certify compliance, confirm HSN/ITC-HS, or claim origin.

Your role is to discover and reason over public retender/corrigenda/date-extension patterns. Python/Playwright later performs exact capture from known sources and document parsing where allowed.

Identify strong leads for later staging, clearly mark evidence level, distinguish `lead` from `case candidate`, and include the next owner action for every alert. Recommend repo staging only when operational capture can later prove or reject the lead from a specific source.

## Search Focus

Look for:

- retender
- re-tender
- cancelled and recalled
- corrigendum
- amendment
- date extension
- BOQ revised
- technical bid extended
- single bid received
- shortfall of bidders

Prioritize boring institutional categories and source pages where competition may be lower because the earlier tender failed or changed.

## Evidence Rules

- `PUBLIC_LISTING_ONLY` = lead, not bid-ready case.
- `DOCUMENTS_DISCOVERED` or `DETAIL_PAGE_READ` = operational capture target.
- `DOCUMENTS_DOWNLOADED` or manually uploaded evidence = possible case candidate after repo staging.

## Output Sections

```html
<h1>Daily Retender/Corrigenda Watch - [TODAY IST]</h1>
<section id="executive-summary">...</section>
<section id="highest-priority-alerts">...</section>
<section id="date-extension-alerts">...</section>
<section id="boq-or-scope-change-alerts">...</section>
<section id="low-competition-rationale">...</section>
<section id="leads-to-stage-into-tender-export-os">...</section>
<section id="recommended-owner-action">...</section>
```

## Alert Card Fields

For each alert include:

- `old_or_related_tender`
- `new_source_url`
- `buyer`
- `change_type`
- `old_deadline_if_known`
- `new_deadline_if_visible`
- `evidence_level`
- `why_competition_may_be_lower`
- `what_to_recheck`
- `recommended_owner_action`
- `suggested_repo_action`

Allowed `suggested_repo_action` values: `IGNORE`, `WATCH`, `MANUAL_SOURCE_CHECK`, `MANUAL_DOCUMENT_UPLOAD`, `CREATE_RADAR_LEAD`, `CREATE_CASE_CANDIDATE_AFTER_EVIDENCE`.

No automatic repo mutation. Recommend staging only when the source URL is specific enough for operational capture.
