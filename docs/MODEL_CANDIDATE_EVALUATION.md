# Model Candidate Evaluation

`scripts/evaluate_model_candidate.py` evaluates a candidate forecast model on mature holdout rows.

It reports:

- Brier score
- log loss
- calibration error
- precision/recall at the operational threshold
- scored-row coverage
- subgroup breakdown by workflow and forecast type
- latency
- comparison with the current champion in `data/model_registry.csv`

The script does not promote, register, deploy, or apply the model. Promotion remains controlled by the later learning proposal and approval gates.

Example:

```bash
python3 scripts/evaluate_model_candidate.py \
  --candidate-model-id CANDIDATE-001 \
  --target-id EXPORT_BUYER_REPLY_21D \
  --workflow-type EXPORT \
  --json
```
