# Apply Learning Proposal

`scripts/apply_learning_proposal.py` applies an approved learning proposal only after strict validation.

Required gates:

- proposal row status is `APPROVED`;
- `approval_id` exists;
- approval scope includes the requested target, version, and artifact hash;
- evaluation report status is `PASS`;
- checkpoint path exists;
- rollback artifact exists.

Only after validation and `--write` does it mark the proposal `APPLIED` and append `learning.promoted` to `data/events.jsonl`.
