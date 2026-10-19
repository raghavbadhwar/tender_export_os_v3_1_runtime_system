# Relationship Memory Policy

Hermes relationship memory is a small verified operating register, not an inbox mirror. The source of truth is `data/relationship_memory.csv`, governed by `config/relationship_memory_policy.yaml`.

Allowed entries: verified communication preferences, opt-outs, recurring objections, and owner corrections. Every entry needs a metadata-only JSON receipt, a SHA-256 hash, a named recorder, and `VERIFIED` status.

Never retain raw email bodies, full threads, direct email addresses or phone numbers, private contact lists, credentials, cookies, mailbox exports, or unredacted reply snippets. Reply classification alone does not auto-promote anything into memory.

Use `scripts/record_relationship_memory.py` in dry-run first. `--write` records only the sanitized summary, the receipt reference, and the canonical audit event; it sends nothing and does not alter outreach status.
