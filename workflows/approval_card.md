# Approval Card — Workflow Reference

## What Is an Approval Card?
An approval card is the formal interface between agents (who prepare) and the owner (who decides). No external action occurs until the owner provides an explicit decision on an approval card.

## When Is a Card Created?
Every time an agent reaches a Mode B action (as defined in `config/approval_policy.yaml`), the Approval Desk Agent creates an HTML card and places it in `receipts/approvals/<case_id>_approval_card.html`.

## Required Fields (All Must Be Present)

| Field | Purpose |
|---|---|
| `case_id` | Links to master_cases.csv |
| `workflow_type` | GOV or EXPORT |
| `proposed_action` | Exactly what will happen if approved |
| `business_object` | What external entity is affected |
| `amount_or_price` | ₹ or $ if money involved |
| `expected_benefit` | Why this is a good action |
| `concrete_risk` | Realistic worst case |
| `recovery_rollback_path` | What can be undone |
| `documents_sources_used` | Evidence base |
| `confidence_score` | 0–100 (honest assessment) |
| `missing_information` | Explicit unknowns |
| `approval_options` | Approve / Reject / Ask Changes |

## Owner Response Options

### APPROVE
- Owner confirms all information reviewed
- Action proceeds
- Execution Tracker takes over
- Receipt created

### REJECT
- Case moves to REJECTED status
- No-go note written
- No further agent work on this case

### ASK CHANGES
- Case moves to CHANGES_REQUESTED
- Owner notes are passed back to the relevant agent
- Agent reworks the pack/pricing/compliance
- New approval card created after rework
- Cycle continues until owner approves or rejects

## Hermes Integration
After any owner decision, Hermes records:
- Decision: APPROVED / REJECTED / CHANGES_REQUESTED
- Timestamp
- Owner name
- Receipt ID

Say in Hermes:
- `approve case <case_id>`
- `reject case <case_id>`
- `ask changes <case_id>`
