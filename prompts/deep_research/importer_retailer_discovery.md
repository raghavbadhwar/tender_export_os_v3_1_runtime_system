# Deep Research Packet — Importer and Retailer Discovery

Use this packet to find public, evidence-backed foreign importer, distributor,
and retailer targets for **[CATEGORY]** in **[COUNTRY / REGION]**. The output
is a buyer-market research return, not an outreach instruction.

## Scope

- Return at most **15** companies with a live public website and catalogue or
  product evidence.
- Prefer each company's own website, catalogue, trade-account, supplier, or
  public contact page. Do not guess personal addresses or decision-makers.
- For every company, identify matching products, assortment fit, apparent
  positioning, public contact route, and evidence gaps.
- Include at least one counter-signal where available: current direct sourcing,
  a closed wholesale program, category mismatch, unclear importer status, or
  inaccessible evidence.

## Hard boundaries

- Do not contact, follow up with, or submit anything to any company.
- Do not guess an individual's name, email address, procurement role, MOQ,
  price, delivery date, origin, certification, or buyer demand.
- Catalogue fit is only a demand hypothesis; it is never an RFQ or an order.
- Do not mutate `data/buyer_master.csv`, `data/master_cases.csv`,
  `data/outreach_queue.csv`, approvals, or `data/events.jsonl`.

## Required return

Return a concise cited narrative followed by one JSON block conforming to
`config/schemas/buyer_market_research_return.yaml`:

```json
{
  "research_report_id": "DR-BUYERS-[CATEGORY]-[COUNTRY]-YYYYMMDD",
  "category_code": "EXP-[CATEGORY-CODE]",
  "category_name": "[CATEGORY]",
  "items": [
    {
      "company_name": "Named company",
      "country": "[COUNTRY]",
      "company_type": "Importer | Distributor | Retailer | Wholesaler",
      "website_url": "https://company.example",
      "catalog_url": "https://company.example/catalogue-or-collection",
      "matching_products": [
        {
          "product_name": "Named product visible on the public site",
          "product_url": "https://company.example/products/example",
          "evidence": "What the cited product page visibly shows"
        }
      ],
      "assortment_evidence": "Specific cited fit or mismatch; do not overstate demand",
      "price_positioning": "UNKNOWN | VALUE | MID | PREMIUM",
      "contact_page_url": "https://company.example/contact-or-trade",
      "public_contact": "Only a public business contact if it appears on the cited contact page; otherwise empty",
      "contact_scope": "UNKNOWN | GENERAL_CONTACT | PROCUREMENT | BUYING | TRADE_ACCOUNT",
      "evidence_level": "CATALOG_OBSERVED | COMPANY_AND_CATALOG_VERIFIED | CONTACT_PATH_VERIFIED",
      "market_fit_score": 0,
      "demand_confidence": "LOW | MEDIUM | HIGH",
      "source_citations": [
        "https://company.example/catalogue-or-collection",
        "https://company.example/products/example",
        "https://company.example/contact-or-trade"
      ],
      "risks": ["Reason this target may not be suitable"],
      "missing_info": ["Proof required before any outreach or quotation"]
    }
  ]
}
```

`catalog_url`, every `matching_products[].product_url`, and any populated
`contact_page_url` must each appear in `source_citations`. Use `UNKNOWN` or an
empty public contact field rather than guessing.

## Staging instruction

Save the JSON locally, then validate and render only a dry-run preview:

```bash
.venv/bin/python scripts/stage_buyer_market_research.py --input <saved-packet.json> --dry-run
```

The dry run does not authorize outreach. Any later persistent staging remains
approval-gated before the Gmail-plugin handoff, and no external action is
authorized by this packet. Do not mutate any business register from this
research task.
