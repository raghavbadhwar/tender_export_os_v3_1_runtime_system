# Deep Research to Repo Staging

ChatGPT Scheduled Deep Research returns are advisory until reviewed. This staging contract defines what can be copied into Tender Export OS and what must stay outside operational state.

## Source

Deep Research outputs may be manually saved as:

- structured JSON lead files
- Markdown reports with a separate structured lead appendix
- Drive bridge returns under `08_ChatGPT_Bridge/02_From_ChatGPT/`

The staging helper does not browse the web. It ingests saved output only.

## Required Lead Fields

```yaml
lead_id:
research_report_id:
source_url:
source_name:
buyer_name:
buyer_type:
workflow_type:
category:
lead_title:
location:
deadline:
evidence_level:
why_interesting:
why_low_competition:
fulfilment_hypothesis:
risks:
missing_info:
recommended_repo_action:
owner_review_required:
```

## Allowed Recommended Repo Actions

- `IGNORE`
- `WATCH`
- `MANUAL_SOURCE_CHECK`
- `MANUAL_DOCUMENT_UPLOAD`
- `CREATE_RADAR_LEAD`
- `CREATE_CASE_CANDIDATE_AFTER_EVIDENCE`

## Forbidden Actions

Deep Research returns and staged leads must never request or execute:

- `SUBMIT`
- `SEND_QUOTE`
- `PAY`
- `UPLOAD`
- `USE_DSC`
- `COMMIT_PRICE`
- `CERTIFY_COMPLIANCE`

They also must not approve actions, send messages, submit bids, upload documents, use DSC, pay, confirm final price, confirm final compliance, confirm HSN/ITC-HS, or claim country of origin.

## Evidence Levels

- `PUBLIC_LISTING_ONLY`: lead only. Not bid-ready. Not Deep Read-ready unless owner requests manual source check.
- `DETAIL_PAGE_READ`: stronger lead, still not bid-ready without operational evidence.
- `DOCUMENTS_DISCOVERED`: operational capture target.
- `DOCUMENTS_DOWNLOADED`: possible case candidate after repo validation.
- `MANUAL_UPLOAD_REQUIRED`: owner or operator must upload documents before Deep Read.
- `BLOCKED_LOGIN_REQUIRED`, `BLOCKED_CAPTCHA`, `BLOCKED_PAYWALL`: blocker/manual lane.

## Staging Procedure

Use:

```bash
python3 scripts/stage_deep_research_leads.py --input <file> --dry-run
python3 scripts/stage_deep_research_leads.py --input <file> --stage
```

Default behavior is dry-run validation and staging-output generation only. It does not mutate `data/master_cases.csv`.

When `--stage` is used, the script writes a reviewed staging package under:

```text
outputs/deep_research_staging/
```

and appends a `deep_research.leads_staged` event.

## Promotion Rules

Deep Research discovers. Python captures/proves. The repo remembers. Hermes routes/approves. The owner decides external commitments.

- A staged lead can become a source-watch item.
- A staged lead can become a manual source-check request.
- A staged lead can become a manual document-upload request.
- A staged lead can become a radar lead only after dedupe and evidence review.
- A staged lead can become a case candidate only after operational evidence exists.

## Low-Competition Orders

For low-competition orders:

1. Deep Research finds the low-competition thesis and source/category signals.
2. The staging helper validates the returned lead fields.
3. Python/Playwright checks known sources and captures evidence where allowed.
4. Radar/Fast Kill/Deep Read advance only evidence-backed records.

`PUBLIC_LISTING_ONLY = lead, not bid-ready case.`
