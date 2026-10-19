# Infrastructure Scale Gates

TASK-100 is implemented by:

```text
config/infrastructure_scale_gates.yaml
```

Validator:

```bash
python3 scripts/validate_infrastructure_scale_gates.py --json
```

Current default:

```text
KEEP_OFF_UNTIL_MEASURED_TRIGGER_AND_OWNER_APPROVAL
```

## Gates defined

- PostgreSQL
- Temporal
- external vector memory
- Langfuse
- paid extraction or cloud browser

Each gate is currently `OFF` and requires measured trigger evidence plus owner approval before activation.

## Activation requirements

- measured trigger evidence path;
- owner approval receipt;
- rollback plan;
- privacy and credential boundary review;
- test plan;
- first-week operating cost cap.

This preserves the current lightweight CSV/event-ledger architecture until measured failure or scale pressure justifies heavier infrastructure.
