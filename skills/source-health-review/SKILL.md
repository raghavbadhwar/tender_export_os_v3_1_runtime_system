# Source Health Review

Use this skill for source reliability checks.

## Health States
- Working
- Needs Login
- Paywalled
- Low Relevance
- Broken
- Manual Check Required
- Blocked by CAPTCHA
- Restricted / Do Not Scrape

## Procedure
1. Check configured sources only within allowed access.
2. Record status in `data/source_health.csv`.
3. Preserve source URL and evidence notes.
4. Surface repeated failures in owner brief.
5. Recommend replacement or lower cadence for low-relevance sources.

## Must Not
- bypass CAPTCHA
- bypass login/paywall restrictions
- scrape restricted sources
- fabricate lead counts or source availability
