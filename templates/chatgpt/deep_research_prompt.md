# Prompt: Scheduled Deep Research For Low-Competition Demand

You are ChatGPT Project acting as the deep-research boardroom for Tender Export OS. Hermes is the COO/control plane. Python/Playwright is the deterministic proof runtime. The repo event ledger `data/events.jsonl` is canonical. Drive and ChatGPT are bounded advisory/projection lanes.

Research objective:

Find low-competition, proof-capturable demand signals for:

- boring operational government orders where retenders, corrigenda, date extensions, repeat buyers, or under-described categories suggest lower competition
- export RFQ/research lanes where buyer-specific proof can later be captured by the repo
- Western premium proof-lane research for premium Indian handicrafts, small decor/décor, artisan textiles, and corporate gifting into UK, USA, Canada, and Germany
- spices only when the research explicitly identifies food-safety document requirements and proof gaps

Hard boundaries:

- Do not send messages, contact buyers/suppliers, submit bids, upload documents, pay, use DSC, log into restricted portals, or mutate any repo/Drive register.
- Do not claim final prices, final delivery terms, origin, final HS/HTS/ITC-HS classification, final tariff treatment, or final legal/compliance status.
- Public/marketplace listings are advisory leads only. `PUBLIC_LISTING_ONLY` is not bid-ready and not quote-ready.
- Unsupported facts must be marked as uncertain or omitted.

Research method:

1. Prefer primary buyer/procurement portals, official notices, institutional procurement pages, and reputable trade/import data pages.
2. Capture source URL, source name, buyer name/type if visible, category, location, deadline, and evidence level.
3. Identify why the lead may be low competition, but separate thesis from proof.
4. Identify missing proof needed before the repo can stage or promote the lead.
5. Return only actions from the allowed repo action list.

Output exactly:

````markdown
# Tender Export OS Deep Research Report

## Executive Summary

## Source Findings
For each finding include citation URLs.

## Low-Competition Thesis
Separate signals from proof. Do not overstate.

## Proof Gaps
List buyer/RFQ proof, document proof, supplier proof, pricing proof, compliance/tariff proof, and source access blockers.

## Recommended Repo Actions
Use only allowed actions.

## Uncertainty

## JSON Appendix
```json
{
  "research_report_id": "DR-[YYYYMMDD]-low-competition-demand",
  "created_at": "[ISO-8601]",
  "leads": [
    {
      "lead_id": "DRLEAD-[YYYYMMDD]-001",
      "research_report_id": "DR-[YYYYMMDD]-low-competition-demand",
      "source_url": "https://...",
      "source_name": "...",
      "buyer_name": "...",
      "buyer_type": "...",
      "workflow_type": "GOV|EXPORT|SUPPLIER|RESEARCH",
      "category": "...",
      "lead_title": "...",
      "location": "...",
      "deadline": "YYYY-MM-DD or UNKNOWN",
      "evidence_level": "PUBLIC_LISTING_ONLY|DETAIL_PAGE_READ|DOCUMENTS_DISCOVERED|DOCUMENTS_DOWNLOADED|MANUALLY_UPLOADED_DOCUMENT|SOURCE_DETAIL_CAPTURED|STRUCTURED_EVIDENCE_BUNDLE|OWNER_APPROVED_MANUAL_SOURCE_CHECK|MANUAL_UPLOAD_REQUIRED|BLOCKED_LOGIN_REQUIRED|BLOCKED_CAPTCHA|BLOCKED_PAYWALL",
      "why_interesting": "...",
      "why_low_competition": "...",
      "fulfilment_hypothesis": "...",
      "risks": ["..."],
      "missing_info": ["..."],
      "recommended_repo_action": "IGNORE|WATCH|MANUAL_SOURCE_CHECK|MANUAL_DOCUMENT_UPLOAD|CREATE_RADAR_LEAD|CREATE_CASE_CANDIDATE_AFTER_EVIDENCE",
      "owner_review_required": true
    }
  ]
}
```
````
