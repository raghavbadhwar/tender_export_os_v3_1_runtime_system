---
name: teos-buyer-acquisition
description: Discover, evidence, stage, approve, contact, and track foreign buyer targets without confusing catalogue fit with confirmed demand.
version: 1.0.0
author: Tender Export OS
metadata:
  hermes:
    tags: [buyers, exports, deep-research, agent-browser, outreach, replies]
---

# Tender Export OS Buyer Acquisition

1. ChatGPT Deep Research discovers markets, retailer assortments, buyer segments, and public target-account candidates with official citations.
2. `scripts/agent_browser_capture.py` captures exact public company, catalogue, product, and contact evidence. Never click, fill, submit, upload, message, pay, use DSC, or bypass access controls.
3. `scripts/stage_buyer_market_research.py` validates and stages demand signals, buyer targets, drafts, cases, and approval cards. Catalogue fit is not an RFQ or confirmed purchasing intent.
4. Never guess emails, infer personal addresses, or describe a general sales/trade contact as a buying/procurement contact.
5. First outreach and every follow-up require a current owner approval receipt and matching scope hash.
6. Gmail operations use the Gmail plugin only. Approved handoffs live under `runtime/gmail_plugin_outbox/`; send receipts and replies use the contracts in `docs/GMAIL_PLUGIN_BUYER_REPLY_CONNECTOR.md`.
7. `scripts/generate_buyer_reply_monitor.py` classifies replies. Opt-out, bounce, or not-interested stops the lane; positive, question, negotiation, or unclear replies become an owner action. Never auto-reply.
8. Keep all commercial facts provisional until supplier proof, pricing, compliance, delivery, and payment gates are satisfied.
9. Approval-wait Kanban cards must use a sticky `needs_input` block. Create them with `--initial-status blocked`, verify the task has a `blocked` event whose `kind` is `needs_input`, and reclaim/re-block immediately if a dispatcher ever claims one. Never rely on an untyped generic block for an approval gate.
