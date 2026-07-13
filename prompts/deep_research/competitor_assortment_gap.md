# Deep Research Packet — Competitor Assortment-Gap Study

Use this packet to identify an evidence-backed assortment or positioning gap
for **[CATEGORY]** across **[TARGET MARKET]**. It should produce a limited
list of leads that deserve later operational validation, not a claim that a
buyer wants a product.

## Scope

- Compare no more than **10** public competitor, retailer, distributor, or
  marketplace catalogues.
- Distinguish observed facts from hypotheses. For each gap, state the
  evidence, counter-evidence, price/positioning uncertainty, and what a
  supplier/compliance check would still need to prove.
- Prefer primary company catalogues and product pages. Cite a trade or market
  report only as supporting context, not as proof of a company assortment.

## Hard boundaries

- Do not copy protected catalogue content beyond short factual descriptions.
- Do not infer demand, sales, unit economics, customer lists, availability, or
  a competitor's sourcing arrangement from a public listing.
- Do not contact companies or mutate registers, proposals, pricing, outreach,
  or the event ledger.
- `PUBLIC_LISTING_ONLY` remains an advisory lead and may not become a bid-ready
  case through this packet.

## Required return

Return a concise cited analysis followed by a JSON block compatible with
`config/schemas/deep_research_lead_schema.yaml`:

```json
{
  "research_report_id": "DR-GAP-[CATEGORY]-[MARKET]-YYYYMMDD",
  "research_type": "competitor_assortment_gap",
  "scope": {"category": "[CATEGORY]", "market": "[TARGET MARKET]", "max_sources": 10},
  "leads": [
    {
      "lead_id": "DR-GAP-[CATEGORY]-[MARKET]-001",
      "research_report_id": "DR-GAP-[CATEGORY]-[MARKET]-YYYYMMDD",
      "source_url": "https://public-competitor-or-market-source.example",
      "source_name": "Named public source",
      "buyer_name": "Named company if an operational buyer target exists, otherwise UNKNOWN",
      "buyer_type": "RETAILER | DISTRIBUTOR | RESEARCH",
      "workflow_type": "EXPORT",
      "category": "[CATEGORY]",
      "lead_title": "Observed assortment gap with a clear validation path",
      "location": "[TARGET MARKET]",
      "deadline": "UNKNOWN",
      "evidence_level": "PUBLIC_LISTING_ONLY",
      "why_interesting": "Observed product/assortment fact and the bounded gap hypothesis",
      "why_low_competition": "Why the gap may be less crowded, plus contrary evidence",
      "fulfilment_hypothesis": "What supplier, price, compliance, packing, and logistics facts must later be proven",
      "risks": ["Competition, IP, market-fit, evidence, or regulatory risk"],
      "missing_info": ["Specific proof gap"],
      "recommended_repo_action": "WATCH",
      "owner_review_required": true,
      "source_citations": ["https://public-competitor-or-market-source.example"],
      "observed_assortment": ["Short factual observations"],
      "counter_evidence": ["Observed reasons the gap may not be real"]
    }
  ]
}
```

If a gap cannot be tied to a cited public source, omit it rather than filling
it with a plausible-sounding inference.

## Staging instruction

Save the JSON locally and validate it without direct register mutation:

```bash
.venv/bin/python scripts/stage_deep_research_leads.py --input <saved-packet.json> --dry-run
```

Only verified operational evidence can advance a lead into a later capture,
supplier, compliance, or approval workflow.

Do not mutate any business register from this research task. No external action
is authorized by this packet.
