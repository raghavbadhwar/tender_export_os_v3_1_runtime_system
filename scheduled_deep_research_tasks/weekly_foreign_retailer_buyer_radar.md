# Weekly Foreign Retailer Buyer Radar

Use `templates/chatgpt/buyer_market_deep_research_prompt.md`.

Default pilot:

- Category: Handicrafts and Artisan Products (`EXP-CRAFT-001`)
- Markets: United Kingdom, Germany, Canada, Australia, United States
- Target types: ethical/fair-trade retailers, homeware retailers, importers/distributors, museum/design shops, corporate gifting buyers
- Target count: 5–10 evidence-backed companies; quality over quantity

Return the structured JSON appendix. Hermes stages it with:

```bash
.venv/bin/python scripts/stage_buyer_market_research.py --input <saved-return.json> --dry-run
.venv/bin/python scripts/stage_buyer_market_research.py --input <saved-return.json> --stage
```

No outreach is sent by Deep Research or by staging. Every draft remains owner-approval-gated.
