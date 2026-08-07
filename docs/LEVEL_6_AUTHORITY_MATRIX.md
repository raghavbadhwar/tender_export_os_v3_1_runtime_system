# Level 6 Authority Matrix

## Purpose

`config/agent_authority_matrix.yaml` is the constitutional cross-check for Tender Export OS. It binds the following existing controls without granting new execution authority:

- `config/tender_tool_policy.yaml` — tool/action risk policy;
- `config/approval_policy.yaml` — owner approval requirements and timeout behavior;
- `config/hermes_specialist_profiles.yaml` — profile and tool boundaries;
- `config/schemas/event.schema.json` and `config/schemas/event_types.yaml` — typed evidence/event records.

The matrix fails closed. An action that is not mapped, a profile that is not registered, a prohibited action mapped to an executable class, or an external action without approval is a validation failure.

## Authority semantics

| Matrix field | Meaning |
|---|---|
| `staging_profiles` | Profiles allowed to prepare or stage an internal request. This is not send/submit authority. |
| `execution_profiles` | Profiles permitted to execute the class after all gates. External classes contain only `owner`. |
| `approval_mode` | `not_required`, `required`, or `prohibited`. |
| `external_effect` | Whether the action can affect an external party, portal, money, legal position, or runtime exposure. |
| `receipt_contract` | Minimum receipt shape expected after the action or decision. |

`external_actions_default: false` is a constitutional invariant. No owner approval is inferred from a draft, a recommendation, a tool result, or the existence of a credential.

## Action lifecycle

```text
signal
  -> evidence receipt
  -> typed internal task/state staging
  -> recommendation or draft
  -> scoped approval card
  -> owner decision
  -> bounded execution (only if approved)
  -> external confirmation / verification
  -> outcome receipt
  -> projection reconciliation
```

Approval cards are requests for decisions, not decisions. Their scope hash, expiry, evidence links, and post-action receipt are mandatory for consequential work.

## Validation

Run from the repository root:

```bash
.venv/bin/python scripts/validate_authority_matrix.py --json \
  --output outputs/system_health/authority_matrix_validation.json
```

The validator is also part of:

- `scripts/system_health_check.py`;
- `scripts/run_full_safe_regression.py`.

A successful validation emits a JSON receipt with `status: PASS` and `external_actions_executed: false`. It performs no external send, upload, submission, payment, portal mutation, or credential operation.

## Change protocol

When adding or changing an action:

1. Update the tool policy first, including tier, effect, approval, and prohibition fields.
2. Add exactly one mapping in `policy_action_classes`.
3. Put consequential actions in `approval_required_actions`; keep them out of autopilot.
4. Add or update the receipt contract and evidence requirements.
5. Run the authority validator and focused tests.
6. Run the safe regression before enabling any new connector or external channel.

Do not use this matrix to bypass existing approval controls. If the matrix and a lower-level policy disagree, the stricter result wins and the validator must fail until the disagreement is resolved.
