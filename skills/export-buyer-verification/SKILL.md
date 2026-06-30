# Export Buyer Verification

Use this skill before treating an export RFQ buyer as credible.

## Inputs
- buyer name, country, source URL, RFQ text
- `data/master_cases.csv`
- available public business registry or source evidence

## Procedure
1. Confirm `case_id` and workflow `EXPORT`.
2. Verify source provenance and buyer identity signals.
3. Score credibility conservatively.
4. Flag missing business registration, suspicious payment terms, unverifiable buyer details, or inconsistent contact channels.
5. Update the case by `case_id` with draft credibility notes.
6. Append `data/agent_run_log.csv`.

## Stop Conditions
- buyer cannot be verified from available public/source evidence
- source requires login, payment, CAPTCHA bypass, or restricted access
- payment or identity risk is high

## Must Not
- claim buyer is verified without evidence
- send buyer replies
- accept payment terms
- promise price or delivery

## Sources
Cite public registry pages, RFQ pages, platform pages, and local files used.
