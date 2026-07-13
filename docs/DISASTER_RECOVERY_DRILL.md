# Disaster Recovery Drill

TASK-098 is implemented by:

```bash
python3 scripts/run_disaster_recovery_drill.py --json
```

The drill is non-destructive. It does not restore over live profiles, clear checkpoints, mutate Kanban, or write back rebuilt projections.

## What it verifies

- exports all configured Tender profiles into a drill output folder;
- snapshots `data/events.jsonl`;
- snapshots relevant routing/config files;
- rebuilds CSV projections from events into a temporary drill folder;
- restores one profile into an isolated local folder name;
- checks Hermes checkpoint-store status;
- records measured recovery time and data-loss point.

## Latest measured result

The latest run passed:

- profile exports: 9 profiles;
- projection rebuild: pass;
- checkpoint status: pass;
- isolated restore: `tender-export-os`;
- measured recovery time: 0.983 seconds;
- data-loss point: latest local `data/events.jsonl` copied at drill start.

Report path:

```text
outputs/disaster_recovery_drill/DR-20260712T231832Z/disaster_recovery_drill_report.json
```
