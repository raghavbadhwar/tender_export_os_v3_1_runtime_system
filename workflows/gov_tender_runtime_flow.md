# Government Tender Runtime Flow

## Purpose
Step-by-step operational flow for government tender opportunities from discovery to bid submission.

---

## Flow Diagram
```
Source Scan → Case ID Assigned → Fast Kill → Deep Read → Supplier Sourcing
    → 5-3-2 Gate → Pricing → Bid Pack → Approval Card → OWNER DECISION
    → [Approved] → Submit Bid (DSC) → Track Result → WON/LOST/ARCHIVED
```

---

## Stage 1: Discovery
**Agent:** Radar Agent  
**Sources:** GeM, CPPP, eProcure, state portals  
**Output:** New case row in master_cases.csv (status = NEW)

**Key fields captured:**
- Tender reference number
- Buyer name and type
- Category
- Deadline
- EMD amount (if visible)
- Estimated value (if visible)

---

## Stage 2: Fast Kill
**Agent:** Fast Kill Agent  
**Decision time:** < 2 minutes per case  
**Outcome:** REJECTED | WATCHLIST | pass to DEEP_READ

**Automatic rejects:**
- Deadline ≤ 5 days
- Turnover requirement exceeded
- OEM auth required but unavailable
- Mandatory license missing
- MSME reserved but we are not registered (if applicable)

**Watchlist (human review):**
- EMD borderline high
- Experience gap — may be manageable
- Local content unclear

---

## Stage 3: Deep Read
**Agent:** Deep Read Agent  
**Inputs:** All tender documents, BOQ, corrigenda  
**Output:** Full case data, deep read report

**Critical extractions:**
- Complete BOQ with quantities and specs
- Eligibility matrix: every requirement vs. our status
- Payment terms: advance % + milestone + final trigger
- Penalty clause: per day/week rate + cap
- Delivery: location + days from PO
- Documents required for bid: full checklist
- Corrigenda: read all — override original where they conflict

---

## Stage 4: Supplier Sourcing
**Agent:** Supplier Engine  
**Gate:** Minimum 5 candidates, 3 source types, 2 quote proofs  
**Sources:** GeM sellers, IndiaMART, NSIC, local clusters  

**For GOV tenders, check:**
- BIS/ISI mark compliance (if required by tender)
- MSME/Udyam number (for reserved tenders)
- Past government supply track record
- Willingness to provide delivery to tender delivery location

---

## Stage 5: Pricing
**Agent:** Pricing Agent  
**Waterfall:** Supplier cost + GST + freight + packaging + EMD finance + working capital + payment delay buffer + penalty reserve + margin = **Final Bid Price**

**Show 3 options:**
- Conservative (safe, higher price)
- Recommended (target margin)
- Aggressive (win, thin margin — only if strategic)

---

## Stage 6: Bid Pack Assembly
**Agent:** Pack Builder  
**Contents:**
- Bid cover and executive summary
- Filled BOQ with draft prices
- Compliance matrix (clause-by-clause)
- Eligibility declaration template
- Supplier summary and certificates
- EMD plan (amount, form, source)
- Delivery timeline
- Risk register
- Missing items list (explicit)

---

## Stage 7: Approval Card
**Agent:** Approval Desk  
**Owner receives:** Full approval card with benefit / risk / recovery  
**Owner decides:** Approve / Reject / Ask Changes

---

## Stage 8: Bid Submission (OWNER ONLY)
⚠️ **This stage requires the owner to act manually.**

1. Owner reviews final bid pack
2. Owner confirms all eligibility documents are ready
3. Owner triggers DSC use (on portal)
4. Owner uploads bid documents on portal
5. Owner pays EMD (bank transfer / DD as required)
6. Owner submits bid

**Codex/Hermes do NOT do any of this.**

---

## Stage 9: Post-Submission Tracking
**Agent:** Execution Tracker

- Record bid submission acknowledgement (portal reference number)
- Track bid opening date
- Track result date
- On result: update case as WON or LOST
- On WIN: track work order receipt, delivery timeline, invoice, payment
- On LOSS: archive with L1 price (for benchmarking)

---

## Status Reference (GOV)
```
NEW → FAST_KILL → REJECTED
NEW → FAST_KILL → WATCHLIST → [owner promotes] → DEEP_READ
DEEP_READ → SUPPLIER_SEARCH → PRICING_READY → APPROVAL_REQUIRED
APPROVAL_REQUIRED → APPROVED → SENT_OR_SUBMITTED → FOLLOW_UP → WON/LOST → ARCHIVED
APPROVAL_REQUIRED → CHANGES_REQUESTED → [rework] → APPROVAL_REQUIRED
APPROVAL_REQUIRED → REJECTED (owner rejects)
```
