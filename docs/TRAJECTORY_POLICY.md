# Trajectory Policy

`config/trajectory_policy.yaml` defines what Hermes may capture for learning.

Allowed capture is structured metadata only:

- task/case/workflow/profile identifiers;
- tool names;
- decision, policy, approval, proposal, and outcome references;
- evidence receipt paths and hashes;
- evaluator scores;
- latency, token, cost, status, and error metadata.

Excluded capture includes raw prompts, raw documents, raw HTML, email bodies, credentials, cookies, sessions, DSC material, bank/payment data, and private browser content.

RL/fine-tuning is disabled until a labeled dataset and approved training design exist.

Validate:

```bash
python3 scripts/validate_trajectory_policy.py --json
```
