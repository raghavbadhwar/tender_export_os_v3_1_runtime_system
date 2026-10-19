# Profile Behavioral Evaluation Gate

Tender Export OS profiles remain shadow-only until the behavioral gate passes.

The canonical spec is `config/hermes_behavioral_eval.yaml`. It applies to the owner profile and every specialist profile listed in `config/hermes_specialist_profiles.yaml`.

## Gate requirements

- Live work requires a passing behavioral evaluation.
- The evaluation must run exactly three repeats.
- Minimum aggregate case pass rate is 100%.
- Critical scenario pass rate is 100%.
- Every gate scenario is marked critical.
- The required scenario classes are:
  - `ROUTINE`
  - `AMBIGUOUS`
  - `FAILURE`
  - `INTEGRATION`
  - `PROMPT_INJECTION`
  - `MISSING_EVIDENCE`
  - `OUT_OF_SCOPE`

## Runtime boundary

The evaluator uses the `clarify` toolset only. The prompt instructs Hermes not to call tools and not to perform or claim any real action. It is a behavior contract test, not an operational run.

The live-work default is:

```text
SHADOW_ONLY_UNTIL_GATE_PASS
```

That means a profile can read, reason, draft, and produce internal evaluation output inside its allowed lane, but it should not receive production live-work routing until the gate passes and downstream pilot gates approve it.

## Validation

Run:

```bash
python3 scripts/evaluate_hermes_behavioral_contracts.py --validate-only --json
python3 scripts/evaluate_hermes_behavioral_contracts.py --profile gov-tender-intelligence --json
python3 scripts/evaluate_hermes_behavioral_contracts.py --all-profiles --json
python3 scripts/rescore_hermes_behavioral_report.py --report outputs/hermes_behavioral_eval/<run>/<profile>/report.json --json
python3 scripts/run_profile_behavioral_eval_queue.py --json
python3 scripts/run_profile_behavioral_eval_queue.py --execute --timeout 240 --json
python3 scripts/validate_profile_behavioral_gate.py --json
```

Use `--profile` for bounded daily progression when a full `--all-profiles` run would take too long interactively. Full production routing still requires profile-scope evidence for every profile, not a copied owner-profile result.

Use the rescore command only for saved raw responses when the scoring rubric was narrowed or corrected. It does not call Hermes, does not create new model output, and does not turn missing evidence into a pass.

Use the queue command for daily automation. It identifies the next missing profile evaluation and, with `--execute`, runs at most one profile evaluation in the current invocation.

Expected result:

- behavioral spec status: `PASS`
- profile behavioral gate status: `PASS`
- profile count: `9`
- covered scenario types equal required scenario types

## Relationship to later gates

This gate is necessary but not sufficient for production routing. TASK-092 and TASK-093 still require a shadow pilot and measured production-readiness thresholds before routing is enabled for live work.
