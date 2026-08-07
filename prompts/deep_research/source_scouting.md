# Deep Research Packet — Source and Signal Scouting

Use this packet to discover public sources, buyer signals, tender-like demand
sources, category watchlists, and repeatable monitoring opportunities for
**[CATEGORY / WORKFLOW]**. The goal is a small, cited source map—not a bulk
scrape, a live portal interaction, or automatic case creation.

## Scope

- Return no more than **15** source or signal leads.
- Classify each source as official public, company public, trade/association,
  marketplace, secondary media, login-required, or paywalled.
- State the exact signal to monitor, likely refresh cadence, public evidence
  available, access blocker, and next deterministic capture check.
- Include source-quality risks: staleness, aggregation, duplicate coverage,
  terms/robots uncertainty, or potential prompt-injection content.

## Hard boundaries

- Do not log in, pay, scrape around a paywall, bypass a CAPTCHA, submit a
  form, or create browser sessions.
- Do not write source configuration, cases, buyer records, supplier records,
  pricing, approval cards, or ledger events.
- Public source discovery is advisory. A source needs an owner-reviewed,
  robots-compliant, read-only capture design before any repeatable automation.

## Required return

Return a concise cited source map followed by a JSON block compatible with
`config/schemas/deep_research_lead_schema.yaml`:

```json
{
  "research_report_id": "DR-SOURCES-[WORKFLOW]-[CATEGORY]-YYYYMMDD",
  "research_type": "source_scouting",
  "scope": {"workflow": "GOV | EXPORT | SUPPLIER | RESEARCH", "category": "[CATEGORY]", "max_sources": 15},
  "leads": [
    {
      "lead_id": "DR-SOURCES-[WORKFLOW]-001",
      "research_report_id": "DR-SOURCES-[WORKFLOW]-[CATEGORY]-YYYYMMDD",
      "source_url": "https://public-source.example",
      "source_name": "Named source",
      "buyer_name": "UNKNOWN",
      "buyer_type": "RESEARCH",
      "workflow_type": "RESEARCH",
      "category": "[CATEGORY]",
      "lead_title": "Named source and its exact monitorable signal",
      "location": "Country, state, or global scope",
      "deadline": "UNKNOWN",
      "evidence_level": "PUBLIC_LISTING_ONLY | BLOCKED_LOGIN_REQUIRED | BLOCKED_PAYWALL | BLOCKED_CAPTCHA",
      "why_interesting": "What observable signal the source can contribute",
      "why_low_competition": "Why it may reveal an under-watched source/category, with caveats",
      "fulfilment_hypothesis": "The later deterministic capture or manual-proof route—not a commercial commitment",
      "risks": ["robots, terms, freshness, blocker, duplication, or source-quality risks"],
      "missing_info": ["Proof needed before source activation"],
      "recommended_repo_action": "MANUAL_SOURCE_CHECK",
      "owner_review_required": true,
      "source_citations": ["https://public-source.example"],
      "source_access_class": "OFFICIAL_PUBLIC | PUBLIC | LOGIN_REQUIRED | PAYWALLED",
      "proposed_capture_cadence": "daily | weekly | monthly | manual"
    }
  ]
}
```

Use a blocker evidence level when a source is blocked; do not quietly replace
it with a supposedly equivalent aggregator or an unsupported access path.

## Staging instruction

Save the JSON locally and validate it before any owner review or source-design
work:

```bash
.venv/bin/python scripts/stage_deep_research_leads.py --input <saved-packet.json> --dry-run
```

This command stages a review artifact only. It does not authorize a source
adapter, register mutation, browser activity, or external action.

Do not mutate any business register from this research task. No external action
is authorized by this packet.
