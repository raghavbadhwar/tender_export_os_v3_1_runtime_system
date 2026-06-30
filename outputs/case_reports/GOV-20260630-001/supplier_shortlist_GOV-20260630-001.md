# Supplier Shortlist — GOV-20260630-001

Generated: 2026-06-30
Agent: supplier_engine_5_3_2_kanban
Workflow: GOV
Product: Office Stationery and Supplies
Quantity: 500 Set
Delivery location: Pune Collectorate

## 5-3-2 Gate Check

| Gate | Result |
|---|---|
| Minimum 5 candidate suppliers | Met: 6 candidates are available when existing SUP-001 is combined with SUP-010 through SUP-014. |
| Minimum 3 source types | Met: internal supplier history/past quote, TradeIndia India B2B, ExportersIndia directory, and OpenStreetMap local-cluster sources. |
| Minimum 2 quote proofs | Met in `data/quote_master.csv`: Q-001 and Q-004. |
| Blacklist/watchlist check | No listed candidate is marked blacklisted/watchlisted in `data/supplier_master.csv`; new candidates are provisional and need formal verification before outreach. |
| External action | None taken. No supplier RFQ, call, email, PO, delivery/payment commitment, or price commitment was sent. |

## Candidate Suppliers

| Rank | Supplier ID | Supplier | Source type | Evidence | Preliminary score | Status |
|---:|---|---|---|---|---:|---|
| 1 | SUP-001 | Ravi Stationery Works | Internal history / IndiaMART | Existing quote Q-001; local supplier history; GeM flag in supplier master | 94 | Primary existing proof |
| 2 | SUP-011 | Brahmani Stationery Private Limited | India B2B / TradeIndia | TradeIndia public listing for JB9 Eco Friendly Stationery Kit with Sticky Note Pad at INR 145 | 76 | Public quote proof Q-004; formal confirmation required |
| 3 | SUP-010 | Sg Interglobe LLP | India B2B / TradeIndia | TradeIndia public listing for A4 notepads with INR 2-200 per piece price trend | 74 | Candidate; no RFQ sent |
| 4 | SUP-012 | Venus Traders | Local cluster / OSM | OSM shop=stationery Pune result; website shown for one listing | 65 | Local Pune candidate; verify before RFQ |
| 5 | SUP-014 | Payper Nest Notebooks | India B2B directory / ExportersIndia | ExportersIndia office stationery table lists Hubli supplier with INR 3-150 per piece range | 62 | Candidate; no RFQ sent |
| 6 | SUP-013 | Jeevandip Stationery and Varieties | Local cluster / OSM | OSM shop=stationery Pune result on Dhayari Road | 58 | Backup local candidate; verify before RFQ |

## Quote Proofs Now Recorded

| Quote ID | Supplier | Source | Unit price | Caveat |
|---|---|---|---:|---|
| Q-001 | Ravi Stationery Works | Existing recorded supplier response | INR 210 / Set | Existing formal quote record. |
| Q-004 | Brahmani Stationery Private Limited | Public TradeIndia listing | INR 145 / Set | Indicative public listed price only; not a supplier-requested quote and not an external commitment. |

## Approval Discipline

APR-002 remains the owner approval gate before any formal supplier quote request or clarification is sent. This run only captured public/internal evidence and updated local registers.

## Sources Used

- `data/master_cases.csv`
- `data/supplier_master.csv`
- `data/quote_master.csv`
- `config/sources.supplier.yaml`
- `agents/supplier_engine_agent.md`
- https://www.tradeindia.com/manufacturers/office-stationery.html
- https://www.tradeindia.com/manufacturers/stationery-set.html
- https://www.exportersindia.com/indian-suppliers/office-stationery.htm
- OpenStreetMap/Overpass shop=stationery Pune query via https://overpass-api.de/api/interpreter

## Recommendation

Use Q-001 and Q-004 for an internal preliminary pricing range only. Before any external submission or supplier commitment, obtain owner approval and send formal quote-confirmation RFQs to the shortlisted suppliers.
