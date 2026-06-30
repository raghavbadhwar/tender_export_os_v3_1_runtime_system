# Supplier Sourcing Runtime Flow

## Purpose
Defines exactly how supplier sourcing works for both GOV tender and EXPORT RFQ cases. This is how we apply the 5-3-2 rule in practice.

## v4 Runtime Split
- Hermes routes the sourcing task, tracks Kanban state, and creates approval cards.
- Codex App-Server Runtime may perform table updates, supplier scorecards, and shortlist artifact production.
- No supplier quote request is sent until owner approval is recorded.
- Supplier lessons may be summarized into Hermes memory only after approval and never as raw supplier tables.

---

## 5-3-2 Rule Definition
- **5** minimum candidate suppliers identified
- **3** minimum source types searched
- **2** minimum quote proofs received before pricing proceeds

Exception: Specialized/niche category with explicit owner approval in case record.

---

## Step 1: Internal Check First
Always start with `data/supplier_master.csv`

Search filter:
- `products_supplied` contains the product category keyword
- `blacklisted = FALSE`
- `watchlisted = FALSE` (or owner aware)
- `last_quote_date` within 90 days preferred

Outcome: May find 0–3 known suppliers to include in candidate list.

---

## Step 2: External Search Plan

Identify which source types to search based on workflow:

### For GOV Tender
| Source Type | Platforms | Priority |
|---|---|---|
| GeM seller | mkp.gem.gov.in | 1st |
| India B2B | IndiaMART | 2nd |
| India B2B | TradeIndia | 3rd |
| MSME/NSIC | nsicspms.com | 4th |
| Local cluster | Google Maps + JustDial | 5th |
| Past awardees | CPPP results search | 6th |

### For EXPORT RFQ
| Source Type | Platforms | Priority |
|---|---|---|
| EPC directory | APEDA, FIEO, Spices Board | 1st |
| India B2B | IndiaMART (exporters filter) | 2nd |
| Local cluster | Google Maps industrial area | 3rd |
| India B2B | TradeIndia | 4th |
| Global benchmark | Alibaba (price only) | 5th |
| Supplier master | Internal history | Always |

---

## Step 3: For Each Source — What to Extract

For each supplier found:
- Full legal name
- Contact: person, phone, email
- City, state
- GST number (for identity verification)
- MSME/Udyam (for GOV tenders)
- IEC number (for EXPORT)
- Product match details
- Visible certifications (BIS, ISO, FSSAI, APEDA, etc.)
- Approximate lead time
- Platform rating / trust score
- Past order evidence (if visible on platform)

---

## Step 4: Blacklist and Watchlist Check

Before adding to candidate list:
1. Check `data/supplier_master.csv` for `blacklisted = TRUE` → exclude immediately
2. Check for `watchlisted = TRUE` → include but flag in report
3. If not in master → run basic verification (GST number validity check if possible)

---

## Step 5: Score Each Supplier (Preliminary)
Use supplier scoring factors from `config/scoring_weights.yaml`.

At this stage, score what is visible:
- Identity proof: GST + address verifiable?
- Product fit: exact match / close match / partial?
- Certificates: visible on platform?
- Export/tender experience: visible on platform?
- Platform signals: rating, years on platform, response rate

Full score updated after quote received.

---

## Step 6: Prepare Shortlist (Top 3)

Rank all candidates. Select top 3 for quote requests.

For each shortlisted supplier, prepare:
- Quote request draft (using `templates/supplier_quote_request.txt`)
- Key data to include in request:
  - Product name and detailed spec
  - Quantity required
  - Delivery location (GOV) or origin port (EXPORT)
  - Required packing and labelling
  - Required certifications
  - Timeline for quote response (48 hours)
  - Our payment terms
  - Request for: unit price, lead time, MOQ, validity

---

## Step 7: Create Approval Card for Quote Requests
⚠️ Cannot send quote requests without owner approval.

- Create approval card with all 3 supplier details
- Note: what happens if supplier doesn't respond
- Owner can approve all 3 at once or select specific ones

---

## Step 8: Track Quote Responses
After approval received and requests sent:

| Timeframe | Action |
|---|---|
| 0–24 hours | Monitor for acknowledgement |
| 24–48 hours | If no response, flag in agent log |
| 48 hours | If no response, escalate in brief — try alternate supplier |
| Quote received | Log to quote_master.csv immediately |
| 2+ quotes received | Trigger pricing agent |

---

## 5-3-2 Gate Check Before Pricing
```
✓ Number of candidates searched: ≥ 5
✓ Number of source types used: ≥ 3  
✓ Number of confirmed quotes received: ≥ 2
✓ Blacklist check done: YES
✓ At least basic identity verified: YES
```

If ANY gate fails: DO NOT proceed to Pricing. Log gap, flag in brief.

---

## Supplier Master Update
After every sourcing run, update `data/supplier_master.csv`:
- Add new suppliers not previously in master
- Update `last_quote_date` for existing suppliers
- Update certificate and contact details if changed
- Update `total_quotes_requested` and `total_quotes_received` counters
