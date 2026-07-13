# Drive Knowledge Bus Revalidation

TASK-096 revalidation is implemented through:

```bash
python3 scripts/revalidate_drive_knowledge_bus_sync.py --json
```

The script:

- creates a non-sensitive local receipt under `receipts/drive_setup/`;
- runs `scripts/sync_to_drive.py` in dry-run mode for `00_Project_Context`;
- writes a dry-run manifest under `outputs/drive_revalidation/`;
- checks Drive auth;
- never attempts live upload unless a separate owner-approved execute path is run.

## Routing contract

- Stable shared context belongs in `00_Project_Context`.
- `08_ChatGPT_Bridge` is only for bounded packet exchange.
- Drive is not canonical case state; `data/events.jsonl` remains canonical.

## Current result

The current revalidation produced:

```text
status: DRY_RUN_PASS_LIVE_AUTH_BLOCKED
live_upload_attempted: false
```

Dry-run routing passed. Live sync proof remains blocked until Google Drive/gws auth responds successfully.

The receipt includes machine-readable `remediation_steps`. For the current auth blocker:

```bash
gws auth login -s drive,sheets
python3 scripts/revalidate_drive_knowledge_bus_sync.py --json
```

Keep `live_upload_attempted: false` unless a separate owner-approved execute path is requested.
