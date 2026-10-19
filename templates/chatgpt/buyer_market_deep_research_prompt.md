# Foreign Retailer Demand and Buyer Deep Research

Research public businesses in `[COUNTRIES/MARKETS]` whose current catalogue shows a credible fit for `[CATEGORY]` supplied from India.

For handicrafts/home decor, inspect actual public assortment pages—not generic directories or marketplace landing pages. Prefer retailers, importers, distributors, museum/design shops, ethical/fair-trade stores, hospitality procurement groups, and corporate-gifting buyers. Separate competitors from plausible buyer targets.

For each target:

1. Verify the legal/company identity from its official site or official registry page.
2. Cite the company homepage, the catalogue/category page, at least one matching product page, and the public contact page.
3. Describe the exact observed products/materials/style and why they indicate category fit.
4. Label the evidence honestly: catalogue fit is a demand hypothesis, not an RFQ or proof that the company wants a new supplier.
5. Record only a public business contact path. Never guess an email, infer a personal address, scrape private data, or claim a general sales/trade address is a procurement address.
6. Recommend outreach only when the company, catalogue fit, and contact path are all evidenced.

Do not send messages, submit forms, log into portals, accept terms, upload files, quote a price, promise delivery, finalize classification/origin/compliance, or perform any external action.

Return a concise research memo plus this JSON appendix:

```json
{
  "research_report_id": "DR-BUYER-MARKET-YYYYMMDD-001",
  "category_code": "EXP-CRAFT-001",
  "category_name": "Handicrafts and Artisan Products",
  "items": [
    {
      "company_name": "",
      "country": "",
      "company_type": "Retailer|Importer|Distributor|Hospitality buyer|Corporate gifting buyer",
      "website_url": "https://...",
      "catalog_url": "https://...",
      "matching_products": [
        {
          "product_name": "",
          "product_url": "https://...",
          "evidence": ""
        }
      ],
      "assortment_evidence": "",
      "price_positioning": "VALUE|MID|PREMIUM|UNKNOWN",
      "contact_page_url": "https://...",
      "public_contact": "public business email, public form, or blank",
      "contact_scope": "UNKNOWN|GENERAL_CONTACT|PROCUREMENT|BUYING|TRADE_ACCOUNT",
      "evidence_level": "CATALOG_OBSERVED|COMPANY_AND_CATALOG_VERIFIED|CONTACT_PATH_VERIFIED",
      "market_fit_score": 0,
      "demand_confidence": "LOW|MEDIUM|HIGH",
      "source_citations": ["https://..."],
      "risks_and_unknowns": [""]
    }
  ]
}
```
