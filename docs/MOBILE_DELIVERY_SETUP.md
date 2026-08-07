# Mobile Delivery Setup

Status: **NOT CONFIGURED — LOCAL DELIVERY ONLY**.

No owner messaging platform, token, chat allowlist, webhook, or external delivery credential is enabled in the Tender Export OS profile. Scheduled output remains local-file delivery with local fallback.

## Safe activation sequence

1. Owner explicitly selects exactly one private channel: Telegram, ntfy, Slack, Discord, or email.
2. Configure only a profile-local secret reference; never commit or print the credential value.
3. Add an owner-only user/chat/topic allowlist.
4. Run the credentialless validator before any configuration change:

   ```bash
   .venv/bin/python scripts/validate_owner_channel_delivery.py --json
   ```

5. Run one harmless owner-only delivery canary and preserve a `PASS` receipt.
6. Verify readback and failure fallback to a local report.
7. Change selected cron delivery targets only after the canary, receipt, and owner decision pass.

## Current live contract

- `config/owner_channel_delivery.yaml`: `enabled: false`
- `config/hermes_cron.yaml`: `owner_gateway: local`
- `config/hermes_cron.yaml`: `default_delivery_fallback: local_file`
- scheduled Telegram delivery: disabled
- local fallback: required
- external business actions from the owner channel: forbidden

The owner channel may carry only owner briefs, exception alerts, Kanban updates, and approval cards. It must never become a buyer/supplier outreach connector. Gmail buyer/supplier communication remains on the Gmail-plugin-only contract.

## Historical receipts

Older mobile-delivery receipts or documents are historical evidence and do not authorize current delivery. Current truth is determined by the live profile configuration, `config/hermes_cron.yaml`, the validator output, and a fresh canary receipt.
