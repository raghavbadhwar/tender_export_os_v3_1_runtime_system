# Case ID and Status System

## ID Formats
| Object | Format |
|---|---|
| Government tender | `GOV-YYYYMMDD-001` |
| Export opportunity | `EXP-YYYYMMDD-001` |
| Supplier | `SUP-0001` |
| Task | `TASK-YYYYMMDD-001` |
| Receipt | `REC-YYYYMMDD-001` |

All records and artifacts must reference `case_id` where case-specific. Supplier IDs and receipt IDs must still link back to `case_id` when applicable.

## Status Flow
- `NEW`
- `FAST_KILL`
- `REJECTED`
- `WATCHLIST`
- `DEEP_READ`
- `SUPPLIER_SEARCH`
- `PRICING_READY`
- `ARTIFACT_PRODUCTION`
- `APPROVAL_REQUIRED`
- `APPROVED`
- `CHANGES_REQUESTED`
- `SENT_OR_SUBMITTED`
- `FOLLOW_UP`
- `WON`
- `LOST`
- `ARCHIVED`

## Runtime Ownership
- Hermes interprets status and routes work.
- Codex updates records and artifacts.
- Google Drive stores shared state.
- ChatGPT reviews trends and strategy from snapshots.

## Script
Use:

```bash
python3 scripts/case_id_generator.py --type GOV
python3 scripts/case_id_generator.py --type EXP
python3 scripts/case_id_generator.py --type SUP
python3 scripts/case_id_generator.py --type TASK
python3 scripts/case_id_generator.py --type REC
```

Legacy `--workflow GOV` and `--workflow EXPORT` remain supported.

## Sources
- User upgrade brief: `/Users/raghav/.codex/attachments/50962de5-cb39-48a4-8d6e-31bce3df71ac/pasted-text.txt`
