# Candidate Model Training

`scripts/train_candidate_models.py` is the gated entrypoint for learned forecast models.

It does not promote models, update `data/model_registry.csv`, or replace expert priors. It only prepares an interpretable candidate training plan when all gates pass:

- exact target/workflow has at least 100 mature observations;
- exact target/workflow has at least 20 positive and 20 negative examples;
- examples are already time-separated by the forecast/backtest contract;
- feature snapshots do not contain protected, private, credential, or future/post-outcome fields;
- the split strategy is time-based, not random.

Run:

```bash
python3 scripts/train_candidate_models.py --json
```

With the current live dataset, the expected result is blocked because there are not enough mature target-specific outcomes yet.
