---
name: teos-recovered-context
description: Search the preserved Ares/Hermes session archive and recover relevant operating context without merging stale identities, demo data, credentials, or raw tool output into the live Tender Export OS profile.
version: 1.0.0
author: Tender Export OS
metadata:
  hermes:
    tags: [memory, recovery, session-search, provenance, ares]
---

# Tender Export OS Recovered Context

Use this skill only when earlier Ares/Hermes conversations or settings may materially answer the current Tender Export OS question.

1. Search the preserved archive with:

   `python3 scripts/search_recovered_ares_context.py --query "<terms>" --scope tender`

2. Keep `--scope tender` unless the owner explicitly asks for unrelated AIOS, Nectra, fitness, Telegram, or demo-wholesaler history.
3. Tool messages are excluded by default. Do not use `--include-tool-messages` unless raw execution evidence is necessary; inspect the result for secrets and personal data before relying on it.
4. Cite the returned legacy `session_id`, timestamp, archive hash, and current source-of-truth file when a recovered statement affects a decision.
5. Treat recovered content as historical evidence, not current truth. Recheck live repo state, auth, schedules, prices, policies, contacts, and external facts.
6. Never activate the old `Tom` or `A. Soul` identities, old fitness schedules, demo invoices, mock GST data, or generic wholesaler records inside this profile.
7. Never copy credentials, cookies, Telegram tokens, browser sessions, `.env` values, DSC material, bank data, or raw buyer/supplier tables into memory.
8. Promote a recovered fact into `MEMORY.md`, a skill, or canonical project state only after owner approval, provenance review, and current verification.

The preserved archive is read-only. The current `tender-export-os` profile, `data/events.jsonl`, receipts, and current repository files remain authoritative.
