# Gmail Plugin Buyer Reply Connector

Tender Export OS accepts Gmail reply data only from the installed Gmail plugin. Do not use `gws`, direct IMAP, Himalaya, browser Gmail, or guessed mailbox state for Gmail operations.

The connector automation writes one JSON packet per mailbox read to:

```text
runtime/gmail_plugin_inbox/
```

Contract:

```json
{
  "connector": "GMAIL_PLUGIN",
  "account": "the owner-approved Gmail account",
  "fetched_at": "2026-07-12T09:00:00+05:30",
  "messages": [
    {
      "external_message_id": "provider message id",
      "external_thread_id": "provider thread id",
      "outreach_id": "OUT-...",
      "received_at": "2026-07-12T08:55:00+05:30",
      "subject": "Re: ...",
      "snippet": "short connector-provided snippet",
      "body_text": "reply body"
    }
  ]
}
```

The automation should also write `runtime/gmail_plugin_inbox/connector_status.json` with `{ "connected": true }` after a verified live mailbox read.

Hermes then runs:

```bash
.venv/bin/python scripts/generate_buyer_reply_monitor.py --process-inbox --record-event
```

The importer stores reply text only under ignored private receipts, records minimal metadata in the communication ledger, classifies the reply, stops on opt-out/bounce/not-interested signals, and prepares an owner action. It never sends or auto-replies.

## Approved Send Handoff

After the owner approves an outreach card, the reply monitor synchronizes the outreach row to `READY_AFTER_APPROVAL`. Generate the Gmail-plugin handoff with:

```bash
.venv/bin/python scripts/generate_gmail_plugin_outbox.py --write-outbox
```

The Gmail plugin automation consumes `runtime/gmail_plugin_outbox/*.json`. It must enforce the included approval ID, approval receipt, scope hash, and idempotency key. After an actual send, it writes a receipt packet:

```json
{
  "connector": "GMAIL_PLUGIN",
  "sends": [
    {
      "outreach_id": "OUT-...",
      "status": "SENT",
      "external_message_id": "...",
      "external_thread_id": "...",
      "sent_at": "2026-07-12T10:00:00+05:30"
    }
  ]
}
```

Record it with `scripts/ingest_gmail_send_receipts.py --input <receipt.json> --ingest`. Follow-ups remain separately approval-gated.
