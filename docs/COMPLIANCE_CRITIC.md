# Compliance Critic

`scripts/compliance_critic.py` is an internal independent critic for compliance matrices.

It reviews a matrix and returns:

- whether a critic review is required
- high-risk clauses
- SCOMET/restricted/prohibited signals
- matrix validation gaps
- stale source gaps
- a status of `PASS_NO_CRITIC_REQUIRED`, `REVIEW_REQUIRED`, or `BLOCKED`

## High-Risk Triggers

The critic is required for clauses involving:

- SCOMET
- HSN/ITC-HS
- tariff
- tax
- certificate requirements
- destination requirements
- origin questions
- `UNKNOWN`
- `DOES_NOT_COMPLY`
- `OWNER/EXPERT_REVIEW`

## Boundary

The critic cannot write final compliance state. It cannot approve classification, origin, tax treatment, certificates, destination-country compliance, bid submission, export quotation, or any external action.

When run with `--write`, it writes only an internal critic report and appends a `compliance.critic_reviewed` event.
