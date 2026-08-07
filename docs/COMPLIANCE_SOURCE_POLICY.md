# Compliance Source Policy

`config/compliance_source_policy.yaml` defines workflow-specific source rules for compliance matrices.

The policy separates GOV and EXPORT requirements and enforces:

- allowed source kind
- primary-source requirement
- source date
- freshness window

`scripts/compliance_source_policy.py` validates the policy and is used by `scripts/compliance_matrix_contract.py`.

## GOV

GOV compliance clauses must cite current primary tender evidence, such as:

- tender document
- corrigendum
- official portal page
- owner-uploaded primary evidence
- supplier certificate when certificate proof is being reviewed
- GST portal where tax/GST verification is being reviewed

## EXPORT

EXPORT compliance clauses must cite current primary sources by requirement type:

- DGFT or official tariff sources for HSN/ITC-HS and export policy
- DGFT/SCOMET list for SCOMET screening
- customs tariff or official destination regulator for tariff/tax
- commodity board, destination regulator, or supplier certificate for certificate requirements
- destination regulator, buyer RFQ, or official trade source for destination rules
- DGFT/customs/destination/chamber sources for origin questions

## Boundary

Passing source freshness means only that the draft cites current primary evidence. It does not finalize compliance, classification, origin, tax treatment, certificates, destination-country requirements, bid readiness, or export quotation readiness.
