# Model Promotion Gate

`scripts/promote_model_candidate.py` is the promotion gate for forecast models.

It refuses promotion unless all conditions are true:

- candidate row exists in `data/model_registry.csv`;
- candidate is `CANDIDATE` and `CALIBRATED`;
- candidate passes target/workflow maturity gates;
- evaluation report matches the same candidate, target, and workflow;
- Brier score improves versus the current champion when a champion exists;
- coverage meets the configured minimum;
- deterministic and behavioral tests passed;
- rollback version exists;
- a matching `APPROVED` `MODEL` row exists in `data/learning_proposals.csv` with `approval_id` and rollback artifact.

The script only writes when `--write` is supplied. It retires the previous champion for the same target/workflow and marks the candidate as `CHAMPION`.
