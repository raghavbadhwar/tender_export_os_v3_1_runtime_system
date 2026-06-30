# Supplier Shortlist — EXP-20260630-001

Generated: 2026-06-30
Agent: supplier_engine_5_3_2_kanban
Workflow: EXPORT
Product: Organic Turmeric Powder
Quantity: 5000 KG monthly
Buyer destination: Dubai, UAE

## 5-3-2 Gate Check

| Gate | Result |
|---|---|
| Minimum 5 candidate suppliers | Met: 6 candidates remain recorded in `data/supplier_master.csv` (SUP-003 and SUP-005 through SUP-009). |
| Minimum 3 source types | Met: internal/APEDA history, direct exporter site, TradeIndia India B2B, and ExportersIndia directory. |
| Minimum 2 quote proofs | Met in `data/quote_master.csv`: Q-002 and Q-005. |
| Blacklist/watchlist check | No case candidate is marked blacklisted/watchlisted in `data/supplier_master.csv`; provisional candidates still require verification. |
| External action | None taken. No supplier RFQ, call, email, PO, delivery/payment commitment, export quote, classification/origin claim, or price commitment was sent. |
| Remaining blocker | Product/spec ambiguity remains: Q-002 says “95% curcumin,” which may not match plain organic turmeric powder. COA/spec clarification is still required before final pricing or buyer quote. |

## Candidate Suppliers

| Supplier ID | Supplier | Source type | Source/platform | Evidence | Preliminary fit | Action |
|---|---|---|---|---|---:|---|
| SUP-003 | Spice Valley Exports | epc_directory / internal history | APEDA / supplier master | Existing quote Q-002; APEDA/exporter history in supplier master | 98 | Request COA/spec clarification if APR-003 is approved |
| SUP-005 | Amar Foodz | direct_exporter_site | AmarFoodz / ExportersIndia | Public supplier/product page and ExportersIndia price table; Q-005 captured from public price listing | 77 | Formal quote/COA required if APR-003 is approved |
| SUP-006 | Ratnaraj Foods Private Limited | india_b2b | TradeIndia | TradeIndia organic turmeric powder listing | 68 | Draft RFQ remains unsent |
| SUP-007 | Navnath Spices Private Limited | india_b2b | TradeIndia | TradeIndia listing; FSSAI product claim requires proof | 70 | Draft RFQ remains unsent |
| SUP-008 | Darideep Agro Foods Private Limited | india_b2b_directory | ExportersIndia | ExportersIndia organic turmeric supplier listing | 60 | Draft RFQ remains unsent |
| SUP-009 | Globus Global Trade Import And Export | india_b2b | TradeIndia | TradeIndia organic turmeric powder listing | 58 | Draft RFQ remains unsent |

## Quote Proofs Now Recorded

| Quote ID | Supplier | Source | Unit price | Caveat |
|---|---|---|---:|---|
| Q-002 | Spice Valley Exports | Existing recorded supplier response | INR 95 / KG | Formal-looking existing quote, but “95% curcumin” wording requires COA/spec clarification. |
| Q-005 | Amar Foodz | Public ExportersIndia price table | INR 170 / KG | Indicative public listed price only; not a supplier-requested quote and not an external commitment. |

## Approval Discipline

APR-003 remains the owner approval gate before any supplier quote/clarification request is sent. This run only captured public/internal evidence and updated local registers.

## Sources Used

- `data/master_cases.csv`
- `data/supplier_master.csv`
- `data/quote_master.csv`
- `config/sources.supplier.yaml`
- `agents/supplier_engine_agent.md`
- https://www.tradeindia.com/manufacturers/organic-turmeric-powder.html
- https://www.exportersindia.com/indian-suppliers/organic-turmeric-powder.htm
- https://www.amarfoodz.in/organic-turmeric-powder.htm
- Existing audit: `outputs/case_reports/EXP-20260630-001/audit_EXP-20260630-001.md`

## Recommendation

Do not send a buyer quote or final pricing externally. The next useful owner action is to approve or ask changes on APR-003 so formal supplier quote confirmations and COA/spec clarification can be obtained.
