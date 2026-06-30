# Export RFQ Batch Scan — 2026-06-30

Kanban task: t_86c809f2
Agent run: RUN-20260630131453

## Summary
- Sources checked: 16
- Cases created: 4 (EXP-20260630-003, EXP-20260630-004, EXP-20260630-005, EXP-20260630-006)
- External actions: none — no supplier/buyer contact, registration, bid, price, classification, or origin claim.
- Evidence reports: `outputs/source_scans/export_scan_probe_20260630_130537.json`, `outputs/source_scans/export_candidate_details_20260630_130726.json`

## New case rows
- `EXP-20260630-003` — Supply Inquiry for Rice
  - Source: TradeKey — https://importer.tradekey.com/buyoffer/Supply-Inquiry-For-Rice-3849377.html
  - Buyer/country: TradeKey buyer — contact hidden pending sign-in / South Africa
  - Product: Agricultural Commodities — Rice
  - Deadline: not stated
  - Status: NEW
- `EXP-20260630-004` — Purchase Inquiry for Juniper Oils
  - Source: TradeKey — https://importer.tradekey.com/buyoffer/Purchase-Inquiry-For-Juniper-Oils-3849579.html
  - Buyer/country: TradeKey buyer — partially masked, Turkey / Turkey
  - Product: Essential Oils — Juniper Oil
  - Deadline: not stated
  - Status: NEW
- `EXP-20260630-005` — 131-2026-RFQ-UNDP-GF “Supply of food kits”
  - Source: UNDP Procurement Notices — https://procurement-notices.undp.org/view_negotiation.cfm?nego_id=46967
  - Buyer/country: UNDP-TJK — Tajikistan / Tajikistan
  - Product: Food Kits / Humanitarian Supplies
  - Deadline: 2026-07-13
  - Status: NEW
- `EXP-20260630-006` — Long-Term Agreement for Supply and Delivery of Hygiene Supplies
  - Source: UNDP Procurement Notices — https://procurement-notices.undp.org/view_negotiation.cfm?nego_id=47079
  - Buyer/country: UNDP-PHL — Philippines / Philippines
  - Product: Hygiene Supplies
  - Deadline: 2026-07-21
  - Status: NEW

## Source results
- India Business Portal (DGFT): Broken; cases_found=0; login_required=FALSE; paywalled=FALSE; url=https://www.indiabusinessportal.gov.in; note=DNS resolution failed during scan; no buyer RFQ page reached.
- Indian Trade Portal (ITP): Access Blocked; cases_found=0; login_required=FALSE; paywalled=FALSE; url=https://www.indiantradeportal.in; note=Public fetch returned HTTP 403; no RFQ created.
- FIEO Connect: Needs Login; cases_found=0; login_required=TRUE; paywalled=FALSE; url=https://connect.fieo.org; note=Configured manual/login source; DNS resolution also failed during landing-page probe.
- APEDA AgriXchange: Needs Login; cases_found=0; login_required=FALSE; paywalled=FALSE; url=https://agriexchange.apeda.gov.in; note=Home page reachable, but /Buyer/BuyLeads redirected to exporter login; no public buyer lead extracted.
- Spices Board India: Working; cases_found=0; login_required=FALSE; paywalled=FALSE; url=https://www.indianspices.com; note=Public site reachable; tenders/trade enquiry pages found, but no export buyer RFQ created in this scan.
- Alibaba RFQ: Needs Login; cases_found=0; login_required=TRUE; paywalled=FALSE; url=https://rfq.alibaba.com; note=Configured login/manual source; public landing page only, no buyer details extracted.
- Global Sources: Access Blocked; cases_found=0; login_required=TRUE; paywalled=FALSE; url=https://www.globalsources.com; note=Bot/cookie interstitial encountered; no buyer RFQ extracted.
- EC21: Access Blocked; cases_found=0; login_required=FALSE; paywalled=FALSE; url=https://www.ec21.com; note=Public fetch returned HTTP 403; no RFQ created.
- TradeKey: Working; cases_found=2; login_required=FALSE; paywalled=FALSE; url=https://www.tradekey.com; note=Public latest buy offers reached; created cases for rice and juniper oil leads; skipped purge lump as non-export/inactive category fit.
- Made-in-China (Buying Leads): Needs Login; cases_found=0; login_required=TRUE; paywalled=FALSE; url=https://inquiry.made-in-china.com; note=Configured login/manual source; DNS resolution failed during landing-page probe.
- UN Global Marketplace (UNGM): Needs Login; cases_found=0; login_required=TRUE; paywalled=FALSE; url=https://www.ungm.org; note=Configured login/manual source; public probe returned HTTP 403.
- World Bank Procurement Notices: Working; cases_found=0; login_required=FALSE; paywalled=FALSE; url=https://www.worldbank.org/en/projects-and-operations/procurement; note=Configured URL returned 404; corrected public URL https://projects.worldbank.org/en/projects-operations/procurement was reachable/API scanned. Latest matching goods notice was complex lab/chemical equipment and no case was created.
- UNDP Procurement Notices: Working; cases_found=2; login_required=FALSE; paywalled=FALSE; url=https://procurement-notices.undp.org; note=Public notices reached; created cases for food kits and hygiene supplies; Quantum registration required before any bid action.
- African Development Bank Tenders: Access Blocked; cases_found=0; login_required=FALSE; paywalled=FALSE; url=https://www.afdb.org/en/projects-and-operations/procurement; note=Public fetch returned HTTP 403; no RFQ created.
- ExportersIndia: Working; cases_found=0; login_required=FALSE; paywalled=FALSE; url=https://www.exportersindia.com; note=Public site reachable; post-buy-requirement page found but no public buyer RFQ extracted.
- IndiaMart — Buyer Leads: URL Changed; cases_found=0; login_required=FALSE; paywalled=FALSE; url=https://www.indiamart.com/buy-leads/; note=Configured URL returned 404. Alternate /buyers/ page reachable but looked like a domestic profile, not export RFQ; no case created.
