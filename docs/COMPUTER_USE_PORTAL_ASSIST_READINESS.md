# Computer Use Portal-Assist Readiness

TASK-097 is implemented as a readiness gate, not as an enabled portal automation.

Config: `config/computer_use_portal_assist.yaml`

Validator:

```bash
python3 scripts/validate_computer_use_readiness.py --json
```

The validator runs:

- `hermes doctor`
- `hermes computer-use status`
- `hermes computer-use doctor`

It records a local receipt under:

```text
outputs/computer_use_readiness/
```

## Current result

The most recent local readiness report confirms one shareable display plus Screen Recording and Accessibility access. Its success state is:

```text
portal_assist_enabled: false
status: READY_FOR_READ_ONLY_CANARY
```

This is deliberately not an enablement state. It only clears the machine preflight; an explicit owner-approved, manually observable, read-only canary is still required.

After an owner creates an approval record whose action is exactly `computer_use_read_only_canary` for one real case, manually observe a public or owner-opened page with no login, form submission, upload, payment, DSC, CAPTCHA bypass, or commitment. Then record the local evidence:

```bash
python3 scripts/record_computer_use_read_only_canary.py \
  --case-id <CASE_ID> \
  --approval-reference <READ_ONLY_CANARY_APPROVAL_ID> \
  --observed-by owner \
  --observed-at <ISO8601_TIMESTAMP> \
  --evidence <LOCAL_EVIDENCE_FILE> \
  --write --json
```

The recorder checks the case, approval scope, approval status, expiry, evidence hash, and canary safety contract before it writes an append-only event and run-log row. It never controls the browser itself.

## Required before any portal-assist session

- Hermes doctor passes.
- Computer Use status passes.
- Computer Use doctor passes without display/shareability blockers.
- A read-only canary receipt exists.
- Owner provides case-scoped approval.
- Session is manually observable.

## Always forbidden

- bid submission;
- document upload;
- payment;
- DSC or e-signature use;
- CAPTCHA bypass;
- final price, delivery, classification, or origin commitment.
