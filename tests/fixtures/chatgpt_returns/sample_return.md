return_id: CGPTRET-20990101-SAMPLE
related_case_ids: GOV-20990101-001
sources_used:
- tests/fixtures/chatgpt_returns/sample_return.md
- data/examples/master_cases.example.csv
confidence_level: medium
open_questions:
- Whether the buyer will publish corrigenda.
recommended_next_actions:
- Ask Hermes to create an internal deep-read task.
approval_boundary_statement: This return is advisory only; no send, submit, pay, sign, upload, price commitment, HSN/ITC-HS confirmation, or origin claim may occur without owner approval.

# executive_summary
This is a fixture only. It should never be treated as live research or operational approval.

# cited_findings
- Fixture source: tests/fixtures/chatgpt_returns/sample_return.md.
- Example case data source: data/examples/master_cases.example.csv.

# recommended_strategy
Review quote-proof gaps before pricing and keep all follow-up internal until owner approval is recorded.

# risks_and_assumptions
- Fixture data is not evidence.
- No external sources were checked.

# suggested_hermes_codex_follow_up_tasks
- Run scripts/validate_case_readiness.py --all.

# evidence_gaps
- No live tender documents are present.
- No buyer communication or supplier quote proof is attached.

# do_not_execute_without_approval
- Do not send buyer messages, submit bids, upload documents, use DSC, pay, certify compliance, claim origin, or commit prices without owner approval.
