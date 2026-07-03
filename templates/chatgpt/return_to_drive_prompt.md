# Prompt: Return ChatGPT Report To Drive Bridge

You are ChatGPT Project returning a bounded research packet to Tender Export OS.

Write the completed report back to:

`Tender Export OS - Knowledge Bus/08_ChatGPT_Bridge/02_From_ChatGPT/[RESEARCH_REPORT_ID]/`

Return files:

1. `research_report.md` — concise findings with citations and uncertainty.
2. `leads_appendix.json` — structured JSON with a top-level `leads` array compatible with `config/schemas/deep_research_lead_schema.yaml`.
3. `source_receipts.md` — source URL list, access blockers, and notes about unavailable documents.

Before returning, verify:

- every lead has all required staging fields
- every factual claim has a citation or an uncertainty note
- no recommended repo action is forbidden
- `PUBLIC_LISTING_ONLY` leads are marked lead/watch/manual-source-check only
- no output claims final price, final delivery, final origin, final HS/HTS/ITC-HS, final tariff, final compliance, or legal certainty
- no instruction asks Hermes, Codex, Python, Drive, or the owner to perform external sends, submissions, uploads, payments, DSC use, supplier commitments, buyer commitments, or register mutation

End the report with this exact staging note:

```text
Repo staging instruction: Save leads_appendix.json locally, then run:
python3 scripts/stage_deep_research_leads.py --input <saved_leads_appendix.json> --dry-run

This ChatGPT return is advisory only. It is not canonical state and did not execute external actions.
```
