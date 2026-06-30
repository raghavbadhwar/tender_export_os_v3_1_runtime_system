# Hermes Skill Write Policy

## Default
Skill writes and patches are approval-gated.

Config source: `config/memory_policy.yaml`

## Stage A Skill Update When
- workflow repeated 3+ times
- owner correction changes future behavior
- source parser fix becomes reusable
- pricing rule improves
- supplier verification rule improves
- compliance check improves
- daily/weekly loop changes

## Extra Approval Required
Pricing and compliance skills require explicit owner approval before patching.

## Procedure
1. Identify repeated pattern or correction.
2. Draft small skill patch.
3. Explain expected effect and risk.
4. Create approval card if pricing/compliance or high-risk runtime is affected.
5. Apply only after approval.
6. Log the change.
