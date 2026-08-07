# Gmail Send Preflight

TASK-094 is implemented in the existing Gmail-plugin handoff path.

The public-template config uses `owner@example.com`. A private deployment may inject its owner account at runtime with `HERMES_GMAIL_SENDER_ACCOUNT`; the value is not committed to the repository.

Generator: `scripts/generate_gmail_plugin_outbox.py`

The system still does not send email by itself. It only prepares packets for the Gmail plugin after deterministic preflight.

## Required checks before packet output

The preflight verifies:

- connector is exactly `GMAIL_PLUGIN`;
- sender account is the configured owner account (`owner@example.com` in this public template; private deployments must inject their account from a secret store);
- connector status is `CONNECTED_GMAIL_PLUGIN`;
- recipient matches the verified outreach contact;
- approval ID, receipt path, and scope hash match the current approval row;
- content SHA-256 matches `body_text`;
- every attachment path and SHA-256 matches, if attachments exist;
- idempotency key is present;
- no prior sent receipt or executed approval exists.

If any check fails, the packet is not written.

## Ambiguous connector rule

If connector state is anything other than `CONNECTED_GMAIL_PLUGIN`, the preflight blocks. It does not retry automatically and does not fall back to gws, direct IMAP, Himalaya, or browser Gmail.

## Verification

Run:

```bash
python3 -m pytest tests/test_gmail_plugin_outbox.py -q
python3 scripts/generate_gmail_plugin_outbox.py
```

The generator is safe in preview mode. It writes only a local report under `outputs/gmail_plugin_outbox/` and does not send email.
