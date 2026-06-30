# Approval Boundaries

## Hard Approval Required
Owner approval is required before:
- submitting a government bid
- using DSC
- uploading bid or legal documents externally
- paying EMD, security, or advance
- sending supplier email or quote request
- sending buyer email or RFQ reply
- sending final export quote
- sending invoice externally
- committing final price
- committing delivery
- accepting payment terms
- confirming HSN/ITC-HS
- claiming origin or FTA benefit
- ordering from supplier
- blacklisting supplier permanently
- patching pricing or compliance skills
- enabling new network-heavy or credential-heavy plugins
- exposing Hermes/Codex services publicly

## No Approval Needed
Approval is not required for:
- internal scans
- internal records
- internal drafts
- internal source-health updates
- internal plugin-health updates
- internal scorecards
- internal pricing drafts
- internal artifact drafts
- daily briefs
- case reports
- staged memory updates
- staged skill updates

## Approval Card Required Fields
Every approval card must include:
- `case_id`
- workflow type
- proposed action
- business object affected
- amount or price if any
- expected benefit
- concrete risk
- recovery or rollback path
- sources/documents used
- confidence score
- missing information
- Approve / Reject / Ask Changes options

## Receipt Required Fields
Every executed approved action must create a receipt with:
- `receipt_id`
- `case_id`
- action
- actor/runtime
- timestamp
- approval reference
- input summary
- output summary
- evidence/proof
- external effect
- verification status
- next action

## Enforcement
If an action is approval-gated, the runtime must stop at `APPROVAL_REQUIRED`. Silence, intent, old approval, or urgency is not approval.

## Sources
- `config/approval_policy.yaml`
- `AGENTS.md`
- User upgrade brief: `/Users/raghav/.codex/attachments/50962de5-cb39-48a4-8d6e-31bce3df71ac/pasted-text.txt`
