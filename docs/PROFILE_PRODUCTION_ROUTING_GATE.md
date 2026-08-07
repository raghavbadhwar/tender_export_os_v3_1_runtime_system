# Profile Production Routing Gate

TASK-093 is implemented as a measured readiness gate, not an automatic promotion.

Config: `config/profile_production_routing_gate.yaml`

Evaluator: `scripts/evaluate_profile_production_routing.py`

Output:

- `outputs/profile_routing_readiness/profile_routing_readiness_*.json`
- `outputs/profile_routing_readiness/profile_routing_readiness_*.html`

## Promotion thresholds

A profile is eligible only if all of these are true:

- the 14-day shadow pilot report status is `PASS`;
- critical/profile behavioral evaluation pass rate is 100%;
- task success rate is at least 90%;
- evidence completeness is at least 95%;
- policy violation count is 0.

If any data is missing, the profile remains `SHADOW`.

The evaluator may also read the specialist canary report:

```text
outputs/profile_specialization/specialist_canaries.json
```

A passing read-only canary proves that a specialist profile can execute one bounded local task without external actions. It can clear the narrow "no profile run evidence at all" concern, but it does not satisfy the broader production task-success, behavioral-eval, shadow-pilot, or owner-review gates.

Profile behavioral evidence is advanced by:

```bash
python3 scripts/run_profile_behavioral_eval_queue.py --json
python3 scripts/run_profile_behavioral_eval_queue.py --execute --timeout 240 --json
```

The queue runner executes at most one missing profile evaluation per invocation so the readiness heartbeat can progress without blocking on a full all-profile run.

## Current safety posture

The evaluator is read-only. It never mutates Kanban routing and never enables production routing.

Even if every metric passes, the result is:

```text
ELIGIBLE_PENDING_OWNER_REVIEW
```

Production routing remains disabled until an owner-reviewed follow-up applies the routing change.

## Current expected result before TASK-092 completes

Until the shadow pilot has a clean 14-day `PASS` report, the readiness report should be:

```text
status: BLOCKED
production_routing_enabled: false
```

That is the correct safe state.
