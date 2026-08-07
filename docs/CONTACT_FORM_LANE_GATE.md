# Contact-Form Lane Gate

TASK-095's connector design controls are approved, but execution is intentionally disabled.

Approval receipt: `receipts/contact_form_connector_approvals/CFCD-20260713T191305Z.json`

Config: `config/contact_form_lane.yaml`

Validator: `scripts/validate_contact_form_lane.py`

Draft connector design: `config/contact_form_connector_design.yaml`

Design validator: `scripts/validate_contact_form_connector_design.py`

Current status:

```text
APPROVED_DESIGN_EXECUTION_DISABLED
```

## Required before enabling

The connector design is approved at the control-design level. Before any case-specific contact-form execution can be enabled, the lane must still receive:

- domain allowlist;
- exact form-field map;
- screenshot receipt;
- HTML receipt;
- content hash;
- idempotency key;
- anti-CSRF/session handling;
- human CAPTCHA stop;
- post-submit confirmation;
- owner approval receipt.

The reusable design packet intentionally remains `DRAFT_APPROVAL_REQUIRED`; approval is recorded separately in the immutable receipt and projected into the lane config. The approval does not authorize a form submission, browser action, message, quote, bid, upload, payment, DSC use, or external commitment.

## Explicitly forbidden

- unrestricted form automation;
- CAPTCHA bypass;
- credential capture;
- payments or purchases;
- final quote, delivery, classification, origin, legal, or compliance commitments;
- exposing a public service.

## Validation

Run:

```bash
python3 scripts/validate_contact_form_lane.py --json
python3 scripts/validate_contact_form_connector_design.py --json
```

Expected current result:

```text
status: PASS
production_enabled: false
has_approved_design: false
```

This is the correct safe state until the owner approves a separate connector design.
