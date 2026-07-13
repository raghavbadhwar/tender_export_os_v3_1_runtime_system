# Runtime SLO Checks

TASK-099 is implemented by:

```bash
python3 scripts/check_runtime_slos.py --json
```

Config:

```text
config/runtime_slo.yaml
```

The checker covers:

- gateway health;
- MCP discovery freshness;
- Kanban list/dispatch access;
- scheduler heartbeat;
- source canary freshness;
- projection rebuild freshness;
- behavioral evaluation freshness;
- production-readiness gate freshness;
- disk headroom;
- disaster-recovery drill age.

Failures write local exception cards under:

```text
outputs/runtime_slo/exception_cards/
```

The checker does not mutate Kanban directly:

```text
kanban_mutated: false
```

Latest run status:

```text
PASS
exception_cards: 0
```
