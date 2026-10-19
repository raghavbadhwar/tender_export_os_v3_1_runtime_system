# ChatGPT Return Schema

ChatGPT returns are advisory packets only. They cannot mutate registers, send messages, submit bids, approve prices, certify compliance, or override Hermes/Codex approval gates.

Required metadata:

- `return_id`
- `related_case_ids`
- `sources_used`
- `confidence_level`
- `open_questions`
- `recommended_next_actions`
- `approval_boundary_statement`

Required sections:

- `executive_summary`
- `cited_findings`
- `recommended_strategy`
- `risks_and_assumptions`
- `suggested_hermes_codex_follow_up_tasks`
- `evidence_gaps`
- `do_not_execute_without_approval`

Validation rules:

- Markdown and JSON are accepted.
- External factual claims must include cited sources.
- Direct register mutation instructions are rejected.
- External/money/legal/DSC/final-commitment instructions without owner approval are rejected.
- Valid returns are staged as advisory review packets only.
