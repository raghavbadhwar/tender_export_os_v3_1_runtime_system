# Profile Operating Budgets

`config/hermes_specialist_profiles.yaml` now defines an explicit `operating_budget` for every profile.

Each profile declares:

- `max_turns`
- `max_runtime_seconds`
- `max_delegate_count`
- `max_delegate_depth`
- `retry_count`
- `max_artifacts`
- `stop_on_no_progress_turns`

The registry also declares a telemetry contract for Hermes-exposed runtime metadata:

- input tokens
- output tokens
- cost
- latency
- runtime seconds

The telemetry contract is metadata-only. It does not allow raw prompt, raw response, raw document, credential, cookie, session, email-body, or private browser-content capture.

Validate:

```bash
python3 scripts/validate_profile_operating_budgets.py --json
```
