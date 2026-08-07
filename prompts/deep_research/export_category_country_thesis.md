# Deep Research Packet — Export Category × Country Thesis

Use this packet for an evidence-led decision about whether **[CATEGORY]** has a
credible export opening in **[COUNTRY]**. It is a research request, not an
instruction to contact anyone, create a business record, or make a commercial
claim.

## Scope

- Research window: the most recent 24 months unless a source is clearly older
  and still authoritative.
- Return at most **12** named buyer, channel, procurement, or source leads.
- Prefer official trade, customs, retailer, importer, buyer, and company
  sources. Label secondary sources as secondary.
- Look for demand, price positioning, distribution channels, import friction,
  competitor density, product/packaging fit, and a realistic India fulfilment
  hypothesis.
- Seek disconfirming evidence as actively as confirming evidence.

## Hard boundaries

- Do not send messages, submit forms, sign up, purchase data, use a login,
  bypass a paywall/CAPTCHA, or infer a buyer's intent.
- A catalogue, assortment, directory listing, or contact page is not an RFQ,
  order, supplier approval, or confirmed demand.
- Do not set `recommended_repo_action` to `CREATE_CASE_CANDIDATE_AFTER_EVIDENCE`
  from this research packet. Use `WATCH`, `MANUAL_SOURCE_CHECK`, or
  `MANUAL_DOCUMENT_UPLOAD` only.
- Do not write or mutate `data/master_cases.csv`, buyer registers, pricing,
  outreach queues, or the event ledger. This packet is staged separately.

## Required return

Return a short cited narrative followed by one JSON block matching
`config/schemas/deep_research_lead_schema.yaml` exactly:

```json
{
  "research_report_id": "DR-EXPORT-[CATEGORY]-[COUNTRY]-YYYYMMDD",
  "research_type": "export_category_country_thesis",
  "generated_at": "YYYY-MM-DD",
  "scope": {"category": "[CATEGORY]", "country": "[COUNTRY]", "max_leads": 12},
  "leads": [
    {
      "lead_id": "DR-EXPORT-[CATEGORY]-[COUNTRY]-001",
      "research_report_id": "DR-EXPORT-[CATEGORY]-[COUNTRY]-YYYYMMDD",
      "source_url": "https://public-source.example/path",
      "source_name": "Named official, buyer, retailer, importer, or trade source",
      "buyer_name": "Named buyer if evidenced, otherwise UNKNOWN",
      "buyer_type": "IMPORTER | RETAILER | DISTRIBUTOR | RESEARCH",
      "workflow_type": "EXPORT",
      "category": "[CATEGORY]",
      "lead_title": "Specific category-country opportunity or validation lead",
      "location": "[COUNTRY / city if evidenced]",
      "deadline": "UNKNOWN",
      "evidence_level": "PUBLIC_LISTING_ONLY",
      "why_interesting": "What the cited source directly supports",
      "why_low_competition": "A bounded hypothesis, including counter-evidence if competition is high",
      "fulfilment_hypothesis": "What must later be verified about supplier, compliance, price, and logistics",
      "risks": ["Specific commercial, regulatory, demand, or evidence risks"],
      "missing_info": ["Exact proof still required before a case or outreach"],
      "recommended_repo_action": "WATCH",
      "owner_review_required": true,
      "source_citations": ["https://public-source.example/path"],
      "confidence": "LOW | MEDIUM | HIGH",
      "disconfirming_evidence": ["Evidence against the thesis, or an explicit none found statement"]
    }
  ]
}
```

Every `source_url` must be a public HTTP(S) URL. Every material claim needs a
nearby citation in the narrative and its corresponding lead's
`source_citations` list. If no defensible lead exists, return an empty
`leads` array and explain why.

## Staging instruction

Save the JSON as a local research packet, then validate without mutating a
business register:

```bash
.venv/bin/python scripts/stage_deep_research_leads.py --input <saved-packet.json> --dry-run
```

Only an evidence review can later route a staged item to a deterministic
capture lane. No external action is authorized by this packet.
