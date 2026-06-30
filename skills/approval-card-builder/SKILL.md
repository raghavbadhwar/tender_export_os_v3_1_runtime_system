# Approval Card Builder

Use this skill whenever a gated action is proposed.

## Required Fields
- `case_id`
- workflow type
- proposed action
- business object affected
- amount/price if any
- expected benefit
- concrete risk
- recovery/rollback path
- documents/sources used
- confidence score 0-100
- missing information
- approval options: Approve / Reject / Ask Changes

## Procedure
1. Read `config/approval_policy.yaml`.
2. Read the case and relevant artifacts.
3. Build card from `templates/approval_card.html`.
4. Save to `receipts/approvals/<case_id>_approval_card.html`.
5. Add/update pending approval register row.
6. Set case status to `APPROVAL_REQUIRED` only when the card is complete.
7. Append `data/agent_run_log.csv`.

## Must Not
- execute the action
- pre-fill approval decision
- infer approval from silence or old approval
