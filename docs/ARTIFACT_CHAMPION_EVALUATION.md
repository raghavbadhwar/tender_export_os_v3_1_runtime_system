# Artifact Champion Evaluation

`scripts/evaluate_artifact_champions.py` compares current artifact quality against champion fixtures.

Current dimensions:

- BOQ extraction
- pricing spreadsheet formulas
- compliance matrix completeness
- approval-card readability

The evaluation checks higher-is-better and lower-is-better metrics per dimension using `config/artifact_evaluation_champions.yaml`.

The current fixture report is written to:

```text
outputs/artifact_evaluations/current_champion_evaluation.json
```

## Boundary

This is an internal quality gate only. Passing it does not approve packs, final prices, compliance, bid submission, export quotation, or any external action.
