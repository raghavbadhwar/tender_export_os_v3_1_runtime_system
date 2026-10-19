# GOV Tender Fast Kill

Use this skill when screening a government tender before deep read.

## Inputs
- `data/master_cases.csv`
- `config/kill_rules.yaml`
- `config/scoring_weights.yaml`
- `config/categories.yaml`
- source URL or tender summary

## Procedure
1. Identify `case_id` and confirm workflow is `GOV`.
2. Apply kill rules in order.
3. Never reject only because data is missing.
4. If a rule is ambiguous, set status to `WATCHLIST` and flag human review.
5. If rejected, write `outputs/case_reports/<case_id>/no_go_reason_note.txt`.
6. Update `data/master_cases.csv` only by `case_id`.
7. Append `data/agent_run_log.csv`.

## Stop Conditions
- source is login-required, paywalled, CAPTCHA-blocked, or restricted
- eligibility is ambiguous
- required data is missing

## Must Not
- fabricate eligibility, certifications, prices, buyer verification, or rejection reasons
- proceed to supplier outreach
- submit, upload, pay, use DSC, or contact external parties

## Sources
Cite every tender page, PDF, corrigendum, and config file used.
