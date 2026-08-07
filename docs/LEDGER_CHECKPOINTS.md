# Ledger Checkpoints

`python3 scripts/export_ledger_checkpoint.py` creates a local, privacy-safe
`ledger_checkpoint.v1` receipt from the validated `data/events.jsonl` stream.
The receipt contains only the validated event count, a hash-chain terminal
digest, the raw source SHA-256 digest, the timestamp policy, and the maximum
validated event timestamp. It never copies event payloads, tender/supplier/
buyer identifiers, credentials, or owner data.

## Determinism and verification

The hash chain starts from a fixed checkpoint-v1 genesis value and hashes each
canonical, sorted JSON event in stream order. Identical ledger bytes therefore
produce identical receipts. `source_sha256` detects byte-level changes,
`event_count` detects truncation, and `terminal_hash` detects reordered or
content-changed valid events.

Create a receipt and verify a later ledger against it locally:

```bash
python3 scripts/export_ledger_checkpoint.py \
  --events-file data/events.jsonl \
  --output outputs/ledger_checkpoint.json
python3 scripts/export_ledger_checkpoint.py \
  --events-file data/events.jsonl \
  --expected-checkpoint outputs/ledger_checkpoint.json
```

A mismatch exits non-zero and reports `tamper_detected`; malformed or invalid
events fail closed. The command only reads local files and optionally writes a
local receipt. It does not contact, upload to, or claim an external trust
anchor. External storage or anchoring, retention, and operator acceptance are
separate human/infrastructure gates.
