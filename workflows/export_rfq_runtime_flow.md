# Export RFQ Runtime Flow

## Purpose
Step-by-step operational flow for export buyer RFQ opportunities from discovery to quote sent.

---

## Flow Diagram
```
Source Scan → Case ID → Fast Kill → Buyer Verify → Deep Read → Compliance Draft
    → Supplier Sourcing → 5-3-2 Gate → Pricing (EXW/FOB/CIF)
    → Export Quote Pack → Approval Card → OWNER DECISION
    → [Approved] → Send Quote → Track PO → WON/LOST/ARCHIVED
```

---

## Stage 1: Discovery
**Agent:** Radar Agent  
**Sources:** Alibaba RFQ, India Business Portal, FIEO Connect, EC21, TradeKey, ExportersIndia, IndiaMart buyer leads

**Key fields captured:**
- Buyer name, country, platform
- Product description
- Quantity and unit
- Destination and Incoterms requested
- Payment terms requested
- RFQ deadline or response window

---

## Stage 2: Fast Kill
**Agent:** Fast Kill Agent  
**Outcome:** REJECTED | WATCHLIST | DEEP_READ

**Automatic rejects:**
- SCOMET item detected (immediate stop)
- Prohibited export
- Buyer not verifiable (score < 40)
- High-risk destination country
- Order too small (margin < threshold)
- Deadline < 3 days

**Watchlist:**
- Restricted export policy (needs DGFT license check)
- Complex compliance (SPS, drug cert)
- Buyer partially verified

---

## Stage 3: Buyer Verification
**Process (within Deep Read)**

Verify buyer via:
1. Company registration database of destination country
2. Dun & Bradstreet or equivalent credit check
3. LinkedIn or company website check
4. Previous transactions or references (if any)
5. Platform trust score (Alibaba trade assurance, etc.)

Buyer credibility score:
- 80–100: Proceed, strong buyer
- 60–79: Proceed, note risks
- 40–59: Watchlist, request additional verification
- < 40: Reject — do not proceed

---

## Stage 4: Deep Read
**Agent:** Deep Read Agent  
**Inputs:** RFQ document, buyer spec sheet, platform RFQ page

**Critical extractions:**
- Product spec: grade, dimensions, composition, packing
- Quantity: total and per shipment
- Destination: country, port, address
- Delivery deadline
- Incoterms proposed
- Payment terms proposed
- Sample requirement (quantity, paid/free, destination)
- Inspection method
- Destination country import requirements (visible from RFQ)
- Certificate requirements stated by buyer

---

## Stage 5: Compliance Draft
**Agent:** Compliance Agent  
**Output:** `compliance_draft_<case_id>.md`

**Covers:**
- ITC-HS candidate classification (DRAFT ONLY)
- Export policy: Free / Restricted / Prohibited / SCOMET
- Destination country requirements
- Certificate of origin type and issuing body
- Rules of origin (for FTA if applicable)
- FTA preferential tariff opportunity
- Documents required: packing list, commercial invoice, PI, shipping bill, BL, COO, inspection cert
- Incoterms recommendation (our recommendation vs. buyer's ask)
- IEC/GST/e-RCMC checklist

⚠️ AI classification is DRAFT only. Expert and owner must approve before use in external documents.

---

## Stage 6: Supplier Sourcing
**Agent:** Supplier Engine  
**5-3-2 Rule strictly enforced:**
- 5+ candidates: IndiaMART, APEDA, EPC directory, local cluster, GeM/TradeIndia
- 3+ source types
- 2+ quote proofs before pricing

**For EXPORT, check:**
- IEC held by supplier
- Export experience (past shipments)
- FSSAI/APEDA for food/agri
- Willingness to supply in export packing
- Pre-shipment inspection compatibility
- Lead time vs. buyer deadline

---

## Stage 7: Pricing
**Agent:** Pricing Agent  
**Waterfall:** Supplier base + packaging + inland freight + CHA + port + international freight + insurance (if CIF) + bank charges + inspection + sample + currency buffer + risk buffer + margin = **EXW / FOB / CIF Quote**

**Always show all three:** EXW, FOB, CIF — owner selects which to send.

---

## Stage 8: Export Quote Pack
**Agent:** Pack Builder  
**Contents:**
- Quote cover and executive summary
- Proforma invoice (draft)
- Product specification sheet
- Compliance summary (condensed)
- Supplier summary
- Pricing breakdown (all three Incoterms)
- Payment terms proposal
- Quote validity: 30 days standard
- Missing items list

---

## Stage 9: Approval Card
**Agent:** Approval Desk  
**Card includes:** Amount in USD, buyer details, payment risk, compliance status, confidence score

---

## Stage 10: Quote Send (OWNER ACTION)
⚠️ **This stage requires owner action.**

1. Owner reviews export quote pack
2. Owner confirms compliance note is understood
3. Owner sends proforma invoice / quote email (using template)
4. Owner records send timestamp

**Hermes/Codex do NOT send the quote.**

---

## Stage 11: Post-Quote Tracking
**Agent:** Execution Tracker

- Track quote validity window (30 days default)
- 7-day no-reply → flag for follow-up
- Quote validity expiry alert (24h before)
- On PO receipt: status = WON, trigger order execution
- On rejection: record feedback, archive

---

## Status Reference (EXPORT)
```
NEW → FAST_KILL → REJECTED
DEEP_READ → SUPPLIER_SEARCH → PRICING_READY → APPROVAL_REQUIRED
APPROVED → SENT_OR_SUBMITTED → FOLLOW_UP → WON → [delivery / payment] → ARCHIVED
```
