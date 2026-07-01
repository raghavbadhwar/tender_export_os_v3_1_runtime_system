# Drive + ChatGPT Return Loop Safety Boundary

Tender Export OS uses Drive as a projection/knowledge bus, not as the canonical state database. The repo event ledger remains canonical.

## Current safe posture

- `public-template` Drive sync includes only sanitized docs, schemas, examples, and public config snapshots.
- `private-runtime` Drive sync includes live runtime registers only for the private Knowledge Bus lane.
- Both modes run a pre-upload content scan before any upload.
- `--dry-run` is the default review posture for hardening and regression.
- `--execute` is never used by automation unless the owner explicitly approves the upload scope.

## Public/private boundary

### Public-template may contain

- README / architecture / instruction docs
- JSON/YAML schemas
- `data/examples/**`
- `outputs/examples/**`
- `receipts/examples/**`
- sanitized config snapshots

### Public-template must not contain

- live suppliers, buyers, quotes, RFQs, cases, event ledger, approvals, local paths, credentials, cookies, DSC files, bank details, or private contact data.

### Private-runtime may contain

- live runtime registers
- approval receipts
- case evidence manifests
- source/plugin health
- event ledger

Private-runtime is still scanned for secrets. Known non-secret false positives are narrowly scrubbed only for private-runtime scan evaluation:

- public tender URL query flags such as `token=T` and `session=T`
- `token-cache` warning text without token values
- non-sensitive Drive `uploaded_file_id` references in internal plugin-health notes

## ChatGPT return loop

```text
Drive/08_ChatGPT_Bridge/01_To_ChatGPT
  Hermes sends bounded packet.

Drive/08_ChatGPT_Bridge/02_From_ChatGPT
  ChatGPT returns chatgpt_return.md.

Drive/08_ChatGPT_Bridge/03_Reviewed_For_Codex_Hermes
  Hermes/Codex validates return and writes review_plan.json.
```

Local dry-run checker:

```bash
python3 scripts/check_chatgpt_return_loop.py
```

This creates/validates local bridge folders, validates the fixture return, and writes a staging probe. It does not import from Drive, upload to Drive, mutate registers, approve actions, or send anything.

## Non-negotiables

ChatGPT returns and Drive files never directly mutate registers. They are staged, schema-validated, reviewed, and converted into owner-approved tasks or internal repo events only when safe.

No send, submit, upload, payment, DSC, final price, final HSN/ITC-HS, origin, certification, legal, tax, or compliance claim is authorized by Drive or ChatGPT output.
