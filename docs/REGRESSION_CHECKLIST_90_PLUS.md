# 90+ Regression Checklist

Run before claiming 90+:

- `python3 scripts/validate_register_schemas.py`
- `python3 -m compileall scripts`
- `python3 scripts/audit_agent_prompts.py`
- `python3 scripts/test_source_adapters.py --safe --limit 5`
- `python3 scripts/render_mobile_approval_payload.py --all-pending --dry-run`
- `python3 scripts/generate_founder_dashboard.py`
- `python3 scripts/generate_90_plus_scorecard.py`
- `python3 scripts/system_health_check.py --runtime`

Assertions:
- every artifact and run is keyed by `case_id` where applicable
- approval-gated actions stop at approval cards/receipts
- source citations are present
- no external messages/submissions/payments/DSC/final price/classification/origin claims happen without explicit owner approval
