# Learning Proposal Evaluation

`scripts/evaluate_learning_proposal.py` validates a learning proposal before approval or application.

It requires:

- fixed scenario/fixture input;
- exactly three repeated run records;
- passing policy checks;
- evidence completeness of at least 90 percent per repeat;
- candidate latency and cost no more than 2x current baseline;
- rollback artifact path.

With `--write`, it writes the evaluation report and upserts rows into `data/agent_evaluations.csv`.
